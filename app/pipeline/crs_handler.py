import re
from typing import Tuple, Optional, Dict, Any
from pyproj import Transformer, CRS
from app.config import DEFAULT_EPSG, DEFAULT_CRS_NAME

_transformers = {}

def get_transformer(from_epsg: int, to_epsg: int = 4326) -> Transformer:
    key = (from_epsg, to_epsg)
    if key not in _transformers:
        _transformers[key] = Transformer.from_crs(
            CRS.from_epsg(from_epsg),
            CRS.from_epsg(to_epsg),
            always_xy=True
        )
    return _transformers[key]

def convert_projected_to_latlon(easting: float, northing: float, epsg_code: int = DEFAULT_EPSG) -> Tuple[float, float]:
    """
    Converts Easting, Northing in projected CRS (e.g. UTM 44N EPSG:32644) to (Latitude, Longitude).
    Returns (latitude, longitude) rounded to 8 decimal places.
    """
    try:
        transformer = get_transformer(epsg_code, 4326)
        # always_xy=True means transformer.transform(x, y) returns (lon, lat)
        lon, lat = transformer.transform(easting, northing)
        return round(float(lat), 8), round(float(lon), 8)
    except Exception as e:
        raise ValueError(f"CRS conversion failed for Easting={easting}, Northing={northing}, EPSG={epsg_code}: {str(e)}")

def convert_latlon_to_projected(lat: float, lon: float, epsg_code: int = DEFAULT_EPSG) -> Tuple[float, float]:
    """
    Converts Latitude, Longitude back to projected (Easting, Northing).
    Useful for round-trip validation.
    """
    try:
        transformer = get_transformer(4326, epsg_code)
        x, y = transformer.transform(lon, lat)
        return round(float(x), 4), round(float(y), 4)
    except Exception as e:
        raise ValueError(f"Inverse CRS conversion failed for Lat={lat}, Lon={lon}, EPSG={epsg_code}: {str(e)}")

def detect_crs_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Scans drawing text, title blocks, and notes for CRS clues.
    Looks for UTM Zone mentions, EPSG references, and Indian grid notes.
    """
    if not text:
        return None
        
    upper = text.upper()
    
    # Check explicit EPSG: e.g. EPSG:32644
    epsg_match = re.search(r'EPSG[:\s]*(\d{4,5})', upper)
    if epsg_match:
        code = int(epsg_match.group(1))
        try:
            crs_obj = CRS.from_epsg(code)
            return {
                "epsg_code": code,
                "name": crs_obj.name,
                "confidence": 1.0,
                "source": f"Found explicit '{epsg_match.group(0)}'"
            }
        except Exception:
            pass

    # Check UTM Zone 44N or 43N
    utm_match = re.search(r'UTM\s*(?:ZONE)?\s*(4[34])\s*(?:N|NORTH)?', upper)
    if utm_match:
        zone = int(utm_match.group(1))
        epsg = 32644 if zone == 44 else 32643
        return {
            "epsg_code": epsg,
            "name": f"WGS 84 / UTM zone {zone}N",
            "confidence": 0.9,
            "source": f"Found text mention '{utm_match.group(0)}'"
        }
        
    # Check WGS84 mention
    if "WGS84" in upper or "WGS 84" in upper or "WGS-84" in upper:
        return {
            "epsg_code": 32644,
            "name": "WGS 84 / UTM zone 44N",
            "confidence": 0.8,
            "source": "Found WGS84 mention in project notes"
        }

    return None
