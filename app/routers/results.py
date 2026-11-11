from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from app.database import get_connection, log_event
from app.models import PointUpdateRequest, PierUpdateRequest, AIQueryRequest
from app.pipeline.ai_engine import answer_drawing_query

router = APIRouter()

@router.get("/stats")
def get_summary_stats():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Pier counts by carriageway
    cursor.execute("""
        SELECT carriageway, 
               COUNT(*) as total_piers,
               SUM(CASE WHEN status = 'Verified' THEN 1 ELSE 0 END) as verified_piers,
               SUM(CASE WHEN status = 'Review Required' THEN 1 ELSE 0 END) as review_piers,
               SUM(CASE WHEN status = 'CRS Unverified' THEN 1 ELSE 0 END) as crs_unverified_piers
        FROM piers
        GROUP BY carriageway
    """)
    section_stats = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT COUNT(*) FROM corner_points")
    total_points = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM piers")
    total_piers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM corner_points WHERE status = 'Review Required'")
    points_needing_review = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM conflicts WHERE resolved = 0")
    unresolved_conflicts = cursor.fetchone()[0]

    conn.close()
    return {
        "total_piers": total_piers,
        "total_points": total_points,
        "points_needing_review": points_needing_review,
        "unresolved_conflicts": unresolved_conflicts,
        "sections": section_stats
    }

@router.get("/piers")
def get_piers(
    carriageway: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM piers WHERE 1=1"
    params = []

    if carriageway and carriageway != "All":
        query += " AND carriageway = ?"
        params.append(carriageway)
    
    if status and status != "All":
        query += " AND status = ?"
        params.append(status)

    if search:
        query += " AND (pier_id LIKE ? OR point_range LIKE ? OR notes LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    query += " ORDER BY carriageway, sequence_order, id"
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"piers": rows}

@router.get("/piers/{carriageway}/{pier_id}")
def get_pier_detail(carriageway: str, pier_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM piers WHERE carriageway = ? AND pier_id = ?", (carriageway, pier_id))
    pier = cursor.fetchone()
    if not pier:
        conn.close()
        raise HTTPException(status_code=404, detail="Pier not found")
        
    pier_dict = dict(pier)
    
    # Associated points
    cursor.execute("SELECT * FROM corner_points WHERE carriageway = ? AND pier_id = ? ORDER BY point_id", (carriageway, pier_id))
    points = [dict(r) for r in cursor.fetchall()]
    pier_dict["points"] = points
    
    # Associated page images
    cursor.execute("""
        SELECT DISTINCT p.image_path, p.page_number, pdf.filename 
        FROM pages p
        JOIN pdfs pdf ON p.pdf_id = pdf.id
        WHERE p.raw_text LIKE ?
    """, (f"%{pier_id}%",))
    images = [dict(r) for r in cursor.fetchall()]
    pier_dict["source_images"] = images
    
    conn.close()
    return pier_dict

@router.get("/corner_points")
def get_corner_points(
    carriageway: Optional[str] = None,
    pier_id: Optional[str] = None,
    status: Optional[str] = None
):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM corner_points WHERE 1=1"
    params = []
    
    if carriageway and carriageway != "All":
        query += " AND carriageway = ?"
        params.append(carriageway)
        
    if pier_id:
        query += " AND pier_id = ?"
        params.append(pier_id)
        
    if status and status != "All":
        query += " AND status = ?"
        params.append(status)
        
    query += " ORDER BY id"
    cursor.execute(query, params)
    points = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"corner_points": points}

@router.get("/conflicts")
def get_conflicts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conflicts ORDER BY id DESC")
    conflicts = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"conflicts": conflicts}

@router.get("/logs")
def get_logs(limit: int = 100):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM processing_logs ORDER BY id DESC LIMIT ?", (limit,))
    logs = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"logs": logs}

@router.post("/point/update")
def update_point(payload: PointUpdateRequest):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM corner_points WHERE point_id = ?", (payload.point_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Corner point not found")
        
    updates = []
    params = []
    if payload.easting is not None:
        updates.append("easting = ?")
        params.append(payload.easting)
    if payload.northing is not None:
        updates.append("northing = ?")
        params.append(payload.northing)
    if payload.pier_id is not None:
        updates.append("pier_id = ?")
        params.append(payload.pier_id)
    if payload.status is not None:
        updates.append("status = ?")
        params.append(payload.status)
    if payload.notes is not None:
        updates.append("notes = ?")
        params.append(payload.notes)
        
    if updates:
        params.append(payload.point_id)
        with conn:
            conn.execute(f"UPDATE corner_points SET {', '.join(updates)} WHERE point_id = ?", params)
            
    conn.close()
    
    # Recalculate centre coordinates for the pier
    try:
        from app.pipeline.compute import compute_pier_centres_for_pier
        pier_id = payload.pier_id or existing["pier_id"]
        carriageway = payload.carriageway or existing["carriageway"]
        compute_pier_centres_for_pier(carriageway, pier_id)
    except Exception as e:
        log_event("WARN", "UPDATE", f"Recalculation error: {str(e)}")
        
    return {"status": "success", "message": f"Updated point {payload.point_id}"}

@router.post("/pier/update")
def update_pier(payload: PierUpdateRequest):
    conn = get_connection()
    updates = []
    params = []
    
    if payload.pier_height is not None:
        updates.append("pier_height = ?")
        params.append(payload.pier_height)
    if payload.pier_width is not None:
        updates.append("pier_width = ?")
        params.append(payload.pier_width)
    if payload.pier_cap_height is not None:
        updates.append("pier_cap_height = ?")
        params.append(payload.pier_cap_height)
    if payload.pier_cap_width is not None:
        updates.append("pier_cap_width = ?")
        params.append(payload.pier_cap_width)
    if payload.status is not None:
        updates.append("status = ?")
        params.append(payload.status)
    if payload.notes is not None:
        updates.append("notes = ?")
        params.append(payload.notes)
        
    if updates:
        params.extend([payload.carriageway, payload.pier_id])
        with conn:
            conn.execute(f"UPDATE piers SET {', '.join(updates)} WHERE carriageway = ? AND pier_id = ?", params)
    
    conn.close()
    return {"status": "success", "message": f"Updated pier {payload.pier_id}"}

@router.get("/deck-sections")
def get_deck_sections():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deck_sections ORDER BY id")
    sections = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"sections": sections}

@router.get("/boreholes")
def get_borehole_logs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM borehole_logs ORDER BY borehole_id, depth_from")
    logs = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"boreholes": logs}

@router.get("/insights")
def get_executive_insights():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM executive_insights ORDER BY id")
    insights = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"insights": insights}

@router.post("/ai/ask")
def ask_ai_drawing_question(payload: AIQueryRequest):
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty")
    result = answer_drawing_query(payload.query.strip())
    return result
