import threading
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.pipeline.orchestrator import run_full_extraction_pipeline, get_pipeline_status
from app.database import (
    clear_extracted_data,
    archive_current_run,
    get_run_history,
    restore_run_from_history,
    delete_archived_run
)

router = APIRouter()

@router.get("/status")
def status():
    """Returns the current pipeline processing status and progress percentage."""
    return get_pipeline_status()

@router.post("/run")
def trigger_pipeline(background_tasks: BackgroundTasks):
    """Triggers the full pipeline processing in a background worker thread."""
    current = get_pipeline_status()
    if current["status"] == "running":
        return {"status": "already_running", "message": "Pipeline is already in progress"}
        
    background_tasks.add_task(run_full_extraction_pipeline)
    return {"status": "started", "message": "Extraction pipeline started"}

@router.get("/history")
def list_history():
    """Returns all past archived pipeline runs."""
    return {"history": get_run_history()}

@router.post("/restore/{run_id}")
def restore_run(run_id: str):
    """Restores a previous run snapshot into active catalog tables."""
    ok = restore_run_from_history(run_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Run archive not found")
    return {"status": "success", "message": f"Restored {run_id} into active view"}

@router.delete("/history/{run_id}")
def delete_history_run(run_id: str):
    """Deletes an archived run."""
    delete_archived_run(run_id)
    return {"status": "deleted", "run_id": run_id}

@router.post("/session-reset")
def session_reset():
    """
    Called when a new session begins or website is re-opened:
    Safely archives any active results (so work is never lost) and clears active tables.
    Uploaded documents remain intact.
    """
    archive_current_run("Session Auto-Archive")
    clear_extracted_data()
    return {"status": "success", "message": "Active tables cleared; previous data archived."}

@router.post("/clear-active")
def clear_active_view():
    """Explicitly clears active catalog tables while preserving uploaded documents and run history."""
    clear_extracted_data()
    return {"status": "success", "message": "Active view cleared."}
