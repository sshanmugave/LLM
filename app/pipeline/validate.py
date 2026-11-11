import math
from typing import List, Tuple, Dict, Any, Optional
from app.config import (
    VALID_EASTING_MIN, VALID_EASTING_MAX,
    VALID_NORTHING_MIN, VALID_NORTHING_MAX
)

def validate_coordinates(easting: float, northing: float) -> Tuple[bool, Optional[str]]:
    """
    Validates Easting and Northing values.
    Detects potential Easting/Northing swaps and out-of-range coordinates.
    """
    # Check for swapped coordinates
    if easting > 1000000.0 and northing < 1000000.0:
        return False, f"Coordinates appear SWAPPED: Easting={easting} > 1,000,000 and Northing={northing} < 1,000,000"
        
    if not (VALID_EASTING_MIN <= easting <= VALID_EASTING_MAX):
        return False, f"Easting {easting} outside plausible range ({VALID_EASTING_MIN} - {VALID_EASTING_MAX})"
        
    if not (VALID_NORTHING_MIN <= northing <= VALID_NORTHING_MAX):
        return False, f"Northing {northing} outside plausible range ({VALID_NORTHING_MIN} - {VALID_NORTHING_MAX})"
        
    return True, None

def validate_pier_point_cluster(points: List[Tuple[float, float]], max_allowed_spread_m: float = 60.0) -> Tuple[bool, Optional[str]]:
    """
    Verifies that all corner points belonging to a pier lie reasonably close to each other.
    Typical flyover pier foundations have a maximum dimension of 10-25m.
    """
    if len(points) <= 1:
        return True, None
        
    eastings = [p[0] for p in points]
    northings = [p[1] for p in points]
    
    spread_e = max(eastings) - min(eastings)
    spread_n = max(northings) - min(northings)
    max_dist = math.sqrt(spread_e**2 + spread_n**2)
    
    if max_dist > max_allowed_spread_m:
        return False, f"Pier points spread across {max_dist:.1f}m, which exceeds expected footing boundary ({max_allowed_spread_m}m)"
        
    return True, None

def check_coordinate_conflict(pt1: Tuple[float, float], pt2: Tuple[float, float], tolerance_m: float = 0.05) -> Tuple[bool, float]:
    """
    Checks if two extractions of the same point have conflicting coordinates.
    Returns (has_conflict, difference_in_metres).
    """
    dx = pt1[0] - pt2[0]
    dy = pt1[1] - pt2[1]
    diff = math.sqrt(dx**2 + dy**2)
    return diff > tolerance_m, round(diff, 4)
