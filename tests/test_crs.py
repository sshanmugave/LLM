import pytest
from app.pipeline.crs_handler import (
    convert_projected_to_latlon,
    convert_latlon_to_projected,
    detect_crs_from_text
)

def test_utm_to_latlon_conversion():
    # Point from GAD 1(2): Easting=385993.744, Northing=1452420.52
    easting = 385993.744
    northing = 1452420.52
    lat, lon = convert_projected_to_latlon(easting, northing, 32644)
    
    # Coordinates in Chennai region (approx 13.13° N, 79.94° E)
    assert 13.0 < lat < 13.5
    assert 79.5 < lon < 80.5
    
    # Test round trip conversion
    round_e, round_n = convert_latlon_to_projected(lat, lon, 32644)
    assert abs(round_e - easting) < 0.01
    assert abs(round_n - northing) < 0.01

def test_crs_detection():
    text1 = "Drawing references: Coordinates are based on UTM Zone 44N projection"
    detected1 = detect_crs_from_text(text1)
    assert detected1 is not None
    assert detected1["epsg_code"] == 32644

    text2 = "Refer to EPSG:32644 for geodetic reference"
    detected2 = detect_crs_from_text(text2)
    assert detected2 is not None
    assert detected2["epsg_code"] == 32644

    text3 = "No projection details provided"
    assert detect_crs_from_text(text3) is None
