import pytest
from app.pipeline.normalise import (
    normalise_carriageway,
    normalise_pier_id,
    normalise_point_id,
    extract_pier_sequence_order
)

def test_normalise_carriageway():
    assert normalise_carriageway("LHS CARRIAGE WAY COORDINATES") == "LHS Carriageway"
    assert normalise_carriageway("RHS") == "RHS Carriageway"
    assert normalise_carriageway("LOOP-1 COORDINATES") == "Loop-1"
    assert normalise_carriageway("Loop 2") == "Loop-2"
    assert normalise_carriageway("Loop4") == "Loop-4"

def test_normalise_pier_id():
    # User specifically requested prefixing Loop piers with section name: Loop1-P1
    assert normalise_pier_id("1P1") == "Loop1-P1"
    assert normalise_pier_id("1A1") == "Loop1-A1"
    assert normalise_pier_id("2P14") == "Loop2-P14"
    assert normalise_pier_id("3P2") == "Loop3-P2"
    assert normalise_pier_id("4P10") == "Loop4-P10"
    
    # Main carriageway
    assert normalise_pier_id("P 15") == "P15"
    assert normalise_pier_id("p-15") == "P15"
    assert normalise_pier_id("P02") == "P2"
    assert normalise_pier_id("A1") == "A1"
    assert normalise_pier_id("a 2") == "A2"

def test_normalise_point_id():
    assert normalise_point_id("P 01") == "P01"
    assert normalise_point_id("p1") == "P01"
    assert normalise_point_id("P120") == "P120"
    assert normalise_point_id("L 05") == "L05"
    assert normalise_point_id("l-57") == "L57"

def test_pier_sequence_order():
    assert extract_pier_sequence_order("A1") == 0
    assert extract_pier_sequence_order("P1") == 1
    assert extract_pier_sequence_order("P15") == 15
    assert extract_pier_sequence_order("A2") == 500
    assert extract_pier_sequence_order("Loop1-P4") == 4
