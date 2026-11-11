import pytest
from pathlib import Path
from app.config import INPUT_DIR
from app.database import init_db
from app.pipeline.document_classifier import (
    classify_engineering_document, store_classification_result,
    generate_classification_test_report, CATEGORY_GAD, CATEGORY_MCW_PLAN_PROFILE,
    CATEGORY_FOUNDATION_LAYOUT, CATEGORY_STRUCTURAL_DRAWING, CATEGORY_CROSS_SECTION,
    CATEGORY_UNCERTAIN
)

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_us_llm_009_gad_classification():
    """US-LLM-009: Classifies supported GAD documents correctly against the approved test set."""
    gad_path = INPUT_DIR / "GAD 1 (1) 1.pdf"
    if not gad_path.exists():
        gad_path = INPUT_DIR.parent / "GAD 1 (1) 1.pdf"
    assert gad_path.exists(), "Test file GAD 1 (1) 1.pdf must exist"

    result = classify_engineering_document(gad_path)
    store_classification_result(result)

    assert result.doc_category == CATEGORY_GAD, f"Expected {CATEGORY_GAD}, got {result.doc_category}"
    assert result.confidence >= 0.80, f"Confidence should be >= 0.80, got {result.confidence}"
    assert result.is_uncertain is False
    assert any("GENERAL ARRANGEMENT" in ev.upper() or "GAD" in ev.upper() for ev in result.evidence)

def test_us_llm_010_mcw_plan_profile_classification():
    """US-LLM-010: Identifies document as MCW Plan & Profile when supported by its content."""
    mcw_path = INPUT_DIR / "MCW P&P 1.pdf"
    if not mcw_path.exists():
        mcw_path = INPUT_DIR.parent / "MCW P&P 1.pdf"
    assert mcw_path.exists(), "Test file MCW P&P 1.pdf must exist"

    result = classify_engineering_document(mcw_path)
    store_classification_result(result)

    assert result.doc_category == CATEGORY_MCW_PLAN_PROFILE, f"Expected {CATEGORY_MCW_PLAN_PROFILE}, got {result.doc_category}"
    assert result.confidence >= 0.80
    assert result.is_uncertain is False
    assert any("PLAN" in ev.upper() and "PROFILE" in ev.upper() for ev in result.evidence)

def test_us_llm_011_foundation_and_structural_distinction():
    """US-LLM-011: Assigns correct document category according to approved classification rules."""
    foundation_path = INPUT_DIR / "GAD 1 (2) 1.pdf"
    if not foundation_path.exists():
        foundation_path = INPUT_DIR.parent / "GAD 1 (2) 1.pdf"
    assert foundation_path.exists(), "Test file GAD 1 (2) 1.pdf must exist"

    result = classify_engineering_document(foundation_path)
    store_classification_result(result)

    assert result.doc_category == CATEGORY_FOUNDATION_LAYOUT, f"Expected {CATEGORY_FOUNDATION_LAYOUT}, got {result.doc_category}"
    assert result.is_uncertain is False
    assert any("FOUNDATION" in ev.upper() or "COORDINATES" in ev.upper() for ev in result.evidence)

def test_us_llm_012_cross_section_and_uncertain_flagging(tmp_path):
    """US-LLM-012: Identifies appropriate category or flags an uncertain classification."""
    # 1. Test ambiguous/empty file is flagged uncertain
    dummy_file = tmp_path / "ambiguous_memo.pdf"
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Meeting Minutes: Project discussion on road alignment without engineering data.")
    doc.save(str(dummy_file))
    doc.close()

    res_uncertain = classify_engineering_document(dummy_file)
    assert res_uncertain.is_uncertain is True, "Ambiguous document must be flagged as uncertain"
    assert res_uncertain.doc_category == CATEGORY_UNCERTAIN
    assert res_uncertain.confidence < 0.60

    # 2. Test cross-section content
    cs_file = tmp_path / "deck_cross_section.pdf"
    doc2 = fitz.open()
    page2 = doc2.new_page()
    page2.insert_text((72, 72), "TYPICAL CROSS SECTION 1-1 OF MAIN CARRIAGEWAY DECK\nROADWAY WIDTH: 14000mm, CAMBER: 2.5%, CRASH BARRIER: 525mm")
    doc2.save(str(cs_file))
    doc2.close()

    res_cs = classify_engineering_document(cs_file)
    assert res_cs.doc_category == CATEGORY_CROSS_SECTION
    assert res_cs.confidence >= 0.70

def test_classification_test_report_deliverable():
    """Verifies that generate_classification_test_report returns the official LLM-DOD-03 deliverable."""
    report = generate_classification_test_report()

    assert report["deliverable"] == "Classification test report"
    assert "evaluations" in report
    assert report["summary"]["total_tests"] >= 4
    assert report["summary"]["all_passed"] is True

