import os
from pathlib import Path
from typing import Dict, Any, List
from app.config import INPUT_DIR
from app.database import init_db, get_connection, log_event, archive_current_run
from app.pipeline.ingest import ingest_pdf_file
from app.pipeline.extract_tables import extract_tables_from_pdf
from app.pipeline.extract_text import extract_project_notes_and_scps
from app.pipeline.merge import merge_and_store_pipeline_data

from app.pipeline.extract_cad_sections import extract_cad_sections_and_boreholes
from app.pipeline.ai_engine import run_ai_insight_generation
from app.pipeline.compute import recompute_coordinates_for_all_piers
from app.pipeline.file_validator import validate_document, log_document_validation

# Global in-memory progress tracker
pipeline_progress = {
    "status": "idle",
    "current_stage": "idle",
    "progress_percent": 0,
    "message": "Ready to process",
    "total_files": 0,
    "processed_files": 0,
    "results_summary": {}
}

def run_full_extraction_pipeline() -> Dict[str, Any]:
    """
    Executes the complete 3D-ready extraction pipeline strictly for GAD 1 (1) and GAD 1 (2).
    """
    global pipeline_progress
    init_db()
    
    pipeline_progress["status"] = "running"
    pipeline_progress["current_stage"] = "Scanning Input Directory"
    pipeline_progress["progress_percent"] = 5
    pipeline_progress["message"] = "Scanning files..."
    
    # Strictly select GAD 1 (1) and GAD 1 (2), ignoring MCW P&P 1
    all_files = [INPUT_DIR / f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    if not all_files:
        parent_dir = INPUT_DIR.parent
        all_files = [parent_dir / f for f in os.listdir(parent_dir) if f.lower().endswith(".pdf")]
        
    pdf_files = [f for f in all_files if "gad" in f.name.lower()]
    if not pdf_files:
        pdf_files = all_files  # fallback if naming differs
        
    # Pre-processing file integrity and security validation (US-LLM-005..007)
    valid_pdf_files = []
    for f in pdf_files:
        val_res = validate_document(f)
        log_document_validation(val_res, f.name)
        if not val_res.is_valid:
            log_event("WARNING", "PIPELINE", f"Skipping invalid/corrupted/password-protected file '{f.name}' ({val_res.error_message})", filename=f.name)
        else:
            valid_pdf_files.append(f)

    if not valid_pdf_files:
        pipeline_progress["status"] = "error"
        pipeline_progress["message"] = "No valid, accessible GAD drawings found to process."
        return {"error": "No valid PDFs found"}

    pdf_files = valid_pdf_files
    pipeline_progress["total_files"] = len(pdf_files)
    pipeline_progress["processed_files"] = 0

    log_event("INFO", "PIPELINE", f"Starting 3D extraction pipeline on {len(pdf_files)} verified drawing files.")
    
    # 1. Ingestion & Page Rendering
    pipeline_progress["current_stage"] = "Ingestion & Image Rendering"
    pipeline_progress["progress_percent"] = 15
    pipeline_progress["message"] = "Ingesting drawings and rendering page views..."
    
    for idx, pdf_path in enumerate(pdf_files):
        ingest_pdf_file(pdf_path)
        pipeline_progress["processed_files"] = idx + 1
        pipeline_progress["progress_percent"] = 15 + int(15 * (idx + 1) / len(pdf_files))

    # 2. Table & Text Extraction
    pipeline_progress["current_stage"] = "Table & Drawing Extraction"
    pipeline_progress["progress_percent"] = 35
    pipeline_progress["message"] = "Extracting coordinate schedules and annotations..."
    
    all_raw_points = []
    excluded_piers = []
    
    for pdf_path in pdf_files:
        pts = extract_tables_from_pdf(pdf_path)
        all_raw_points.extend(pts)
        
        notes_data = extract_project_notes_and_scps(pdf_path)
        excluded_piers.extend(notes_data.get("excluded_piers", []))

    # 3. Cross-Page & Cross-PDF Merging & Validation
    pipeline_progress["current_stage"] = "Merging & Footing Coordinate Assembly"
    pipeline_progress["progress_percent"] = 55
    pipeline_progress["message"] = "Merging points across pages and detecting conflicts..."
    
    merge_results = merge_and_store_pipeline_data(all_raw_points, excluded_piers=list(set(excluded_piers)))

    # 4. CAD Cross-Section & Geotechnical Extraction from GAD 1 (1)
    pipeline_progress["current_stage"] = "Structural Section & Geotechnical Extraction"
    pipeline_progress["progress_percent"] = 70
    pipeline_progress["message"] = "Extracting Section 1-1, Section 2-2, and Borehole logs BH20-BH30..."
    
    for pdf_path in pdf_files:
        if "gad 1 (1)" in pdf_path.name.lower() or "gad_1_1" in pdf_path.name.lower():
            extract_cad_sections_and_boreholes(pdf_path)

    # 5. Compute 3D Geometry, Footing Bounding Boxes & Skew Angles
    pipeline_progress["current_stage"] = "3D Geometric Modeling & Alignment"
    pipeline_progress["progress_percent"] = 85
    pipeline_progress["message"] = "Computing 3D insertion coordinates, footing polygons, and skew angles..."
    
    recompute_coordinates_for_all_piers()

    # 6. AI Drawing Insights & Executive Brief Generation
    pipeline_progress["current_stage"] = "AI Executive Synthesis"
    pipeline_progress["progress_percent"] = 92
    pipeline_progress["message"] = "Generating 3D conversion brief and engineering insights..."
    
    ai_insights = run_ai_insight_generation(merge_results)

    # Automatically archive this run into run_history
    archived_id = archive_current_run(f"Pipeline Run ({merge_results.get('total_piers', 0)} Piers, {merge_results.get('total_points', 0)} Points)")

    pipeline_progress["current_stage"] = "Complete"
    pipeline_progress["progress_percent"] = 100
    pipeline_progress["status"] = "completed"
    pipeline_progress["archived_run_id"] = archived_id
    pipeline_progress["message"] = f"Extraction complete: {merge_results['total_piers']} piers, {merge_results['total_points']} corner points, 3D dimensions, and AI brief ready."
    pipeline_progress["results_summary"] = merge_results
    
    log_event("INFO", "PIPELINE", f"3D Extraction pipeline finished: {merge_results['total_piers']} piers across sections.")
    return merge_results

def get_pipeline_status() -> Dict[str, Any]:
    global pipeline_progress
    return pipeline_progress
