import csv
from pathlib import Path
from typing import Optional
from app.config import OUTPUT_DIR
from app.database import get_connection

def create_csv_export(table_type: str = "piers", filename: Optional[str] = None) -> Path:
    """
    Exports Pier Centres or Corner Points as CSV.
    table_type: 'piers' or 'corner_points'
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if table_type == "piers":
        default_name = "Flyover_Pier_Centres.csv"
        out_filename = filename or default_name
        headers = [
            "Carriageway", "Pier ID", "Point Range", "Latitude", "Longitude",
            "Distance from Previous (m)", "Pier Height", "Pier Width",
            "Pier Cap Height", "Pier Cap Width", "Dimension Units",
            "Centre Easting", "Centre Northing", "Source PDFs", "Source Pages",
            "Status", "Notes"
        ]
        cursor.execute("""
            SELECT carriageway, pier_id, point_range, latitude, longitude,
                   distance_from_previous, pier_height, pier_width,
                   pier_cap_height, pier_cap_width, dimension_units,
                   centre_easting, centre_northing, source_pdfs, source_pages,
                   status, notes
            FROM piers
            ORDER BY carriageway, sequence_order, id
        """)
    else:
        default_name = "Flyover_Corner_Points.csv"
        out_filename = filename or default_name
        headers = [
            "Point ID", "Pier ID", "Carriageway", "Easting (X)", "Northing (Y)",
            "Source PDF", "Source Page", "Status", "Notes"
        ]
        cursor.execute("""
            SELECT point_id, pier_id, carriageway, easting, northing,
                   source_pdf, source_page, status, notes
            FROM corner_points
            ORDER BY carriageway, id
        """)
        
    rows = cursor.fetchall()
    conn.close()
    
    out_path = OUTPUT_DIR / out_filename
    with open(out_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for r in rows:
            writer.writerow(list(r))
            
    return out_path
