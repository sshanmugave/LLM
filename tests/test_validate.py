import pytest
from app.pipeline.validate import (
    validate_coordinates,
    validate_pier_point_cluster,
    check_coordinate_conflict
)

def test_validate_coordinates():
    # Valid Chennai UTM 44N point
    valid, err = validate_coordinates(385993.744, 1452420.520)
    assert valid is True
    assert err is None
    
    # Swapped coordinates
    valid_swap, err_swap = validate_coordinates(1452420.520, 385993.744)
    assert valid_swap is False
    assert "SWAPPED" in err_swap
    
    # Out of range Easting
    valid_e, err_e = validate_coordinates(100.0, 1452420.520)
    assert valid_e is False
    assert "Easting" in err_e

def test_pier_cluster_validation():
    # Footing corner points within 15m
    close_points = [
        (385993.744, 1452420.520),
        (385999.202, 1452417.569),
        (385995.000, 1452425.000)
    ]
    valid, err = validate_pier_point_cluster(close_points)
    assert valid is True
    
    # Points 200m apart (e.g. wrong pier mapping)
    dispersed_points = [
        (385993.744, 1452420.520),
        (386200.000, 1452600.000)
    ]
    valid_disp, err_disp = validate_pier_point_cluster(dispersed_points)
    assert valid_disp is False
    assert "footing boundary" in err_disp

def test_coordinate_conflict():
    pt1 = (385993.744, 1452420.520)
    pt2 = (385993.745, 1452420.519) # 1mm difference -> no conflict
    has_conf, diff = check_coordinate_conflict(pt1, pt2, tolerance_m=0.05)
    assert has_conf is False
    assert diff < 0.05
    
    pt3 = (385993.900, 1452420.520) # 156mm difference -> conflict
    has_conf3, diff3 = check_coordinate_conflict(pt1, pt3, tolerance_m=0.05)
    assert has_conf3 is True
    assert diff3 > 0.05
