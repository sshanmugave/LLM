import pytest
from pathlib import Path
from app.config import INPUT_DIR
from app.database import init_db
from app.pipeline.sheet_processor import (
    process_document_sheets, generate_page_processing_report,
    STATUS_SUCCESS, STATUS_FAILED, STATUS_NEEDS_REVIEW
)

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_us_llm_013_all_pages_processed_status_recorded():
    """US-LLM-013: System records the processing status of each page and identifies failed pages."""
    gad_path = INPUT_DIR / "GAD 1 (1) 1.pdf"
    if not gad_path.exists():
        gad_path = INPUT_DIR.parent / "GAD 1 (1) 1.pdf"
    assert gad_path.exists()

    pages = process_document_sheets(gad_path)
    assert len(pages) == 10, f"GAD 1 (1) has 10 pages, got {len(pages)}"

    for p in pages:
        assert "page_number" in p
        assert "status" in p
        assert p["status"] in [STATUS_SUCCESS, STATUS_NEEDS_REVIEW]

def test_us_llm_014_engineering_tables_identified():
    """US-LLM-014: Supported tables are identified and made available for extraction stage."""
    foundation_path = INPUT_DIR / "GAD 1 (2) 1.pdf"
    if not foundation_path.exists():
        foundation_path = INPUT_DIR.parent / "GAD 1 (2) 1.pdf"
    assert foundation_path.exists()

    pages = process_document_sheets(foundation_path)
    report = generate_page_processing_report()

    # Verify tables registered in registry
    assert report["summary"]["total_tables_registered"] > 0
    tb_types = [t["table_type"] for t in report["tables"]]
    assert "COORDINATE_SCHEDULE" in tb_types or any("COORDINATE" in t for t in tb_types)

def test_us_llm_015_multiple_drawing_sheets_tracked():
    """US-LLM-015: Each applicable sheet is tracked and processed or explicitly marked as requiring review."""
    gad_path = INPUT_DIR / "GAD 1 (1) 1.pdf"
    if not gad_path.exists():
        gad_path = INPUT_DIR.parent / "GAD 1 (1) 1.pdf"

    pages = process_document_sheets(gad_path)
    for p in pages:
        assert p["sheet_number"] is not None
        assert p["sheet_title"] is not None
        assert "Sheet" in p["sheet_number"]

def test_us_llm_016_failed_and_skipped_reporting(tmp_path):
    """US-LLM-016: The system reports failed, skipped, and successfully processed pages or sheets."""
    # Create an invalid file to test failure reporting
    corrupt_path = tmp_path / "corrupt_damaged.pdf"
    corrupt_path.write_bytes(b"%PDF-damaged-stream-without-pages")

    res = process_document_sheets(corrupt_path)
    assert len(res) == 1
    assert res[0]["status"] == STATUS_FAILED
    assert res[0]["error_message"] is not None

    report = generate_page_processing_report()
    assert report["summary"]["failed"] >= 1

def test_page_level_processing_report_deliverable():
    """Verifies that generate_page_processing_report returns the official LLM-DOD-04 deliverable."""
    report = generate_page_processing_report()

    assert report["deliverable"] == "Page-level processing report"
    assert "pages" in report
    assert "tables" in report
    assert "evaluations" in report
    assert len(report["evaluations"]) == 4
    assert any(e["test_id"] == "TC-LLM-013" for e in report["evaluations"])

