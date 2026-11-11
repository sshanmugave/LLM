"""
Document Integrity and Format Validation Module (LLM-DOD-02)

Covers:
- US-LLM-005: Validate uploaded files before processing to identify unopenable/unreadable files.
- US-LLM-006: Identify corrupted files with descriptive error messages.
- US-LLM-007: Identify password-protected/encrypted files and prevent successful processing.
- US-LLM-008: Identify and reject unsupported file formats.
- Deliverable: Comprehensive file validation logs in processing_logs table.
"""

import os
import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import fitz  # PyMuPDF
import openpyxl

from app.database import log_event

SUPPORTED_EXTENSIONS = {
    ".pdf":  "pdf",
    ".xlsx": "excel",
    ".xls":  "excel",
    ".json": "json"
}


@dataclass
class DocumentValidationResult:
    is_valid: bool
    status: str                        # 'registered', 'failed', 'corrupted', 'password_protected', 'unsupported'
    error_type: Optional[str] = None   # None, 'unsupported_format', 'empty_file', 'corrupted', 'password_protected', 'unreadable'
    error_message: Optional[str] = None
    file_type: str = "unknown"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "status": self.status,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "file_type": self.file_type,
            "details": self.details,
        }


def validate_document(filepath: Path, filename: Optional[str] = None) -> DocumentValidationResult:
    """
    Validates a document file for integrity, supported format, corruption, and password protection.
    """
    path = Path(filepath)
    fname = filename or path.name
    ext = path.suffix.lower()

    # 1. Format check (US-LLM-008)
    file_type = SUPPORTED_EXTENSIONS.get(ext)
    if not file_type:
        err_msg = (
            f"Unsupported file format '{ext}'. Accepted formats are: "
            f"PDF CAD drawings (.pdf), Excel workbooks (.xlsx, .xls), and JSON datasets (.json)."
        )
        return DocumentValidationResult(
            is_valid=False,
            status="unsupported",
            error_type="unsupported_format",
            error_message=err_msg,
            file_type="unsupported",
            details={"extension": ext}
        )

    # 2. File existence and size check (US-LLM-005)
    if not path.exists():
        return DocumentValidationResult(
            is_valid=False,
            status="failed",
            error_type="not_found",
            error_message=f"File '{fname}' does not exist on disk.",
            file_type=file_type
        )

    file_size = path.stat().st_size
    if file_size == 0:
        return DocumentValidationResult(
            is_valid=False,
            status="failed",
            error_type="empty_file",
            error_message=f"File '{fname}' is empty (0 bytes) and cannot be opened or processed.",
            file_type=file_type,
            details={"file_size_bytes": 0}
        )

    # 3. Format-specific integrity and security validation
    if file_type == "pdf":
        return _validate_pdf(path, fname, file_size)
    elif file_type == "excel":
        return _validate_excel(path, fname, file_size)
    elif file_type == "json":
        return _validate_json(path, fname, file_size)

    return DocumentValidationResult(
        is_valid=False,
        status="failed",
        error_type="unsupported_format",
        error_message=f"Validation handler not found for '{ext}'.",
        file_type="unknown"
    )


def _validate_pdf(path: Path, filename: str, file_size: int) -> DocumentValidationResult:
    """Validates PDF files for header integrity, password protection (US-LLM-007), and corruption (US-LLM-006)."""
    # Header check
    try:
        with open(path, "rb") as f:
            header = f.read(1024)
            if b"%PDF" not in header:
                return DocumentValidationResult(
                    is_valid=False,
                    status="failed",
                    error_type="corrupted",
                    error_message=f"Corrupted file '{filename}': Missing standard PDF file header (%PDF).",
                    file_type="pdf",
                    details={"file_size_bytes": file_size}
                )
    except Exception as e:
        return DocumentValidationResult(
            is_valid=False,
            status="failed",
            error_type="corrupted",
            error_message=f"Unable to read file '{filename}': {str(e)}",
            file_type="pdf"
        )

    # PyMuPDF opening and security inspection
    doc = None
    try:
        doc = fitz.open(str(path))

        # Check password protection / encryption (US-LLM-007)
        if doc.is_encrypted or doc.needs_pass:
            return DocumentValidationResult(
                is_valid=False,
                status="password_protected",
                error_type="password_protected",
                error_message=f"Document '{filename}' is password-protected or encrypted. Please provide an unlocked document.",
                file_type="pdf",
                details={"is_encrypted": True, "needs_password": bool(doc.needs_pass), "page_count": len(doc)}
            )

        page_count = len(doc)
        if page_count == 0:
            return DocumentValidationResult(
                is_valid=False,
                status="failed",
                error_type="unreadable",
                error_message=f"Corrupted PDF '{filename}': Document contains 0 pages.",
                file_type="pdf",
                details={"page_count": 0}
            )

        # Probe first page geometry and rendering to verify stream integrity
        first_page = doc[0]
        _ = first_page.rect
        _ = first_page.get_text()

    except fitz.FileDataError as e:
        err_str = str(e).lower()
        if "password" in err_str or "encrypt" in err_str:
            return DocumentValidationResult(
                is_valid=False,
                status="password_protected",
                error_type="password_protected",
                error_message=f"Document '{filename}' is password-protected or encrypted: {str(e)}",
                file_type="pdf"
            )
        return DocumentValidationResult(
            is_valid=False,
            status="failed",
            error_type="corrupted",
            error_message=f"Corrupted PDF file '{filename}': {str(e)}",
            file_type="pdf",
            details={"file_size_bytes": file_size}
        )
    except Exception as e:
        err_str = str(e).lower()
        if "password" in err_str or "encrypt" in err_str:
            return DocumentValidationResult(
                is_valid=False,
                status="password_protected",
                error_type="password_protected",
                error_message=f"Document '{filename}' is password-protected: {str(e)}",
                file_type="pdf"
            )
        return DocumentValidationResult(
            is_valid=False,
            status="failed",
            error_type="corrupted",
            error_message=f"Corrupted PDF file '{filename}': Unable to parse page streams ({str(e)}).",
            file_type="pdf"
        )
    finally:
        if doc is not None:
            doc.close()

    return DocumentValidationResult(
        is_valid=True,
        status="registered",
        file_type="pdf",
        details={
            "page_count": page_count,
            "file_size_bytes": file_size,
            "is_encrypted": False
        }
    )


def _validate_excel(path: Path, filename: str, file_size: int) -> DocumentValidationResult:
    """Validates Excel workbooks (.xlsx, .xls) for encryption (US-LLM-007) and archive corruption (US-LLM-006)."""
    # Check for OLE encrypted package header (common for password-protected .xlsx)
    try:
        with open(path, "rb") as f:
            start_bytes = f.read(8)
            # OLE Compound file signature: \xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1
            if start_bytes == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" and path.suffix.lower() == ".xlsx":
                # Check if it contains EncryptedPackage
                f.seek(0)
                content = f.read(4096)
                if b"EncryptedPackage" in content:
                    return DocumentValidationResult(
                        is_valid=False,
                        status="password_protected",
                        error_type="password_protected",
                        error_message=f"Excel workbook '{filename}' is password-protected or encrypted. Please provide an unlocked workbook.",
                        file_type="excel",
                        details={"encrypted_package": True}
                    )
    except Exception:
        pass

    wb = None
    try:
        wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
        sheet_names = list(wb.sheetnames)
        if not sheet_names:
            return DocumentValidationResult(
                is_valid=False,
                status="failed",
                error_type="unreadable",
                error_message=f"Excel workbook '{filename}' contains no worksheets.",
                file_type="excel"
            )

        # Inspect first sheet to verify row structure
        ws = wb[sheet_names[0]]
        sheets_meta = [{"sheet": name, "max_row": ws.max_row, "max_col": ws.max_column} for name in sheet_names[:10]]

    except zipfile.BadZipFile as e:
        return DocumentValidationResult(
            is_valid=False,
            status="failed",
            error_type="corrupted",
            error_message=f"Corrupted Excel workbook '{filename}': Invalid or damaged zip archive ({str(e)}).",
            file_type="excel",
            details={"file_size_bytes": file_size}
        )
    except Exception as e:
        err_str = str(e).lower()
        if "password" in err_str or "encrypted" in err_str:
            return DocumentValidationResult(
                is_valid=False,
                status="password_protected",
                error_type="password_protected",
                error_message=f"Excel workbook '{filename}' is password-protected: {str(e)}",
                file_type="excel"
            )
        return DocumentValidationResult(
            is_valid=False,
            status="failed",
            error_type="corrupted",
            error_message=f"Corrupted Excel workbook '{filename}': Unable to open workbook ({str(e)}).",
            file_type="excel",
            details={"file_size_bytes": file_size}
        )
    finally:
        if wb is not None:
            wb.close()

    return DocumentValidationResult(
        is_valid=True,
        status="registered",
        file_type="excel",
        details={
            "sheet_count": len(sheet_names),
            "sheets": sheets_meta,
            "file_size_bytes": file_size
        }
    )


def _validate_json(path: Path, filename: str, file_size: int) -> DocumentValidationResult:
    """Validates JSON datasets for UTF-8 decoding and valid syntax (US-LLM-006)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, (list, dict)):
            return DocumentValidationResult(
                is_valid=False,
                status="failed",
                error_type="unreadable",
                error_message=f"JSON file '{filename}' does not contain an object or array at root level.",
                file_type="json"
            )

        count = len(data) if isinstance(data, list) else len(data.keys())
        return DocumentValidationResult(
            is_valid=True,
            status="registered",
            file_type="json",
            details={
                "type": "array" if isinstance(data, list) else "object",
                "element_count": count,
                "file_size_bytes": file_size
            }
        )

    except UnicodeDecodeError as e:
        return DocumentValidationResult(
            is_valid=False,
            status="failed",
            error_type="corrupted",
            error_message=f"Corrupted JSON file '{filename}': Invalid UTF-8 encoding or binary characters detected ({str(e)}).",
            file_type="json"
        )
    except json.JSONDecodeError as e:
        return DocumentValidationResult(
            is_valid=False,
            status="failed",
            error_type="corrupted",
            error_message=f"Corrupted JSON file '{filename}': Syntax error on line {e.lineno}, column {e.colno} ({e.msg}).",
            file_type="json"
        )
    except Exception as e:
        return DocumentValidationResult(
            is_valid=False,
            status="failed",
            error_type="corrupted",
            error_message=f"Corrupted JSON file '{filename}': {str(e)}",
            file_type="json"
        )


def log_document_validation(result: DocumentValidationResult, filename: str):
    """
    Persists file validation results to processing_logs (File validation logs deliverable).
    """
    if result.is_valid:
        msg = f"VALIDATION PASSED: '{filename}' ({result.file_type.upper()}) is valid and verified for processing."
        log_event("INFO", "VALIDATION", msg, filename=filename)
    elif result.error_type == "password_protected":
        msg = f"VALIDATION BLOCKED: '{filename}' is password-protected / encrypted. Access restriction identified."
        log_event("ERROR", "VALIDATION", msg, filename=filename)
    elif result.error_type == "corrupted":
        msg = f"VALIDATION FAILED: '{filename}' is corrupted: {result.error_message}"
        log_event("ERROR", "VALIDATION", msg, filename=filename)
    elif result.error_type == "unsupported_format":
        msg = f"VALIDATION REJECTED: '{filename}' has an unsupported format: {result.error_message}"
        log_event("WARNING", "VALIDATION", msg, filename=filename)
    else:
        msg = f"VALIDATION FAILED: '{filename}': {result.error_message}"
        log_event("ERROR", "VALIDATION", msg, filename=filename)

