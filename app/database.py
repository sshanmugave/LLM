import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from app.config import DB_PATH, DEFAULT_EPSG, DEFAULT_CRS_NAME

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 10000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS pdfs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE NOT NULL,
        filepath TEXT NOT NULL,
        page_count INTEGER DEFAULT 0,
        file_hash TEXT,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pdf_id INTEGER NOT NULL,
        page_index INTEGER NOT NULL,
        page_number INTEGER NOT NULL,
        page_type TEXT DEFAULT 'unknown',
        image_path TEXT,
        raw_text TEXT,
        FOREIGN KEY (pdf_id) REFERENCES pdfs(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS corner_points (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        point_id TEXT NOT NULL,
        pier_id TEXT NOT NULL,
        carriageway TEXT NOT NULL,
        easting REAL NOT NULL,
        northing REAL NOT NULL,
        source_pdf TEXT NOT NULL,
        source_page INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Verified',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS piers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        carriageway TEXT NOT NULL,
        pier_id TEXT NOT NULL,
        point_range TEXT,
        latitude REAL,
        longitude REAL,
        distance_from_previous REAL,
        pier_height REAL,
        pier_width REAL,
        pier_cap_height REAL,
        pier_cap_width REAL,
        pier_cap_center_depth REAL,
        pier_cap_tip_depth REAL,
        pier_cap_cantilever REAL,
        pier_shaft_width REAL,
        pier_shaft_thickness REAL,
        pedestal_height REAL,
        bearing_offset REAL,
        skew_angle_deg REAL,
        footing_length REAL,
        footing_width REAL,
        span_length REAL,
        dimension_units TEXT DEFAULT 'mm',
        centre_easting REAL,
        centre_northing REAL,
        source_pdfs TEXT,
        source_pages TEXT,
        status TEXT NOT NULL DEFAULT 'Verified',
        notes TEXT,
        sequence_order INTEGER,
        UNIQUE(carriageway, pier_id)
    );

    CREATE TABLE IF NOT EXISTS borehole_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        borehole_id TEXT NOT NULL,
        sheet_number TEXT,
        chainage TEXT,
        depth_from REAL NOT NULL,
        depth_to REAL NOT NULL,
        strata_description TEXT NOT NULL,
        spt_n_value TEXT,
        water_table_m REAL,
        foundation_depth_df REAL,
        source_pdf TEXT,
        source_page INTEGER
    );

    CREATE TABLE IF NOT EXISTS deck_sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_name TEXT UNIQUE NOT NULL,
        description TEXT,
        carriageway_deck_width REAL,
        roadway_width REAL,
        median_gap REAL,
        deck_slab_thk REAL,
        wearing_coat_thk REAL,
        cross_slope_pct REAL,
        crash_barrier_width REAL,
        curb_height REAL,
        girder_type TEXT,
        girder_depth REAL,
        concrete_grade TEXT,
        scale TEXT
    );

    CREATE TABLE IF NOT EXISTS executive_insights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        generated_by TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS processing_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        level TEXT NOT NULL,
        category TEXT NOT NULL,
        message TEXT NOT NULL,
        filename TEXT,
        page_number INTEGER
    );

    CREATE TABLE IF NOT EXISTS crs_settings (
        id INTEGER PRIMARY KEY,
        epsg_code INTEGER NOT NULL,
        name TEXT NOT NULL,
        is_verified BOOLEAN NOT NULL DEFAULT 0,
        detection_source TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS conflicts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        point_id TEXT NOT NULL,
        pier_id TEXT,
        carriageway TEXT,
        first_easting REAL,
        first_northing REAL,
        first_source TEXT,
        second_easting REAL,
        second_northing REAL,
        second_source TEXT,
        difference_m REAL,
        resolved BOOLEAN DEFAULT 0,
        resolution_notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """);

    # Initialize default CRS if not present
    cursor.execute("SELECT COUNT(*) FROM crs_settings WHERE id = 1")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO crs_settings (id, epsg_code, name, is_verified, detection_source)
            VALUES (1, ?, ?, 0, 'Assumed based on project location (CPRR, Chennai)')
        """, (DEFAULT_EPSG, DEFAULT_CRS_NAME))

    # Automatic schema migration for existing databases
    cursor.execute("PRAGMA table_info(piers)")
    existing_cols = [r[1] for r in cursor.fetchall()]
    new_cols = [
        ("skew_angle_deg", "REAL"),
        ("footing_length", "REAL"),
        ("footing_width", "REAL"),
        ("span_length", "REAL"),
        ("pier_cap_center_depth", "REAL"),
        ("pier_cap_tip_depth", "REAL"),
        ("pier_cap_cantilever", "REAL"),
        ("pier_shaft_width", "REAL"),
        ("pier_shaft_thickness", "REAL"),
        ("pedestal_height", "REAL"),
        ("bearing_offset", "REAL")
    ]
    for col_name, col_type in new_cols:
        if col_name not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE piers ADD COLUMN {col_name} {col_type}")
            except Exception:
                pass

    # Migration: add documents table for multi-format ingestion
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            filepath TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_hash TEXT,
            file_size_bytes INTEGER DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'registered',
            is_valid BOOLEAN NOT NULL DEFAULT 1,
            error_message TEXT,
            meta_json TEXT,
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Ensure is_valid and error_message columns exist if documents already created
    cursor.execute("PRAGMA table_info(documents)")
    doc_cols = [r[1] for r in cursor.fetchall()]
    if "is_valid" not in doc_cols:
        try:
            cursor.execute("ALTER TABLE documents ADD COLUMN is_valid BOOLEAN NOT NULL DEFAULT 1")
        except Exception:
            pass
    if "error_message" not in doc_cols:
        try:
            cursor.execute("ALTER TABLE documents ADD COLUMN error_message TEXT")
        except Exception:
            pass

    # Migration: add run_history table to store previous pipeline runs safely
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS run_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT UNIQUE NOT NULL,
            label TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_piers INTEGER DEFAULT 0,
            total_points INTEGER DEFAULT 0,
            total_sections INTEGER DEFAULT 0,
            total_boreholes INTEGER DEFAULT 0,
            status TEXT DEFAULT 'completed',
            snapshot_json TEXT
        )
    """)

    conn.commit()
    conn.close()

def log_event(level: str, category: str, message: str, filename: Optional[str] = None, page_number: Optional[int] = None, conn: Optional[sqlite3.Connection] = None):
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True
        
    try:
        conn.execute("""
            INSERT INTO processing_logs (level, category, message, filename, page_number)
            VALUES (?, ?, ?, ?, ?)
        """, (level, category, message, filename, page_number))
        conn.commit()
    finally:
        if should_close:
            conn.close()

def clear_extracted_data():
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM corner_points")
        conn.execute("DELETE FROM piers")
        conn.execute("DELETE FROM conflicts")
        conn.execute("DELETE FROM borehole_logs")
        conn.execute("DELETE FROM deck_sections")
        conn.execute("DELETE FROM executive_insights")
    conn.close()

def archive_current_run(label: str = "Pipeline Run Archive") -> Optional[str]:
    """
    Saves a complete snapshot of current extracted data into run_history table,
    so previous run data is never lost and can be inspected or restored anytime.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM piers")
    total_piers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM corner_points")
    total_points = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM deck_sections")
    total_sections = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM borehole_logs")
    total_boreholes = cursor.fetchone()[0]

    if total_piers == 0 and total_points == 0 and total_sections == 0 and total_boreholes == 0:
        conn.close()
        return None

    # Fetch rows
    piers = [dict(r) for r in cursor.execute("SELECT * FROM piers").fetchall()]
    points = [dict(r) for r in cursor.execute("SELECT * FROM corner_points").fetchall()]
    deck = [dict(r) for r in cursor.execute("SELECT * FROM deck_sections").fetchall()]
    geo = [dict(r) for r in cursor.execute("SELECT * FROM borehole_logs").fetchall()]
    insights = [dict(r) for r in cursor.execute("SELECT * FROM executive_insights").fetchall()]

    snapshot = {
        "piers": piers,
        "corner_points": points,
        "deck_sections": deck,
        "borehole_logs": geo,
        "executive_insights": insights
    }
    snapshot_json = json.dumps(snapshot)

    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"RUN_{now_str}"

    with conn:
        conn.execute("""
            INSERT INTO run_history (run_id, label, total_piers, total_points, total_sections, total_boreholes, snapshot_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (run_id, label, total_piers, total_points, total_sections, total_boreholes, snapshot_json))

    conn.close()
    log_event("INFO", "ARCHIVE", f"Archived run {run_id} ({total_piers} piers, {total_points} points)")
    return run_id

def get_run_history() -> List[Dict[str, Any]]:
    """Returns metadata for all archived runs (without heavy snapshot payload)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, run_id, label, timestamp, total_piers, total_points, total_sections, total_boreholes, status
        FROM run_history ORDER BY id DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def restore_run_from_history(run_id: str) -> bool:
    """Restores an archived run into active catalog tables."""
    conn = get_connection()
    row = conn.execute("SELECT snapshot_json FROM run_history WHERE run_id = ?", (run_id,)).fetchone()
    if not row or not row["snapshot_json"]:
        conn.close()
        return False

    snapshot = json.loads(row["snapshot_json"])

    # Clear current active
    with conn:
        conn.execute("DELETE FROM corner_points")
        conn.execute("DELETE FROM piers")
        conn.execute("DELETE FROM deck_sections")
        conn.execute("DELETE FROM borehole_logs")
        conn.execute("DELETE FROM executive_insights")

        # Restore piers
        for p in snapshot.get("piers", []):
            keys = [k for k in p.keys() if k != "id"]
            vals = [p[k] for k in keys]
            placeholders = ", ".join(["?"] * len(keys))
            conn.execute(f"INSERT OR REPLACE INTO piers ({', '.join(keys)}) VALUES ({placeholders})", vals)

        # Restore points
        for pt in snapshot.get("corner_points", []):
            keys = [k for k in pt.keys() if k != "id"]
            vals = [pt[k] for k in keys]
            placeholders = ", ".join(["?"] * len(keys))
            conn.execute(f"INSERT OR REPLACE INTO corner_points ({', '.join(keys)}) VALUES ({placeholders})", vals)

        # Restore deck sections
        for ds in snapshot.get("deck_sections", []):
            keys = [k for k in ds.keys() if k != "id"]
            vals = [ds[k] for k in keys]
            placeholders = ", ".join(["?"] * len(keys))
            conn.execute(f"INSERT OR REPLACE INTO deck_sections ({', '.join(keys)}) VALUES ({placeholders})", vals)

        # Restore boreholes
        for bh in snapshot.get("borehole_logs", []):
            keys = [k for k in bh.keys() if k != "id"]
            vals = [bh[k] for k in keys]
            placeholders = ", ".join(["?"] * len(keys))
            conn.execute(f"INSERT OR REPLACE INTO borehole_logs ({', '.join(keys)}) VALUES ({placeholders})", vals)

        # Restore insights
        for ins in snapshot.get("executive_insights", []):
            keys = [k for k in ins.keys() if k != "id"]
            vals = [ins[k] for k in keys]
            placeholders = ", ".join(["?"] * len(keys))
            conn.execute(f"INSERT OR REPLACE INTO executive_insights ({', '.join(keys)}) VALUES ({placeholders})", vals)

    conn.close()
    log_event("INFO", "RESTORE", f"Restored archived run {run_id} into active view")
    return True

def delete_archived_run(run_id: str) -> bool:
    """Deletes a run from history."""
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM run_history WHERE run_id = ?", (run_id,))
    conn.close()
    return True

def get_crs():
    conn = get_connection()
    row = conn.execute("SELECT * FROM crs_settings WHERE id = 1").fetchone()
    conn.close()
    if row:
        return dict(row)
    return {
        "id": 1,
        "epsg_code": DEFAULT_EPSG,
        "name": DEFAULT_CRS_NAME,
        "is_verified": False,
        "detection_source": "Default fallback"
    }

def update_crs(epsg_code: int, name: str, is_verified: bool = True, detection_source: str = "User specified"):
    conn = get_connection()
    with conn:
        conn.execute("""
            UPDATE crs_settings 
            SET epsg_code = ?, name = ?, is_verified = ?, detection_source = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (epsg_code, name, 1 if is_verified else 0, detection_source))
    conn.close()
