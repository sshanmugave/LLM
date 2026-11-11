from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import get_crs, update_crs, log_event

router = APIRouter()

class CRSUpdatePayload(BaseModel):
    epsg_code: int
    name: Optional[str] = None
    is_verified: bool = True

@router.get("/")
def get_current_crs():
    return get_crs()

@router.post("/update")
def update_current_crs(payload: CRSUpdatePayload):
    try:
        from pyproj import CRS
        proj_crs = CRS.from_epsg(payload.epsg_code)
        name = payload.name or proj_crs.name
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid EPSG code {payload.epsg_code}: {str(e)}")

    update_crs(payload.epsg_code, name, is_verified=payload.is_verified, detection_source="User Specified")
    log_event("INFO", "CRS", f"CRS updated to EPSG:{payload.epsg_code} ({name}) by user.")
    
    # Trigger recalculation of pier coordinates with new CRS
    try:
        from app.pipeline.compute import recompute_coordinates_for_all_piers
        recompute_coordinates_for_all_piers()
    except Exception as e:
        log_event("WARN", "CRS", f"Recomputing piers after CRS change failed: {str(e)}")

    return {"status": "success", "crs": get_crs()}
