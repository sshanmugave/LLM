import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.config import INPUT_DIR
from app.pipeline.document_classifier import (
    classify_engineering_document, store_classification_result, generate_classification_test_report
)
from app.pipeline.sheet_processor import (
    process_document_sheets, generate_page_processing_report
)
from app.pipeline.metadata_extractor import (
    extract_drawing_metadata, generate_metadata_comparison_report
)
from app.pipeline.relationship_manager import (
    build_all_document_relationships, trace_element_provenance, generate_relationship_records_report
)
from app.database import get_connection

router = APIRouter()

@router.get("/classification-report", summary="LLM-DOD-03: Classification Test Report")
def get_classification_report():
    """
    Returns the official Classification Test Report for LLM-DOD-03
    (US-LLM-009, US-LLM-010, US-LLM-011, US-LLM-012).
    """
    report = generate_classification_test_report()
    return JSONResponse(content=report)

@router.get("/page-processing-report", summary="LLM-DOD-04: Page-Level Processing Report")
def get_page_processing_report():
    """
    Returns the official Page-Level Processing Report for LLM-DOD-04
    (US-LLM-013, US-LLM-014, US-LLM-015, US-LLM-016).
    """
    report = generate_page_processing_report()
    return JSONResponse(content=report)

@router.get("/metadata-comparison", summary="LLM-DOD-05: Drawing Metadata Comparison Report")
def get_metadata_comparison():
    """
    Returns the official Drawing Metadata Comparison Report for LLM-DOD-05
    (US-LLM-017, US-LLM-018, US-LLM-019, US-LLM-020).
    """
    report = generate_metadata_comparison_report()
    return JSONResponse(content=report)

@router.get("/relationship-records", summary="LLM-DOD-06: Document Relationship Records Report")
def get_relationship_records():
    """
    Returns the official Document Relationship Records for LLM-DOD-06
    (US-LLM-021, US-LLM-022, US-LLM-023, US-LLM-024).
    """
    report = generate_relationship_records_report()
    return JSONResponse(content=report)

@router.get("/trace/{element_id}", summary="US-LLM-024: Trace Element Provenance")
def trace_element(element_id: str):
    """
    Traces an engineering element (e.g. Pier P4, Point 15, Borehole BH-20)
    back to its origin drawing files, sheet numbers, and cross-references.
    """
    trace_data = trace_element_provenance(element_id)
    return JSONResponse(content=trace_data)

@router.post("/run-all", summary="Execute Full Governance Pipeline")
def run_governance_all():
    """
    Scans all registered input documents and executes:
    1. Document Classification (LLM-DOD-03)
    2. Multi-Page & Sheet Processing (LLM-DOD-04)
    3. Metadata & Revision Extraction (LLM-DOD-05)
    4. Document Relationship Mapping (LLM-DOD-06)
    """
    target_files = []
    if INPUT_DIR.exists():
        target_files = [INPUT_DIR / f for f in os.listdir(INPUT_DIR) if f.lower().endswith(('.pdf', '.xlsx', '.xls', '.json'))]

    results = {
        "classified_count": 0,
        "processed_pages_count": 0,
        "metadata_count": 0,
        "relationships_count": 0,
        "processed_files": []
    }

    for fpath in target_files:
        # 1. Classify
        c_res = classify_engineering_document(fpath)
        store_classification_result(c_res)
        results["classified_count"] += 1

        # 2. Process sheets (for PDFs)
        if fpath.suffix.lower() == ".pdf":
            p_res = process_document_sheets(fpath)
            results["processed_pages_count"] += len(p_res)

        # 3. Extract metadata
        m_res = extract_drawing_metadata(fpath)
        results["metadata_count"] += 1

        results["processed_files"].append({
            "filename": fpath.name,
            "category": c_res.doc_category,
            "drawing_number": m_res.drawing_number,
            "revision": m_res.revision
        })

    # 4. Build relationships
    rels = build_all_document_relationships()
    results["relationships_count"] = len(rels)

    return JSONResponse(content={
        "status": "success",
        "message": f"Successfully processed {len(target_files)} engineering documents through all governance stages (LLM-DOD-03 to LLM-DOD-06).",
        "results": results
    })
