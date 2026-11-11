import os
import json
import shutil
import hashlib
from typing import List, Optional
from pathlib import Path
import sqlite3

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import INPUT_DIR
from app.database import get_connection, log_event
from app.pipeline.file_validator import validate_document, log_document_validation, DocumentValidationResult
from app.pipeline.document_classifier import classify_engineering_document, store_classification_result
from app.pipeline.sheet_processor import process_document_sheets
from app.pipeline.metadata_extractor import extract_drawing_metadata
from app.pipeline.relationship_manager import build_all_document_relationships

router = APIRouter()

ALLOWED_EXTENSIONS = {
    ".pdf":  "pdf",
    ".xlsx": "excel",
    ".xls":  "excel",
    ".json": "json",
}


def get_file_hash(filepath: str) -> str:
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def _probe_excel_meta(filepath: str) -> dict:
    """Return sheet names and row counts for Excel without full parse."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(str(filepath), read_only=True, data_only=True)
        sheets = []
        for name in wb.sheetnames:
            ws = wb[name]
            sheets.append({"sheet": name, "max_row": ws.max_row, "max_col": ws.max_column})
        wb.close()
        return {"workbook": Path(filepath).name, "sheets": sheets}
    except Exception as e:
        return {"workbook": Path(filepath).name, "sheets": [], "error": str(e)}


def _probe_json_meta(filepath: str) -> dict:
    """Return top-level key count / list length from JSON."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return {"type": "array", "count": len(data)}
        elif isinstance(data, dict):
            return {"type": "object", "keys": list(data.keys())[:20]}
        return {"type": type(data).__name__}
    except Exception as e:
        return {"error": str(e)}


def _register_document(conn: sqlite3.Connection, filename: str, filepath: str,
                        file_type: str, file_hash: str, file_size: int, meta: dict,
                        status: str = 'registered', is_valid: bool = True, error_message: Optional[str] = None):
    meta_str = json.dumps(meta)
    with conn:
        conn.execute("""
            INSERT INTO documents (filename, filepath, file_type, file_hash, file_size_bytes, status, is_valid, error_message, meta_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(filename) DO UPDATE SET
                filepath        = excluded.filepath,
                file_type       = excluded.file_type,
                file_hash       = excluded.file_hash,
                file_size_bytes = excluded.file_size_bytes,
                status          = excluded.status,
                is_valid        = excluded.is_valid,
                error_message   = excluded.error_message,
                meta_json       = excluded.meta_json,
                uploaded_at     = CURRENT_TIMESTAMP
        """, (filename, filepath, file_type, file_hash, file_size, status, int(is_valid), error_message, meta_str))


# ── Legacy compat: also register PDFs in the old `pdfs` table ──────────────
def _register_pdf_legacy(conn: sqlite3.Connection, filename: str, filepath: str, file_hash: str):
    with conn:
        conn.execute("""
            INSERT INTO pdfs (filename, filepath, file_hash)
            VALUES (?, ?, ?)
            ON CONFLICT(filename) DO UPDATE SET
                filepath  = excluded.filepath,
                file_hash = excluded.file_hash
        """, (filename, filepath, file_hash))


# ───────────────────────── Routes ─────────────────────────────────────────

@router.get("/list")
def list_available_files():
    """List all ingested documents (PDF, Excel, JSON) with their metadata and validation status."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, filename, file_type, file_size_bytes, status, is_valid, error_message,
               doc_category, drawing_number, revision, drawing_date, structure_id, meta_json, uploaded_at
        FROM documents ORDER BY uploaded_at DESC
    """).fetchall()
    conn.close()
    files = []
    for r in rows:
        entry = dict(r)
        try:
            entry["meta"] = json.loads(entry.pop("meta_json") or "{}")
        except Exception:
            entry["meta"] = {}
        files.append(entry)
    return {"files": files}


@router.post("/files")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload one or more engineering documents with pre-processing format and integrity validation (LLM-DOD-02).
    - Detects unsupported formats (US-LLM-008)
    - Detects corrupted or unopenable files (US-LLM-005, US-LLM-006)
    - Detects password-protected / encrypted documents (US-LLM-007)
    - Logs all validation events to processing_logs (File validation logs)
    """
    saved = []
    rejected = []
    failed = []
    conn = get_connection()

    for file in files:
        ext = Path(file.filename).suffix.lower()
        file_type = ALLOWED_EXTENSIONS.get(ext)
        if file_type is None:
            err_msg = (
                f"Unsupported file format '{ext}'. Accepted formats are: "
                f"PDF CAD drawings (.pdf), Excel workbooks (.xlsx, .xls), and JSON datasets (.json)."
            )
            log_event("WARNING", "VALIDATION", f"Validation REJECTED for '{file.filename}': {err_msg}", filename=file.filename)
            rejected.append({
                "filename": file.filename,
                "reason": err_msg,
                "error_type": "unsupported_format",
                "status": "unsupported"
            })
            continue

        dest_path = INPUT_DIR / file.filename
        with open(dest_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        file_hash = get_file_hash(str(dest_path))
        file_size = dest_path.stat().st_size

        # Pre-processing Document Integrity & Format Validation (US-LLM-005..007)
        val_res = validate_document(dest_path, file.filename)
        log_document_validation(val_res, file.filename)

        meta: dict = val_res.details.copy()
        meta["validation"] = val_res.to_dict()

        if not val_res.is_valid:
            # File failed validation (corrupted, password-protected, empty, unreadable)
            _register_document(
                conn, file.filename, str(dest_path), file_type, file_hash, file_size,
                meta, status=val_res.status, is_valid=False, error_message=val_res.error_message
            )
            row = conn.execute("SELECT id FROM documents WHERE filename = ?", (file.filename,)).fetchone()
            doc_id = row["id"] if row else None

            failed_item = {
                "document_id":   doc_id,
                "filename":      file.filename,
                "file_type":     file_type,
                "size_bytes":    file_size,
                "status":        val_res.status,
                "error_type":    val_res.error_type,
                "error_message": val_res.error_message,
                "meta":          meta,
            }
            failed.append(failed_item)
            rejected.append({
                "filename":   file.filename,
                "reason":     val_res.error_message,
                "error_type": val_res.error_type,
                "status":     val_res.status
            })
        else:
            # File passed validation (US-LLM-005)
            _register_document(
                conn, file.filename, str(dest_path), file_type, file_hash, file_size,
                meta, status="registered", is_valid=True, error_message=None
            )

            # Keep legacy pdfs table in sync for valid PDFs
            if file_type == "pdf":
                _register_pdf_legacy(conn, file.filename, str(dest_path), file_hash)

            # Governance classification, sheet processing, and metadata extraction (LLM-DOD-03..05)
            c_res = classify_engineering_document(dest_path)
            store_classification_result(c_res)
            if file_type == "pdf":
                process_document_sheets(dest_path)
            extract_drawing_metadata(dest_path)

            row = conn.execute("SELECT id FROM documents WHERE filename = ?", (file.filename,)).fetchone()
            doc_id = row["id"] if row else None

            log_event("INFO", "UPLOAD", f"Uploaded and verified {file_type.upper()} file: {file.filename} [{c_res.doc_category}]", filename=file.filename)

            saved.append({
                "document_id": doc_id,
                "filename":    file.filename,
                "file_type":   file_type,
                "size_bytes":  file_size,
                "status":      "registered",
                "is_valid":    True,
                "doc_category": c_res.doc_category,
                "meta":        meta,
            })

    conn.close()

    if saved:
        build_all_document_relationships()
    return {
        "status":   "success" if saved else ("failed" if failed else "no_valid_files"),
        "uploaded": saved,
        "failed":   failed,
        "rejected": rejected,
        "summary": {
            "total_attempted":   len(saved) + len(rejected),
            "accepted":          len(saved),
            "failed_validation": len(failed),
            "rejected_format":   len(rejected) - len(failed),
        }
    }


@router.post("/load-existing")
def load_existing_files():
    """
    Scan the input directory for all supported file types and validate them before registration (LLM-DOD-02).
    """
    registered = []
    failed = []
    conn = get_connection()

    if INPUT_DIR.exists():
        for f in os.listdir(INPUT_DIR):
            ext = Path(f).suffix.lower()
            file_type = ALLOWED_EXTENSIONS.get(ext)
            if file_type is None:
                continue
            path = INPUT_DIR / f
            file_hash = get_file_hash(str(path))
            file_size = path.stat().st_size

            # Run validation (LLM-DOD-02)
            val_res = validate_document(path, f)
            log_document_validation(val_res, f)

            meta: dict = val_res.details.copy()
            meta["validation"] = val_res.to_dict()

            _register_document(
                conn, f, str(path), file_type, file_hash, file_size,
                meta, status=val_res.status, is_valid=val_res.is_valid,
                error_message=val_res.error_message
            )

            if val_res.is_valid:
                if file_type == "pdf":
                    _register_pdf_legacy(conn, f, str(path), file_hash)
                
                # Execute engineering governance pipeline (LLM-DOD-03 to LLM-DOD-05)
                c_res = classify_engineering_document(path)
                store_classification_result(c_res)
                if file_type == "pdf":
                    process_document_sheets(path)
                extract_drawing_metadata(path)

                registered.append({
                    "filename": f,
                    "file_type": file_type,
                    "status": "registered",
                    "doc_category": c_res.doc_category
                })
            else:
                failed.append({
                    "filename": f,
                    "file_type": file_type,
                    "status": val_res.status,
                    "error_type": val_res.error_type,
                    "error_message": val_res.error_message
                })

    conn.close()

    # Rebuild relationships across all registered documents (LLM-DOD-06)
    if registered:
        build_all_document_relationships()
    return {
        "status": "success",
        "registered": registered,
        "failed": failed,
        "total_valid": len(registered),
        "total_failed": len(failed)
    }


@router.get("/validation-logs")
def get_validation_logs(limit: int = 100):
    """
    Returns file validation logs from processing_logs table (LLM-DOD-02 Evidence).
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, timestamp, level, category, message, filename, page_number
        FROM processing_logs
        WHERE category = 'VALIDATION'
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return {"validation_logs": [dict(r) for r in rows]}


@router.get("/validation-summary")
def get_validation_summary():
    """
    Returns summary metrics of document validity across the system (LLM-DOD-02).
    """
    conn = get_connection()
    docs = conn.execute("SELECT status, is_valid, error_message, file_type FROM documents").fetchall()
    conn.close()

    total = len(docs)
    valid_count = sum(1 for d in docs if d["is_valid"])
    corrupted_count = sum(1 for d in docs if d["status"] in ("failed", "corrupted"))
    password_protected_count = sum(1 for d in docs if d["status"] == "password_protected")

    return {
        "total_documents": total,
        "valid_documents": valid_count,
        "corrupted_documents": corrupted_count,
        "password_protected_documents": password_protected_count,
        "invalid_documents": total - valid_count,
        "all_valid": total > 0 and (total == valid_count),
    }


@router.post("/validate-all")
def validate_all_documents():
    """
    Re-validates all documents currently registered in the database (US-LLM-005).
    """
    conn = get_connection()
    rows = conn.execute("SELECT id, filename, filepath, file_type FROM documents").fetchall()
    results = []

    for r in rows:
        path = Path(r["filepath"])
        val_res = validate_document(path, r["filename"])
        log_document_validation(val_res, r["filename"])

        meta = val_res.details.copy()
        meta["validation"] = val_res.to_dict()

        with conn:
            conn.execute("""
                UPDATE documents
                SET status = ?, is_valid = ?, error_message = ?, meta_json = ?
                WHERE id = ?
            """, (val_res.status, int(val_res.is_valid), val_res.error_message, json.dumps(meta), r["id"]))

        results.append({
            "document_id": r["id"],
            "filename": r["filename"],
            "is_valid": val_res.is_valid,
            "status": val_res.status,
            "error_type": val_res.error_type,
            "error_message": val_res.error_message
        })

    conn.close()
    return {"results": results, "total_checked": len(results)}


@router.post("/validate/{document_id}")
def validate_single_document(document_id: int):
    """
    Validates a specific document by ID (US-LLM-005).
    """
    conn = get_connection()
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")

    path = Path(row["filepath"])
    val_res = validate_document(path, row["filename"])
    log_document_validation(val_res, row["filename"])

    meta = val_res.details.copy()
    meta["validation"] = val_res.to_dict()

    with conn:
        conn.execute("""
            UPDATE documents
            SET status = ?, is_valid = ?, error_message = ?, meta_json = ?
            WHERE id = ?
        """, (val_res.status, int(val_res.is_valid), val_res.error_message, json.dumps(meta), document_id))

    conn.close()
    return {"document_id": document_id, "filename": row["filename"], "validation": val_res.to_dict()}


@router.get("/status/{document_id}")
def get_upload_status(document_id: int):
    """Return upload / ingestion status for a specific document ID (US-LLM-004)."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    entry = dict(row)
    try:
        entry["meta"] = json.loads(entry.pop("meta_json") or "{}")
    except Exception:
        entry["meta"] = {}
    return entry


@router.delete("/files/{document_id}")
def delete_document(document_id: int):
    """Delete an uploaded document from disk and from the database."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    filepath = row["filepath"]
    filename = row["filename"]
    file_type = row["file_type"]

    # Remove from filesystem
    try:
        path = Path(filepath)
        if path.exists():
            path.unlink()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Could not delete file: {e}")

    # Remove from documents table
    with conn:
        conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        # Also remove from legacy pdfs table if PDF
        if file_type == "pdf":
            conn.execute("DELETE FROM pdfs WHERE filename = ?", (filename,))

    conn.close()
    log_event("INFO", "DELETE", f"Deleted {file_type.upper()} document: {filename}", filename=filename)
    return {"status": "deleted", "document_id": document_id, "filename": filename}


@router.get("/preview-data/{document_id}")
def get_preview_data(document_id: int):
    """Return previewable content for Excel and JSON documents."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    file_type = row["file_type"]
    filepath = row["filepath"]

    if file_type == "json":
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {"file_type": "json", "data": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not read JSON: {e}")

    elif file_type == "excel":
        try:
            import openpyxl
            wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
            sheets = {}
            for name in wb.sheetnames:
                ws = wb[name]
                rows = []
                for i, row_cells in enumerate(ws.iter_rows(values_only=True)):
                    if i > 200:   # limit preview rows
                        break
                    rows.append([str(c) if c is not None else "" for c in row_cells])
                sheets[name] = rows
            wb.close()
            return {"file_type": "excel", "sheets": sheets}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not read Excel: {e}")

    elif file_type == "pdf":
        # PDFs are previewed via /input-files/ static mount — just return the URL
        filename = row["filename"]
        from urllib.parse import quote
        url = f"/input-files/{quote(filename)}"
        return {"file_type": "pdf", "preview_url": url}

    raise HTTPException(status_code=400, detail="Unsupported file type for preview")
