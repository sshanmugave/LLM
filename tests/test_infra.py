import pytest
import sqlite3
import os
from pathlib import Path
from app.config import DB_PATH, INPUT_DIR, OUTPUT_DIR
from app.database import init_db, get_connection, log_event, get_crs, update_crs

def test_database_initialization():
    # Test DB init
    init_db()
    assert os.path.exists(DB_PATH)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    assert "pdfs" in tables
    assert "pages" in tables
    assert "corner_points" in tables
    assert "piers" in tables
    assert "processing_logs" in tables
    assert "crs_settings" in tables

def test_crs_settings():
    init_db()
    crs = get_crs()
    assert crs["epsg_code"] == 32644
    assert "UTM" in crs["name"]
    
    update_crs(32643, "WGS 84 / UTM zone 43N", is_verified=True, detection_source="Test")
    crs_updated = get_crs()
    assert crs_updated["epsg_code"] == 32643
    assert crs_updated["is_verified"] == 1
    
    # Restore default
    update_crs(32644, "WGS 84 / UTM zone 44N", is_verified=False, detection_source="Default fallback")

def test_logging():
    init_db()
    log_event("INFO", "TEST", "Testing logging mechanism", filename="test.pdf", page_number=1)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM processing_logs WHERE category = 'TEST' ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    assert row["message"] == "Testing logging mechanism"
    assert row["filename"] == "test.pdf"
