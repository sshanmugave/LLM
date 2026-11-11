import pytest
from pathlib import Path
from app.config import INPUT_DIR
from app.database import init_db
from app.pipeline.metadata_extractor import (
    extract_drawing_metadata, generate_metadata_comparison_report
)

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_us_llm_017_drawing_number_and_title_extracted():
    """US-LLM-017: Available drawing numbers and titles are extracted and linked to the source."""
    gad_path = INPUT_DIR / "GAD 1 (1) 1.pdf"
    if not gad_path.exists():
        gad_path = INPUT_DIR.parent / "GAD 1 (1) 1.pdf"

    meta = extract_drawing_metadata(gad_path)
    assert meta.drawing_number is not None, "Drawing number must be extracted"
    assert "O24087" in meta.drawing_number
    assert meta.drawing_title is not None
    assert "GENERAL ARRANGEMENT" in meta.drawing_title.upper()
    assert meta.source_reference is not None

def test_us_llm_018_revisions_captured_without_silent_inference(tmp_path):
    """US-LLM-018: Available revision identifiers are captured without being silently inferred when absent."""
    # 1. Real file with revision
    gad_path = INPUT_DIR / "GAD 1 (1) 1.pdf"
    if not gad_path.exists():
        gad_path = INPUT_DIR.parent / "GAD 1 (1) 1.pdf"

    meta = extract_drawing_metadata(gad_path)
    assert meta.revision is not None
    assert meta.revision in ["RC", "REV.C", "R0", "C"]
    assert meta.is_revision_explicit is True

    # 2. Synthetic drawing with NO revision tag: must NOT infer "R0" or "0"
    no_rev_file = tmp_path / "sketch_without_revision.pdf"
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "PROJECT SKETCH\nNO REVISION BLOCK INCLUDED\nDATE: 01/01/2026")
    doc.save(str(no_rev_file))
    doc.close()

    meta_no_rev = extract_drawing_metadata(no_rev_file)
    assert meta_no_rev.revision is None, "Revision must be None when absent, NOT silently inferred!"
    assert meta_no_rev.is_revision_explicit is False

def test_us_llm_019_drawing_dates_captured_with_source():
    """US-LLM-019: Available drawing dates are captured with their source references."""
    mcw_path = INPUT_DIR / "MCW P&P 1.pdf"
    if not mcw_path.exists():
        mcw_path = INPUT_DIR.parent / "MCW P&P 1.pdf"

    meta = extract_drawing_metadata(mcw_path)
    assert meta.revision_date is not None
    assert "2025" in meta.revision_date or "2026" in meta.revision_date or "SEP" in meta.revision_date.upper()
    assert "MCW P&P 1.pdf" in meta.source_reference

def test_us_llm_020_distinguish_different_revisions(tmp_path):
    """US-LLM-020: Documents with different revisions are distinguishable."""
    import fitz
    # Version A
    f_v0 = tmp_path / "DRG_001_Rev0.pdf"
    doc0 = fitz.open()
    p0 = doc0.new_page()
    p0.insert_text((72, 72), "DRAWING NO: BR-101\nTITLE: ABUTMENT DETAIL\nREV: R0\nDATE: 01/01/2025")
    doc0.save(str(f_v0))
    doc0.close()

    # Version B (revised)
    f_v1 = tmp_path / "DRG_001_Rev1.pdf"
    doc1 = fitz.open()
    p1 = doc1.new_page()
    p1.insert_text((72, 72), "DRAWING NO: BR-101\nTITLE: ABUTMENT DETAIL\nREV: R1\nDATE: 15/06/2025")
    doc1.save(str(f_v1))
    doc1.close()

    m0 = extract_drawing_metadata(f_v0)
    m1 = extract_drawing_metadata(f_v1)

    assert m0.drawing_number == m1.drawing_number
    assert m0.revision != m1.revision
    assert m0.revision == "R0"
    assert m1.revision == "R1"

    report = generate_metadata_comparison_report()
    comp = next((c for c in report["version_comparisons"] if c["drawing_number"] == "BR-101"), None)
    assert comp is not None
    assert comp["is_distinguishable"] is True

def test_drawing_metadata_comparison_deliverable():
    """Verifies that generate_metadata_comparison_report returns the official LLM-DOD-05 deliverable."""
    report = generate_metadata_comparison_report()

    assert report["deliverable"] == "Drawing metadata comparison"
    assert "drawings" in report
    assert "version_comparisons" in report
    assert "evaluations" in report
    assert len(report["evaluations"]) == 4
    assert report["summary"]["all_passed"] is True
