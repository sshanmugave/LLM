import math
from typing import List, Dict, Any, Tuple
from app.database import get_connection, get_crs, log_event
from app.pipeline.normalise import extract_pier_sequence_order
from app.pipeline.compute import compute_pier_centre, calculate_distance, format_point_range
from app.pipeline.crs_handler import convert_projected_to_latlon
from app.pipeline.validate import validate_coordinates, validate_pier_point_cluster, check_coordinate_conflict

def merge_and_store_pipeline_data(
    all_raw_points: List[Dict[str, Any]], 
    excluded_piers: List[str] = None
) -> Dict[str, Any]:
    """
    Performs cross-page and cross-PDF merging:
    - Groups raw points by (carriageway, point_id)
    - Detects duplicates and flags conflicts
    - Stores corner points in database
    - Groups into piers, computes centres, lat/long, and inter-pier distances
    - Stores piers in database
    """
    conn = get_connection()
    cursor = conn.cursor()
    crs_info = get_crs()
    epsg = crs_info["epsg_code"]
    is_crs_verified = crs_info["is_verified"]
    
    # Clear previous extracted points and piers
    with conn:
        conn.execute("DELETE FROM corner_points")
        conn.execute("DELETE FROM piers")
        conn.execute("DELETE FROM conflicts")
        
    # Group raw points by (carriageway, point_id)
    grouped_points: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for pt in all_raw_points:
        key = (pt["carriageway"], pt["point_id"])
        grouped_points.setdefault(key, []).append(pt)
        
    final_corner_points = []
    conflict_count = 0
    duplicate_count = 0
    
    for (cw, pt_id), pt_list in grouped_points.items():
        if len(pt_list) == 1:
            final_corner_points.append(pt_list[0])
        else:
            # Check for conflict between first instance and subsequent instances
            base = pt_list[0]
            first_coords = (base["easting"], base["northing"])
            has_conflict = False
            
            for other in pt_list[1:]:
                other_coords = (other["easting"], other["northing"])
                is_conf, diff = check_coordinate_conflict(first_coords, other_coords, tolerance_m=0.05)
                
                if is_conf:
                    has_conflict = True
                    conflict_count += 1
                    cursor.execute("""
                        INSERT INTO conflicts (
                            point_id, pier_id, carriageway,
                            first_easting, first_northing, first_source,
                            second_easting, second_northing, second_source,
                            difference_m, resolution_notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        pt_id, base["pier_id"], cw,
                        base["easting"], base["northing"], f"{base['source_pdf']} (pg {base['source_page']})",
                        other["easting"], other["northing"], f"{other['source_pdf']} (pg {other['source_page']})",
                        diff, f"Difference of {diff:.3f}m between sources"
                    ))
                    log_event("WARN", "CONFLICT", f"Point {pt_id} coordinate conflict: {diff:.3f}m between {base['source_pdf']} and {other['source_pdf']}", filename=base['source_pdf'], page_number=base['source_page'], conn=conn)
                else:
                    duplicate_count += 1
                    
            if has_conflict:
                base["status"] = "Review Required"
                base["notes"] = f"Coordinate conflict detected across sources (difference > 0.05m)"
            else:
                base["notes"] = f"Verified across {len(pt_list)} occurrences"
                
            final_corner_points.append(base)
            
    # Insert corner points into database
    for pt in final_corner_points:
        cursor.execute("""
            INSERT INTO corner_points (
                point_id, pier_id, carriageway, easting, northing,
                source_pdf, source_page, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pt["point_id"], pt["pier_id"], pt["carriageway"],
            pt["easting"], pt["northing"], pt["source_pdf"],
            pt["source_page"], pt["status"], pt.get("notes")
        ))
    conn.commit()
    
    # Group points by (carriageway, pier_id) to compute piers
    piers_by_section: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for pt in final_corner_points:
        cw = pt["carriageway"]
        pid = pt["pier_id"]
        if pid:
            piers_by_section.setdefault(cw, {}).setdefault(pid, []).append(pt)
            
    total_piers_created = 0
    
    for cw, pier_map in piers_by_section.items():
        # Sort piers by logical sequence order
        sorted_pier_ids = sorted(pier_map.keys(), key=lambda p: extract_pier_sequence_order(p))
        
        prev_centre = None
        for pid in sorted_pier_ids:
            pts = pier_map[pid]
            pt_coords = [(p["easting"], p["northing"]) for p in pts if p["status"] != "Duplicate"]
            pt_ids = [p["point_id"] for p in pts]
            pt_range = format_point_range(pt_ids)
            
            # Check cluster spread
            is_cluster_valid, cluster_err = validate_pier_point_cluster(pt_coords)
            
            centre = compute_pier_centre(pt_coords)
            if centre:
                ce, cn = centre
                lat, lon = convert_projected_to_latlon(ce, cn, epsg)
                dist = calculate_distance(prev_centre, centre) if prev_centre else None
                prev_centre = centre
            else:
                ce, cn, lat, lon, dist = None, None, None, None, None
                
            # Collect unique sources
            src_pdfs = ", ".join(sorted(set(p["source_pdf"] for p in pts)))
            src_pages = ", ".join(sorted(set(str(p["source_page"]) for p in pts)))
            
            # Determine pier status
            status = "Verified"
            pier_notes = []
            
            if not is_crs_verified:
                status = "CRS Unverified"
                pier_notes.append("CRS unverified (assumed UTM 44N)")
                
            if not is_cluster_valid:
                status = "Review Required"
                pier_notes.append(cluster_err)
                
            if any(p["status"] == "Review Required" for p in pts):
                status = "Review Required"
                pier_notes.append("One or more corner points flagged for review")
                
            pier_notes.append("Dimensions blank: Section 1-1 to 5-5 drawings not found in PDFs")
            
            seq_order = extract_pier_sequence_order(pid)
            
            cursor.execute("""
                INSERT INTO piers (
                    carriageway, pier_id, point_range, latitude, longitude,
                    distance_from_previous, pier_height, pier_width,
                    pier_cap_height, pier_cap_width, dimension_units,
                    centre_easting, centre_northing, source_pdfs, source_pages,
                    status, notes, sequence_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cw, pid, pt_range, lat, lon,
                dist, None, None,
                None, None, "mm",
                ce, cn, src_pdfs, src_pages,
                status, "; ".join(pier_notes), seq_order
            ))
            total_piers_created += 1
            
    conn.commit()
    conn.close()
    
    log_event("INFO", "MERGE", f"Completed merge: {len(final_corner_points)} points, {total_piers_created} piers, {conflict_count} conflicts.")
    return {
        "total_points": len(final_corner_points),
        "total_piers": total_piers_created,
        "conflict_count": conflict_count,
        "duplicate_count": duplicate_count
    }
