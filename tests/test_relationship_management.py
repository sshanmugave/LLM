import pytest
from pathlib import Path
from app.config import INPUT_DIR
from app.database import init_db
from app.pipeline.relationship_manager import (
    build_all_document_relationships, trace_element_provenance,
    generate_relationship_records_report, RELATIONSHIP_DRAWING_REFERENCE,
    RELATIONSHIP_STRUCTURE_GROUP, RELATIONSHIP_ELEMENT_LINK
)
from app.pipeline.metadata_extractor import extract_drawing_metadata

@pytest.fixture(autouse=True)
def setup_relationships():
    init_db()
    # Extract metadata for test files
    for f in [INPUT_DIR / "GAD 1 (1) 1.pdf", INPUT_DIR / "GAD 1 (2) 1.pdf", INPUT_DIR / "MCW P&P 1.pdf"]:
        if f.exists():
            extract_drawing_metadata(f)
    build_all_document_relationships()

def test_us_llm_021_drawing_references_associated():
    """US-LLM-021: Relationships recorded when supported by explicit references or approved rules."""
    report = generate_relationship_records_report()
    drg_refs = [r for r in report["records"] if r["relationship_type"] == RELATIONSHIP_DRAWING_REFERENCE]

    assert len(drg_refs) > 0, "Explicit drawing references must be discovered"
    assert any("O24087-C-RP-MB-GA-8330" in r["reference_text"] for r in drg_refs)
    assert any("GAD 1 (2)" in r["source_doc"] or "GAD 1 (1)" in r["source_doc"] for r in drg_refs)

def test_us_llm_022_structure_id_associations():
    """US-LLM-022: Structure associations match the available source identifiers."""
    report = generate_relationship_records_report()
    struct_groups = [r for r in report["records"] if r["relationship_type"] == RELATIONSHIP_STRUCTURE_GROUP]

    assert len(struct_groups) > 0, "Documents sharing a structure ID must be grouped"
    assert any("FLYOVER-INTERCHANGE-CH54+281" in r["structure_id"] for r in struct_groups)

def test_us_llm_023_common_element_linking_and_ambiguity_flagging():
    """US-LLM-023: Common element IDs link related records, and ambiguous matches are flagged."""
    report = generate_relationship_records_report()
    elem_links = [r for r in report["records"] if r["relationship_type"] == RELATIONSHIP_ELEMENT_LINK]
    ambiguous = [r for r in elem_links if r["is_ambiguous"]]

    assert len(elem_links) > 0, "Element links must connect shared entities"
    # P3 and P11 are excluded piers in drawing notes -> must be flagged as ambiguous
    assert len(ambiguous) > 0, "Excluded or ambiguous piers must be flagged"
    assert any(r["element_id"] in ["P3", "P11", "P03"] for r in ambiguous)

def test_us_llm_024_provenance_tracing():
    """US-LLM-024: Each recorded relationship provides references to associated documents or records."""
    trace = trace_element_provenance("P4")

    assert trace["is_found"] is True
    assert trace["element_id"] == "P4"
    assert trace["total_source_references"] >= 1
    assert any("GAD" in s["source_document"] for s in trace["sources"])
    assert trace["trace_verified"] is True

def test_document_relationship_records_deliverable():
    """Verifies that generate_relationship_records_report returns official LLM-DOD-06 deliverable."""
    report = generate_relationship_records_report()

    assert report["deliverable"] == "Document relationship records"
    assert "records" in report
    assert "evaluations" in report
    assert len(report["evaluations"]) == 4
    assert report["summary"]["all_passed"] is True

