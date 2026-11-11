import re
from typing import Optional

def normalise_carriageway(raw: str) -> str:
    """Normalises carriageway / section text into standard naming."""
    if not raw:
        return "Unknown"
    
    clean = raw.strip()
    upper = clean.upper()
    
    if "RHS" in upper or "RIGHT" in upper:
        return "RHS Carriageway"
    if "LHS" in upper or "LEFT" in upper:
        return "LHS Carriageway"
    if "LOOP-1" in upper or "LOOP 1" in upper or "LOOP1" in upper:
        return "Loop-1"
    if "LOOP-2" in upper or "LOOP 2" in upper or "LOOP2" in upper:
        return "Loop-2"
    if "LOOP-3" in upper or "LOOP 3" in upper or "LOOP3" in upper:
        return "Loop-3"
    if "LOOP-4" in upper or "LOOP 4" in upper or "LOOP4" in upper:
        return "Loop-4"
        
    return clean

def normalise_pier_id(raw_pier: str, carriageway: Optional[str] = None) -> str:
    """
    Normalises pier ID.
    Converts:
    - 'P 15', 'P-15', 'p15' -> 'P15'
    - 'A 1', 'a1', 'A-1' -> 'A1'
    - Loop piers: '1P1' -> 'Loop1-P1', '2P14' -> 'Loop2-P14' (as requested by user)
    """
    if not raw_pier:
        return ""
    
    clean = raw_pier.strip().upper()
    # Replace dashes and spaces
    clean = re.sub(r'[\s\-]+', '', clean)
    
    # Check for loop pier/abutment pattern: e.g. 1P1, 1A1, 2P3, 3P14, 4P2
    loop_match = re.match(r'^([1-4])([AP])(\d+)$', clean)
    if loop_match:
        loop_num = loop_match.group(1)
        pier_type = loop_match.group(2)
        pier_num = int(loop_match.group(3))
        return f"Loop{loop_num}-{pier_type}{pier_num}"
    
    # If carriageway is already Loop-X and pier is just P1
    if carriageway and carriageway.startswith("Loop-"):
        loop_num = carriageway.replace("Loop-", "").strip()
        p_match = re.match(r'^P?(\d+)$', clean)
        if p_match:
            return f"Loop{loop_num}-P{p_match.group(1)}"
            
    # Standard Main Carriageway piers: A1, A2, P1, P2...
    abutment_match = re.match(r'^A(\d+)$', clean)
    if abutment_match:
        return f"A{int(abutment_match.group(1))}"
        
    pier_match = re.match(r'^P(\d+)$', clean)
    if pier_match:
        return f"P{int(pier_match.group(1))}"
        
    return clean

def normalise_point_id(raw_point: str) -> str:
    """
    Normalises point IDs:
    - 'P 01', 'p1' -> 'P01' or 'P1'
    - 'L 01', 'l-01' -> 'L01'
    """
    if not raw_point:
        return ""
        
    clean = raw_point.strip().upper()
    clean = re.sub(r'[\s\-]+', '', clean)
    
    # Check for L points (Loop points): L01, L120
    l_match = re.match(r'^L(\d+)$', clean)
    if l_match:
        num = int(l_match.group(1))
        # Keep 2-digit minimum format L01, L56, L100
        return f"L{num:02d}"
        
    # Check for P points: P01, P120
    p_match = re.match(r'^P(\d+)$', clean)
    if p_match:
        num = int(p_match.group(1))
        return f"P{num:02d}"
        
    return clean

def extract_pier_sequence_order(pier_id: str) -> int:
    """Provides an integer sequence for sorting piers logically within a section."""
    if not pier_id:
        return 999
    
    # Abutment A1 is first
    if pier_id == "A1":
        return 0
    # Abutment A2 is last (in main carriageway)
    if pier_id == "A2":
        return 500
        
    # Pier P1, P2, ...
    p_match = re.match(r'^P(\d+)$', pier_id)
    if p_match:
        return int(p_match.group(1))
        
    # Loop pier e.g. Loop1-P1 or Loop1-A1
    loop_match = re.match(r'^Loop\d+\-([AP])(\d+)$', pier_id)
    if loop_match:
        ptype = loop_match.group(1)
        pnum = int(loop_match.group(2))
        return pnum if ptype == 'P' else (500 + pnum)
        
    return 999
