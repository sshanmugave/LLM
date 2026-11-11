import pytest
import os
from pathlib import Path
import openpyxl
from app.config import INPUT_DIR, OUTPUT_DIR
from app.database import init_db, get_connection
from app.pipeline.orchestrator import run_full_extraction_pipeline
from app.export.excel_writer import create_excel_export
from app.export.csv_writer import create_csv_export

def test_full_pipeline_on_workspace_pdfs():
    """
    Executes the complete 3D pipeline strictly on GAD 1 (1) and GAD 1 (2):
    - Verifies extraction across RHS, LHS, and Loops 1-4
    - Verifies pier count, point count, and 3D dimensions
    - Verifies deck sections, borehole logs, and AI insights
    - Verifies master 7-sheet Excel export
    """
    init_db()
    
    # Run the full end-to-end 3D extraction pipeline
    result = run_full_extraction_pipeline()
    assert "error" not in result
    assert result["total_points"] > 200
    assert result["total_piers"] > 10
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check piers exist for all required sections
    cursor.execute("SELECT DISTINCT carriageway FROM piers")
    sections = [r[0] for r in cursor.fetchall()]
    assert "RHS Carriageway" in sections
    assert "LHS Carriageway" in sections
    assert "Loop-1" in sections
    assert "Loop-2" in sections
    assert "Loop-3" in sections
    assert "Loop-4" in sections
    
    # Verify first pier in each section has distance_from_previous is None
    for cw in sections:
        cursor.execute("SELECT pier_id, distance_from_previous FROM piers WHERE carriageway = ? ORDER BY sequence_order, id LIMIT 1", (cw,))
        first_pier = cursor.fetchone()
        assert first_pier is not None
        assert first_pier["distance_from_previous"] is None
        
    # Verify coordinates are in valid range
    cursor.execute("SELECT pier_id, latitude, longitude, centre_easting, centre_northing FROM piers WHERE centre_easting IS NOT NULL")
    for r in cursor.fetchall():
        assert 13.0 < r["latitude"] < 13.5
        assert 79.5 < r["longitude"] < 80.5
        assert 385000.0 < r["centre_easting"] < 387000.0
        assert 1452000.0 < r["centre_northing"] < 1453000.0
        
    # Verify 3D parameters were populated
    cursor.execute("SELECT pier_cap_width, pier_shaft_width, span_length FROM piers WHERE carriageway = 'RHS Carriageway' LIMIT 1")
    mcw_pier = cursor.fetchone()
    assert mcw_pier is not None
    assert mcw_pier["pier_cap_width"] == 13600.0
    assert mcw_pier["pier_shaft_width"] == 5000.0
    assert mcw_pier["span_length"] == 30000.0

    # Verify CAD deck sections
    cursor.execute("SELECT COUNT(*) FROM deck_sections")
    sec_count = cursor.fetchone()[0]
    assert sec_count >= 2

    # Verify borehole logs
    cursor.execute("SELECT COUNT(*) FROM borehole_logs")
    bh_count = cursor.fetchone()[0]
    assert bh_count >= 10

    # Verify AI insights
    cursor.execute("SELECT COUNT(*) FROM executive_insights")
    ai_count = cursor.fetchone()[0]
    assert ai_count >= 4

    conn.close()
    
    # Verify Master 7-Sheet Excel export generation
    excel_path = create_excel_export("Test_Flyover_3D_Master.xlsx")
    assert excel_path.exists()
    assert excel_path.stat().st_size > 8000
    
    wb = openpyxl.load_workbook(excel_path)
    sheet_names = wb.sheetnames
    assert "3D_Pier_Master_Catalog" in sheet_names
    assert "3D_Footing_Polygons" in sheet_names
    assert "Superstructure_3D_Deck" in sheet_names
    assert "Span_&_Longitudinal_Profile" in sheet_names
    assert "Geotechnical_Subsurface_3D" in sheet_names
    assert "Materials_&_Engineering_Specs" in sheet_names
    assert "Executive_Summary_&_Insights" in sheet_names
    assert len(sheet_names) == 7
    
    # Verify CSV export generation
    csv_piers = create_csv_export("piers", "Test_Piers.csv")
    assert csv_piers.exists()
    assert csv_piers.stat().st_size > 1000
    
    csv_points = create_csv_export("corner_points", "Test_Points.csv")
    assert csv_points.exists()
    assert csv_points.stat().st_size > 2000
