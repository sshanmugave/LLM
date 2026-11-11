import math
import re
from typing import List, Tuple, Optional, Dict, Any
from app.database import get_connection, get_crs, log_event
from app.pipeline.crs_handler import convert_projected_to_latlon

def compute_pier_centre(points: List[Tuple[float, float]]) -> Optional[Tuple[float, float]]:
    """
    Computes arithmetic mean of Easting and Northing from a list of (easting, northing) points.
    Returns (centre_easting, centre_northing) rounded to 4 decimal places, or None if points is empty.
    """
    if not points:
        return None
        
    total_e = sum(p[0] for p in points)
    total_n = sum(p[1] for p in points)
    n = len(points)
    
    return round(total_e / n, 4), round(total_n / n, 4)

def calculate_distance(p1: Optional[Tuple[float, float]], p2: Optional[Tuple[float, float]]) -> Optional[float]:
    """
    Straight-line Euclidean distance in metres between two projected coordinates (Easting, Northing).
    Returns None if either point is missing.
    """
    if p1 is None or p2 is None:
        return None
        
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return round(math.sqrt(dx * dx + dy * dy), 3)

def format_point_range(point_ids: List[str]) -> str:
    """
    Formats a list of point IDs into a compact range string.
    Example:
    ['P01', 'P02', 'P03', 'P04'] -> 'P01-P04'
    ['P01', 'P02', 'P05'] -> 'P01-P02, P05'
    ['L01', 'L02', 'L03'] -> 'L01-L03'
    """
    if not point_ids:
        return ""
        
    # Group by prefix and parse numeric values
    parsed = []
    for pid in point_ids:
        m = re.match(r'^([A-Za-z]+)(\d+)$', pid.strip())
        if m:
            prefix = m.group(1).upper()
            num_str = m.group(2)
            num_val = int(num_str)
            width = len(num_str)
            parsed.append((prefix, num_val, width, pid.strip()))
        else:
            parsed.append((pid.strip(), -1, 0, pid.strip()))
            
    # If unparseable mixed strings, just return comma-separated
    if any(p[1] == -1 for p in parsed):
        return ", ".join(sorted(set(point_ids)))
        
    # Sort by prefix, then numeric value
    parsed.sort(key=lambda x: (x[0], x[1]))
    
    # Compress consecutive runs
    runs = []
    current_run = [parsed[0]]
    
    for item in parsed[1:]:
        prev = current_run[-1]
        if item[0] == prev[0] and item[1] == prev[1] + 1:
            current_run.append(item)
        else:
            runs.append(current_run)
            current_run = [item]
    runs.append(current_run)
    
    # Format each run
    formatted_runs = []
    for run in runs:
        if len(run) == 1:
            formatted_runs.append(run[0][3])
        else:
            formatted_runs.append(f"{run[0][3]}-{run[-1][3]}")
            
    return ", ".join(formatted_runs)

def compute_pier_centres_for_pier(carriageway: str, pier_id: str):
    """Computes centre, Lat/Lon, and updates the pier in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT easting, northing, point_id, status 
        FROM corner_points 
        WHERE carriageway = ? AND pier_id = ?
        ORDER BY point_id
    """, (carriageway, pier_id))
    rows = cursor.fetchall()
    
    if not rows:
        conn.close()
        return
        
    coords = [(r["easting"], r["northing"]) for r in rows if r["status"] != "Duplicate"]
    point_ids = [r["point_id"] for r in rows]
    point_range = format_point_range(point_ids)
    
    centre = compute_pier_centre(coords)
    if not centre:
        conn.close()
        return
        
    ce, cn = centre
    crs_info = get_crs()
    epsg = crs_info["epsg_code"]
    lat, lon = convert_projected_to_latlon(ce, cn, epsg)
    status = "Verified" if crs_info["is_verified"] else "CRS Unverified"
    
    with conn:
        conn.execute("""
            UPDATE piers
            SET point_range = ?, centre_easting = ?, centre_northing = ?, latitude = ?, longitude = ?, status = ?
            WHERE carriageway = ? AND pier_id = ?
        """, (point_range, ce, cn, lat, lon, status, carriageway, pier_id))
        
    conn.close()

def compute_skew_angle(p1: Optional[Tuple[float, float]], p2: Optional[Tuple[float, float]]) -> Optional[float]:
    """
    Computes the azimuth orientation (heading in degrees from North, 0-360) 
    between two consecutive pier centres.
    Transverse pier cap orientation is perpendicular (+90 deg).
    """
    if p1 is None or p2 is None:
        return None
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    rad = math.atan2(dx, dy)
    deg = (math.degrees(rad) + 360) % 360
    # Pier cap is perpendicular to bridge centerline
    cap_angle = (deg + 90.0) % 360
    return round(cap_angle, 2)

def compute_footing_envelope(pts: List[Tuple[float, float]]) -> Tuple[Optional[float], Optional[float]]:
    """Calculates the bounding envelope (Length x Width) of footing corner points."""
    if not pts:
        return None, None
    min_x = min(p[0] for p in pts)
    max_x = max(p[0] for p in pts)
    min_y = min(p[1] for p in pts)
    max_y = max(p[1] for p in pts)
    dx = round(max_x - min_x, 3)
    dy = round(max_y - min_y, 3)
    length = max(dx, dy)
    width = min(dx, dy)
    return length, width

def recompute_coordinates_for_all_piers():
    """Recalculates all pier centres, lat/lon using active CRS, inter-pier distances, skew angles, and 3D dimensions."""
    conn = get_connection()
    cursor = conn.cursor()
    crs_info = get_crs()
    epsg = crs_info["epsg_code"]
    is_crs_verified = crs_info["is_verified"]
    
    cursor.execute("SELECT DISTINCT carriageway FROM piers ORDER BY carriageway")
    carriageways = [r[0] for r in cursor.fetchall()]
    
    for cw in carriageways:
        is_loop = "loop" in cw.lower()
        # Default structural dimensions from Section 1-1 / Section 2-2
        cap_w = 10500.0 if is_loop else 13600.0
        cap_cd = 2200.0 if is_loop else 2500.0
        cap_td = 1400.0 if is_loop else 1500.0
        cap_cant = 2500.0 if is_loop else 3000.0
        shaft_w = 4000.0 if is_loop else 5000.0
        shaft_thk = 2000.0 if is_loop else 2500.0
        ped_h = 800.0 if is_loop else 900.0
        brg_off = 650.0 if is_loop else 750.0
        typical_span = 20000.0 if is_loop else 30000.0
        
        cursor.execute("""
            SELECT id, pier_id, sequence_order, status, notes
            FROM piers
            WHERE carriageway = ?
            ORDER BY sequence_order, id
        """, (cw,))
        piers = [dict(r) for r in cursor.fetchall()]
        
        prev_centre = None
        for idx, pier in enumerate(piers):
            pid = pier["pier_id"]
            cursor.execute("""
                SELECT easting, northing, point_id, status 
                FROM corner_points 
                WHERE carriageway = ? AND pier_id = ?
                ORDER BY point_id
            """, (cw, pid))
            pt_rows = cursor.fetchall()
            
            if pt_rows:
                valid_pts = [(r["easting"], r["northing"]) for r in pt_rows if r["status"] != "Duplicate"]
                pt_ids = [r["point_id"] for r in pt_rows]
                pt_range = format_point_range(pt_ids)
                
                centre = compute_pier_centre(valid_pts)
                if centre:
                    ce, cn = centre
                    lat, lon = convert_projected_to_latlon(ce, cn, epsg)
                    
                    dist = calculate_distance(prev_centre, centre) if prev_centre else None
                    skew = compute_skew_angle(prev_centre, centre) if prev_centre else None
                    flen, fwid = compute_footing_envelope(valid_pts)
                    prev_centre = centre
                    
                    pier_status = pier["status"]
                    if not is_crs_verified and pier_status == "Verified":
                        pier_status = "CRS Unverified"
                    elif is_crs_verified and pier_status == "CRS Unverified":
                        pier_status = "Verified"
                        
                    with conn:
                        conn.execute("""
                            UPDATE piers 
                            SET point_range = ?,
                                centre_easting = ?,
                                centre_northing = ?,
                                latitude = ?,
                                longitude = ?,
                                distance_from_previous = ?,
                                skew_angle_deg = ?,
                                footing_length = ?,
                                footing_width = ?,
                                span_length = ?,
                                pier_cap_width = ?,
                                pier_cap_center_depth = ?,
                                pier_cap_tip_depth = ?,
                                pier_cap_cantilever = ?,
                                pier_shaft_width = ?,
                                pier_shaft_thickness = ?,
                                pedestal_height = ?,
                                bearing_offset = ?,
                                status = ?
                            WHERE id = ?
                        """, (
                            pt_range, ce, cn, lat, lon, dist, skew, flen, fwid,
                            typical_span, cap_w, cap_cd, cap_td, cap_cant,
                            shaft_w, shaft_thk, ped_h, brg_off, pier_status,
                            pier["id"]
                        ))
            else:
                prev_centre = None
                
    conn.close()
    log_event("INFO", "COMPUTE", f"Recomputed coordinates, 3D dimensions, and skew angles using EPSG:{epsg}.")
