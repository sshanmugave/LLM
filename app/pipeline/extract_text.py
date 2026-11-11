import re
from typing import Dict, List, Any
from pathlib import Path
import fitz
from app.database import log_event

def extract_project_notes_and_scps(filepath: Path) -> Dict[str, Any]:
    """
    Extracts high-level notes, excluded piers, chainage information,
    and Survey Control Points from CAD drawing text.
    """
    filename = filepath.name
    doc = fitz.open(str(filepath))
    
    excluded_piers = []
    survey_control_points = []
    span_lengths = []
    notes = []
    
    for page_idx in range(len(doc)):
        text = doc[page_idx].get_text()
        page_num = page_idx + 1
        
        # Look for excluded piers e.g. "PIER NUMBER P3 & P11 NOT USED"
        not_used_match = re.search(r'PIER\s+NUMBER\s+([^\n\r]+?)\s+NOT\s+USED', text, re.I)
        if not_used_match:
            desc = not_used_match.group(0).strip()
            # Extract pier tokens: P3, P11
            piers = re.findall(r'\b(P\d+)\b', not_used_match.group(1), re.I)
            excluded_piers.extend(piers)
            notes.append(f"Page {page_num}: {desc}")
            
        # Look for Survey Control Points (SCPs) in MCW P&P:
        # e.g. SCP-102: E=385367.654, N=1453228.207, RL=40.287
        scp_matches = re.finditer(r'(SCP\s*[-–]\s*\d+)[^\n]*?(?:E\s*=\s*|EASTING\s*[:=]\s*)(\d{6}(?:\.\d+)?)[^\n]*?(?:N\s*=\s*|NORTHING\s*[:=]\s*)(\d{7}(?:\.\d+)?)', text, re.I)
        for m in scp_matches:
            scp_name = re.sub(r'\s+', '', m.group(1).upper())
            easting = float(m.group(2))
            northing = float(m.group(3))
            survey_control_points.append({
                "name": scp_name,
                "easting": easting,
                "northing": northing,
                "source_pdf": filename,
                "source_page": page_num
            })
            
        # Look for typical span lengths: e.g. 30000 mm (30m)
        spans = re.findall(r'\b(2[0-9]{4}|3[0-9]{4}|4[0-9]{4})\b', text)
        if spans:
            for s in spans:
                if s in ["30000", "25000", "35000", "40000"]:
                    span_lengths.append(int(s))
                    
    doc.close()
    
    log_event("INFO", "TEXT", f"Extracted notes from {filename}: Excluded piers: {excluded_piers}, SCPs: {len(survey_control_points)}", filename=filename)
    return {
        "excluded_piers": sorted(list(set(excluded_piers))),
        "survey_control_points": survey_control_points,
        "span_lengths": sorted(list(set(span_lengths))),
        "notes": notes
    }
