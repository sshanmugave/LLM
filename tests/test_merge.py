import pytest
from app.database import init_db, get_connection
from app.pipeline.merge import merge_and_store_pipeline_data

def test_merge_duplicates_and_conflicts():
    init_db()
    
    # 2 matching duplicate points from different PDFs
    pt1 = {
        "point_id": "P01",
        "pier_id": "A1",
        "carriageway": "LHS Carriageway",
        "easting": 385999.744,
        "northing": 1452420.520,
        "source_pdf": "PDF1.pdf",
        "source_page": 1,
        "status": "Verified",
        "notes": None
    }
    pt1_dup = {
        "point_id": "P01",
        "pier_id": "A1",
        "carriageway": "LHS Carriageway",
        "easting": 385999.744, # identical
        "northing": 1452420.520,
        "source_pdf": "PDF2.pdf",
        "source_page": 2,
        "status": "Verified",
        "notes": None
    }
    
    # Conflicting point
    pt2 = {
        "point_id": "P02",
        "pier_id": "A1",
        "carriageway": "LHS Carriageway",
        "easting": 385999.200,
        "northing": 1452417.560,
        "source_pdf": "PDF1.pdf",
        "source_page": 1,
        "status": "Verified",
        "notes": None
    }
    pt2_conf = {
        "point_id": "P02",
        "pier_id": "A1",
        "carriageway": "LHS Carriageway",
        "easting": 385999.800, # 0.6m difference -> conflict!
        "northing": 1452417.560,
        "source_pdf": "PDF2.pdf",
        "source_page": 2,
        "status": "Verified",
        "notes": None
    }
    
    raw = [pt1, pt1_dup, pt2, pt2_conf]
    res = merge_and_store_pipeline_data(raw)
    
    assert res["total_points"] == 2 # P01 and P02
    assert res["duplicate_count"] == 1
    assert res["conflict_count"] == 1
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conflicts WHERE point_id = 'P02'")
    conflict_row = cursor.fetchone()
    assert conflict_row is not None
    assert conflict_row["difference_m"] > 0.05
    
    cursor.execute("SELECT * FROM corner_points WHERE point_id = 'P02'")
    p02_row = cursor.fetchone()
    assert p02_row["status"] == "Review Required"
    
    conn.close()
