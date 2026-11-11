import re
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import pdfplumber

from app.pipeline.normalise import normalise_pier_id, normalise_point_id, normalise_carriageway
from app.pipeline.validate import validate_coordinates
from app.database import log_event

def parse_table_column_words(page, bbox: Tuple[float, float, float, float], carriageway: str, source_pdf: str, page_num: int) -> List[Dict[str, Any]]:
    """
    Parses a 4-column coordinate table column:
    [PIER | POINTS | EASTING (X) | NORTHING (Y)]
    within bounding box bbox = (x0, top, x1, bottom).
    Uses horizontal grid lines in the pier column to group points to piers accurately.
    """
    cropped = page.crop(bbox)
    words = cropped.extract_words()
    if not words:
        return []
        
    # Horizontal grid lines within this column
    h_lines = [
        l for l in page.lines 
        if l['x0'] <= bbox[0] + 35 
        and l['x1'] >= bbox[2] - 35 
        and bbox[1] - 5 <= l['top'] <= bbox[3] + 5
    ]
    h_lines.sort(key=lambda l: l['top'])
    unique_line_tops = []
    for l in h_lines:
        t = l['top']
        if not unique_line_tops or abs(t - unique_line_tops[-1]) > 3:
            unique_line_tops.append(t)

    col_width = bbox[2] - bbox[0]
    # Pier column is the leftmost ~38 points from bbox[0]
    pier_x_max = bbox[0] + 40.0
    
    # Extract pier words located strictly in the pier column
    pier_words = []
    for w in words:
        if w['x0'] <= pier_x_max:
            text = w['text'].strip().upper()
            if re.match(r'^(?:A\d+|P\d+|[1-4][AP]\d+|[1-4]P\d+)$', text):
                pier_words.append(w)
                
    # Group words by vertical row (line)
    lines_by_y = {}
    for w in words:
        if w['top'] > bbox[1] + 20: # skip table header row
            y_cluster = round(w['top'] / 3.5) * 3.5
            lines_by_y.setdefault(y_cluster, []).append(w)
            
    rows = []
    
    for y in sorted(lines_by_y.keys()):
        lw = sorted(lines_by_y[y], key=lambda w: w['x0'])
        line_text = " ".join(w['text'] for w in lw)
        
        # Match point ID (Pxx or Lxx)
        pt_match = re.search(r'\b([PL]\d+)\b', line_text, re.I)
        # Match Easting & Northing numbers
        coords = re.findall(r'\b(38\d{4}(?:\.\d+)?|145\d{4}(?:\.\d+)?)\b', line_text)
        
        if pt_match and len(coords) >= 2:
            raw_pt = pt_match.group(1).upper()
            pt_id = normalise_point_id(raw_pt)
            
            c1 = float(coords[0])
            c2 = float(coords[1])
            easting = min(c1, c2)
            northing = max(c1, c2)
            
            pt_top = lw[0]['top']
            
            # Determine pier for this point
            assigned_pier = ""
            if len(unique_line_tops) >= 2:
                for i in range(len(unique_line_tops) - 1):
                    y_start = unique_line_tops[i]
                    y_end = unique_line_tops[i+1]
                    if y_start - 3 <= pt_top <= y_end + 3:
                        matching_piers = [pw for pw in pier_words if y_start - 5 <= pw['top'] <= y_end + 5]
                        if matching_piers:
                            assigned_pier = matching_piers[0]['text'].strip().upper()
                        break
                        
            if not assigned_pier and pier_words:
                candidates = [pw for pw in pier_words if pw['top'] <= pt_top + 15]
                if candidates:
                    assigned_pier = candidates[-1]['text'].strip().upper()
                else:
                    assigned_pier = pier_words[0]['text'].strip().upper()
                    
            norm_pier = normalise_pier_id(assigned_pier, carriageway)
            is_valid, validation_msg = validate_coordinates(easting, northing)
            
            status = "Verified" if is_valid else "Review Required"
            notes = validation_msg if not is_valid else None
            
            rows.append({
                "point_id": pt_id,
                "pier_id": norm_pier,
                "carriageway": carriageway,
                "easting": easting,
                "northing": northing,
                "source_pdf": source_pdf,
                "source_page": page_num,
                "status": status,
                "notes": notes
            })
            
    return rows

def extract_tables_from_pdf(filepath: Path) -> List[Dict[str, Any]]:
    """
    Extracts all coordinate tables from a PDF file.
    Supports known CAD layout patterns for GAD 1 (2) 1.pdf, as well as generic coordinate tables.
    """
    filename = filepath.name
    # GAD 1 (1) is the master general arrangement drawing and bore logs; it contains no coordinate schedules.
    if "gad 1 (1)" in filename.lower() or "gad_1_1" in filename.lower():
        return []

    all_points = []
    
    with pdfplumber.open(str(filepath)) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            page_num = page_idx + 1
            text = page.extract_text() or ""
            
            upper = text.upper()
            # Check if this page contains coordinate tables
            if not any(k in upper for k in ["COORDINATES", "LOOP", "CARRIAGE", "EASTING"]):
                continue
                
            # GAD 1 (2) layout (or any 4-page foundation layout drawing)
            if "FOUNDATION LAYOUT" in upper or "GAD 1 (2)" in filename:
                if page_idx == 0:
                    # Page 0 (Main Carriageway LHS & RHS)
                    boxes = [
                        ((330, 600, 550, 1045), "LHS Carriageway"),
                        ((550, 600, 770, 1045), "LHS Carriageway"),
                        ((770, 600, 990, 1045), "RHS Carriageway"),
                        ((990, 600, 1210, 1045), "RHS Carriageway"),
                    ]
                    for bbox, cw in boxes:
                        pts = parse_table_column_words(page, bbox, cw, filename, page_num)
                        all_points.extend(pts)
                        
                elif page_idx == 1:
                    # Page 1 (Main Carriageway continuation)
                    boxes = [
                        ((230, 565, 455, 1045), "LHS Carriageway"),
                        ((455, 565, 680, 1045), "LHS Carriageway"),
                        ((680, 565, 905, 1045), "RHS Carriageway"),
                        ((905, 565, 1130, 1045), "RHS Carriageway"),
                    ]
                    for bbox, cw in boxes:
                        pts = parse_table_column_words(page, bbox, cw, filename, page_num)
                        all_points.extend(pts)
                        
                elif page_idx == 2:
                    # Page 2 (Loop-1 & Loop-2)
                    boxes = [
                        ((1050, 135, 1350, 850), "Loop-1"),
                        ((1350, 135, 1650, 850), "Loop-2"),
                    ]
                    for bbox, cw in boxes:
                        pts = parse_table_column_words(page, bbox, cw, filename, page_num)
                        all_points.extend(pts)
                        
                elif page_idx == 3:
                    # Page 3 (Loop-3 & Loop-4)
                    boxes = [
                        ((1150, 135, 1390, 850), "Loop-3"),
                        ((1390, 135, 1650, 850), "Loop-4"),
                    ]
                    for bbox, cw in boxes:
                        pts = parse_table_column_words(page, bbox, cw, filename, page_num)
                        all_points.extend(pts)
            else:
                # Generic fallback using pdfplumber table extraction
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    # Inspect header
                    header = [str(c).upper() for c in table[0] if c]
                    header_str = " ".join(header)
                    if "EASTING" in header_str or "NORTHING" in header_str or "POINT" in header_str:
                        # Detect carriageway from surrounding text or header
                        cw = normalise_carriageway(header_str)
                        current_pier = ""
                        for row in table[1:]:
                            clean_row = [str(c).strip() if c else "" for c in row]
                            # Try to extract pier, point, easting, northing
                            # Row can be [Pier, Point, Easting, Northing]
                            if len(clean_row) >= 4:
                                p_id, pt_id, e_str, n_str = clean_row[:4]
                                if p_id:
                                    current_pier = normalise_pier_id(p_id, cw)
                                if pt_id and e_str and n_str:
                                    try:
                                        e_val = float(re.sub(r'[^\d.]', '', e_str))
                                        n_val = float(re.sub(r'[^\d.]', '', n_str))
                                        valid, msg = validate_coordinates(e_val, n_val)
                                        all_points.append({
                                            "point_id": normalise_point_id(pt_id),
                                            "pier_id": current_pier,
                                            "carriageway": cw,
                                            "easting": min(e_val, n_val),
                                            "northing": max(e_val, n_val),
                                            "source_pdf": filename,
                                            "source_page": page_num,
                                            "status": "Verified" if valid else "Review Required",
                                            "notes": msg
                                        })
                                    except ValueError:
                                        continue

    log_event("INFO", "EXTRACT", f"Extracted {len(all_points)} raw corner points from {filename}.", filename=filename)
    return all_points
