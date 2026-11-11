import pytest
import os
import json
import tempfile
from pathlib import Path
import fitz
import openpyxl
from fastapi.testclient import TestClient

from app.main import app
from app.database import init_db, get_connection
from app.pipeline.file_validator import (
    validate_document,
    log_document_validation,
    DocumentValidationResult
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_us_llm_008_unsupported_formats():
    """
    US-LLM-008: Identify unsupported file formats and reject them with format issue description.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Test .docx, .png, .txt, .dwg
        unsupported_files = ["blueprint.dwg", "document.docx", "drawing.png", "script.exe", "data.txt"]
        
        for fname in unsupported_files:
            file_path = Path(tmp_dir) / fname
            file_path.write_text("dummy content")
            
            res = validate_document(file_path, fname)
            assert res.is_valid is False
            assert res.status == "unsupported"
            assert res.error_type == "unsupported_format"
            assert "Unsupported file format" in res.error_message
            assert ".pdf" in res.error_message  # Lists accepted formats


def test_us_llm_005_detect_empty_or_missing_files():
    """
    US-LLM-005: Detect files that cannot be opened or processed (empty or missing files).
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Zero-byte PDF
        empty_pdf = Path(tmp_dir) / "empty.pdf"
        empty_pdf.touch()
        res = validate_document(empty_pdf)
        assert res.is_valid is False
        assert res.status == "failed"
        assert res.error_type == "empty_file"
        assert "empty (0 bytes)" in res.error_message

        # 2. Zero-byte Excel
        empty_xlsx = Path(tmp_dir) / "empty.xlsx"
        empty_xlsx.touch()
        res_xl = validate_document(empty_xlsx)
        assert res_xl.is_valid is False
        assert res_xl.status == "failed"
        assert res_xl.error_type == "empty_file"

        # 3. Non-existent file
        missing_file = Path(tmp_dir) / "non_existent.pdf"
        res_missing = validate_document(missing_file)
        assert res_missing.is_valid is False
        assert res_missing.error_type == "not_found"


def test_us_llm_006_corrupted_files():
    """
    US-LLM-006: Identify corrupted files, mark them as failed, and provide appropriate error message.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Corrupted PDF (missing %PDF header)
        bad_header_pdf = Path(tmp_dir) / "bad_header.pdf"
        bad_header_pdf.write_bytes(b"NOT A VALID PDF FILE CONTENT")
        res_pdf1 = validate_document(bad_header_pdf)
        assert res_pdf1.is_valid is False
        assert res_pdf1.status == "failed"
        assert res_pdf1.error_type == "corrupted"
        assert "PDF file header" in res_pdf1.error_message

        # 2. Corrupted PDF (truncated bytes with header but invalid stream/xref)
        corrupt_stream_pdf = Path(tmp_dir) / "corrupt_stream.pdf"
        corrupt_stream_pdf.write_bytes(b"%PDF-1.4\n%garbage binary stream without trailer or catalog\x00\xff\xee")
        res_pdf2 = validate_document(corrupt_stream_pdf)
        assert res_pdf2.is_valid is False
        assert res_pdf2.status == "failed"
        assert res_pdf2.error_type == "corrupted"

        # 3. Corrupted Excel workbook (not a valid zip)
        bad_xlsx = Path(tmp_dir) / "broken.xlsx"
        bad_xlsx.write_bytes(b"PK\x03\x04corrupted fake zip bytes")
        res_xl = validate_document(bad_xlsx)
        assert res_xl.is_valid is False
        assert res_xl.status == "failed"
        assert res_xl.error_type == "corrupted"
        assert "Corrupted Excel workbook" in res_xl.error_message

        # 4. Corrupted JSON file (invalid syntax)
        bad_json = Path(tmp_dir) / "syntax_error.json"
        bad_json.write_text('{"unclosed_key": [1, 2, 3')
        res_json = validate_document(bad_json)
        assert res_json.is_valid is False
        assert res_json.status == "failed"
        assert res_json.error_type == "corrupted"
        assert "Syntax error" in res_json.error_message


def test_us_llm_007_password_protected_pdf():
    """
    US-LLM-007: Identify password-protected documents and do not mark as successfully processed.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        pw_pdf = Path(tmp_dir) / "secure_drawing.pdf"
        
        # Create an encrypted PDF using PyMuPDF
        doc = fitz.open()
        doc.new_page()
        doc.save(
            str(pw_pdf),
            encryption=fitz.PDF_ENCRYPT_AES_256,
            user_pw="engineer123",
            owner_pw="admin123"
        )
        doc.close()

        # Validate
        res = validate_document(pw_pdf)
        assert res.is_valid is False
        assert res.status == "password_protected"
        assert res.error_type == "password_protected"
        assert "password-protected" in res.error_message.lower() or "encrypted" in res.error_message.lower()


def test_valid_files_pass_validation():
    """
    Verify healthy PDF, Excel, and JSON files pass validation cleanly.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Valid PDF
        pdf_path = Path(tmp_dir) / "valid.pdf"
        doc = fitz.open()
        p = doc.new_page()
        p.insert_text((50, 50), "Sample drawing text")
        doc.save(str(pdf_path))
        doc.close()
        res_pdf = validate_document(pdf_path)
        assert res_pdf.is_valid is True
        assert res_pdf.status == "registered"
        assert res_pdf.details["page_count"] == 1

        # 2. Valid Excel
        xlsx_path = Path(tmp_dir) / "valid.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Pier Coordinates"
        ws.append(["Pier", "Easting", "Northing"])
        ws.append(["P1", 385993.744, 1452420.52])
        wb.save(str(xlsx_path))
        wb.close()
        res_xl = validate_document(xlsx_path)
        assert res_xl.is_valid is True
        assert res_xl.status == "registered"
        assert res_xl.details["sheet_count"] == 1

        # 3. Valid JSON
        json_path = Path(tmp_dir) / "valid.json"
        json_path.write_text(json.dumps([{"point_id": "P01", "x": 385993.744, "y": 1452420.52}]))
        res_json = validate_document(json_path)
        assert res_json.is_valid is True
        assert res_json.status == "registered"


def test_validation_logging_deliverable():
    """
    LLM-DOD-02: Verify file validation logs are created in processing_logs table with category='VALIDATION'.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        corrupt_file = Path(tmp_dir) / "damaged_sheet.pdf"
        corrupt_file.write_bytes(b"garbage content")
        
        res = validate_document(corrupt_file, "damaged_sheet.pdf")
        log_document_validation(res, "damaged_sheet.pdf")

        conn = get_connection()
        logs = conn.execute("""
            SELECT * FROM processing_logs 
            WHERE category = 'VALIDATION' AND filename = 'damaged_sheet.pdf'
            ORDER BY id DESC LIMIT 1
        """).fetchone()
        conn.close()

        assert logs is not None
        assert logs["level"] == "ERROR"
        assert "VALIDATION FAILED" in logs["message"]
        assert "damaged_sheet.pdf" in logs["message"]


def test_api_upload_validation_integration():
    """
    Test FastAPI endpoints for upload validation, logs, and summary (LLM-DOD-02).
    """
    # 1. Upload unsupported format (.docx) -> rejected (US-LLM-008)
    res_unsupported = client.post(
        "/api/upload/files",
        files=[("files", ("spec.docx", b"Word document content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))]
    )
    assert res_unsupported.status_code == 200
    data_unsupported = res_unsupported.json()
    assert len(data_unsupported["rejected"]) == 1
    assert data_unsupported["rejected"][0]["error_type"] == "unsupported_format"

    # 2. Upload corrupted PDF -> marked failed with error message (US-LLM-006)
    res_corrupt = client.post(
        "/api/upload/files",
        files=[("files", ("corrupt_blueprint.pdf", b"NOT A VALID PDF CONTENT", "application/pdf"))]
    )
    assert res_corrupt.status_code == 200
    data_corrupt = res_corrupt.json()
    assert len(data_corrupt["failed"]) == 1
    assert data_corrupt["failed"][0]["status"] == "failed"
    assert data_corrupt["failed"][0]["error_type"] == "corrupted"

    # 3. Check /api/upload/validation-logs endpoint (Evidence deliverable)
    res_logs = client.get("/api/upload/validation-logs")
    assert res_logs.status_code == 200
    logs_data = res_logs.json()
    assert "validation_logs" in logs_data
    assert len(logs_data["validation_logs"]) > 0
    categories = [l["category"] for l in logs_data["validation_logs"]]
    assert all(c == "VALIDATION" for c in categories)

    # 4. Check /api/upload/validation-summary endpoint
    res_summary = client.get("/api/upload/validation-summary")
    assert res_summary.status_code == 200
    summary_data = res_summary.json()
    assert "total_documents" in summary_data
    assert "valid_documents" in summary_data
    assert "corrupted_documents" in summary_data

