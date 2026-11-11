import pytest
import math
from app.pipeline.compute import (
    compute_pier_centre,
    calculate_distance,
    format_point_range
)

def test_compute_pier_centre():
    points = [
        (385993.744, 1452420.520),
        (385999.202, 1452417.569),
        (385991.000, 1452415.000),
        (385996.000, 1452412.000)
    ]
    centre = compute_pier_centre(points)
    assert centre is not None
    avg_e = (385993.744 + 385999.202 + 385991.000 + 385996.000) / 4
    avg_n = (1452420.520 + 1452417.569 + 1452415.000 + 1452412.000) / 4
    assert abs(centre[0] - avg_e) < 0.0001
    assert abs(centre[1] - avg_n) < 0.0001
    
    # Empty list
    assert compute_pier_centre([]) is None

def test_calculate_distance():
    p1 = (100.0, 100.0)
    p2 = (130.0, 140.0)
    # dx=30, dy=40 -> 50.0m
    dist = calculate_distance(p1, p2)
    assert dist == 50.0
    
    # First pier (no previous)
    assert calculate_distance(None, p2) is None
    assert calculate_distance(p1, None) is None

def test_format_point_range():
    # Consecutive range
    assert format_point_range(['P01', 'P02', 'P03', 'P04']) == 'P01-P04'
    assert format_point_range(['P169', 'P170', 'P171', 'P172']) == 'P169-P172'
    
    # Non-contiguous
    assert format_point_range(['P169', 'P170', 'P171', 'P172', 'P175']) == 'P169-P172, P175'
    assert format_point_range(['P01', 'P02', 'P05']) == 'P01-P02, P05'
    
    # Loops
    assert format_point_range(['L01', 'L02', 'L03', 'L04']) == 'L01-L04'
    
    # Single point
    assert format_point_range(['P01']) == 'P01'
    assert format_point_range([]) == ''
