import os
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple
import fitz  # PyMuPDF
from app.config import PAGE_IMAGES_DIR, INPUT_DIR
from app.database import get_connection, log_event

def compute_file_hash(filepath: str) -> str:
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def classify_page_type(text: str, has_tables: bool = False) -> str:
    """
    Classifies a PDF page into one of:
    - coordinate_table: contains coordinate schedule tables
    - plan_view: general arrangement or layout drawing
    - profile: vertical road profile
    - bore_log: geotechnical borehole logs
    - title_block: cover/metadata only
    - unknown
    """
    if not text:
        return "unknown"
        
    upper = text.upper()
    
    # Borehole logs
    if "BORE" in upper and ("N VALUE" in upper or "STRATA" in upper or "SOIL PROFILE" in upper):
        return "bore_log"
        
    # Coordinate table
    if ("COORDINATES" in upper and ("EASTING" in upper or "NORTHING" in upper)) or \
       ("LOOP-1 COORDINATES" in upper or "LOOP-2 COORDINATES" in upper or \
        "LOOP-3 COORDINATES" in upper or "LOOP-4 COORDINATES" in upper or \
        "CARRIAGE WAY COORDINATES" in upper):
        return "coordinate_table"
        
    # Vertical Profile
    if "PROFILE" in upper and ("DATUM" in upper or "EXISTING ROAD LEVEL" in upper or "FINISHED ROAD LEVEL" in upper):
        return "profile"
        
    # Section drawing
    if "SECTION 1-1" in upper or "SECTION 2-2" in upper or "PIER DETAIL" in upper:
        return "section_drawing"
        
    # Plan view / General Arrangement
    if "GENERAL ARRANGEMENT" in upper or "FOUNDATION LAYOUT" in upper or "PLAN & PROFILE" in upper:
        return "plan_view"
        
    if "TAMILNADU ROAD INFRASTRUCTURE" in upper or "DRAWING NO" in upper:
        return "title_block"
        
    return "unknown"

def render_page_image(page: fitz.Page, output_path: Path, dpi: int = 150) -> str:
    """Renders a PDF page to a PNG image for UI display and vision AI."""
    if output_path.exists():
        return str(output_path)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    pix.save(str(output_path))
    return str(output_path)

def ingest_pdf_file(filepath: Path) -> Dict[str, Any]:
    """
    Ingests a single PDF file:
    - computes hash and registers in pdfs table
    - extracts text from every page
    - renders high-resolution page image for UI inspection
    - classifies page type
    - stores in pages table
    """
    conn = get_connection()
    cursor = conn.cursor()
    filename = filepath.name
    file_hash = compute_file_hash(str(filepath))
    
    doc = fitz.open(str(filepath))
    page_count = len(doc)
    
    # Insert or update pdfs table
    cursor.execute("""
        INSERT INTO pdfs (filename, filepath, page_count, file_hash)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(filename) DO UPDATE SET 
            filepath = excluded.filepath,
            page_count = excluded.page_count,
            file_hash = excluded.file_hash
    """, (filename, str(filepath), page_count, file_hash))
    conn.commit()
    
    cursor.execute("SELECT id FROM pdfs WHERE filename = ?", (filename,))
    pdf_id = cursor.fetchone()[0]
    
    # Clean previous pages for this pdf
    cursor.execute("DELETE FROM pages WHERE pdf_id = ?", (pdf_id,))
    conn.commit()
    
    ingested_pages = []
    
    # Safe prefix for image filenames
    safe_name = filename.replace(".pdf", "").replace(" ", "_").replace("(", "").replace(")", "")
    
    for page_idx in range(page_count):
        page = doc[page_idx]
        raw_text = page.get_text()
        page_type = classify_page_type(raw_text)
        
        # Render image
        img_name = f"{safe_name}_pg{page_idx}.png"
        img_path = PAGE_IMAGES_DIR / img_name
        if not img_path.exists():
            render_page_image(page, img_path, dpi=150)
            
        cursor.execute("""
            INSERT INTO pages (pdf_id, page_index, page_number, page_type, image_path, raw_text)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pdf_id, page_idx, page_idx + 1, page_type, f"/page_images/{img_name}", raw_text))
        
        ingested_pages.append({
            "page_index": page_idx,
            "page_number": page_idx + 1,
            "page_type": page_type,
            "image_path": f"/page_images/{img_name}"
        })
        
    conn.commit()
    conn.close()
    
    log_event("INFO", "INGEST", f"Ingested {filename}: {page_count} pages processed and classified.", filename=filename)
    return {
        "pdf_id": pdf_id,
        "filename": filename,
        "page_count": page_count,
        "pages": ingested_pages
    }
