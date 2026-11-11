# PLAN.md — Flyover Pier Coordinate Extractor

## 1. PDF Inspection Summary

### 1.1 Files Inspected

| File | Size | Pages | Type |
|------|------|-------|------|
| `GAD 1 (1) 1.pdf` | 19.7 MB | 10 | General Arrangement Drawing (plan view + bore logs) |
| `GAD 1 (2) 1.pdf` | 3.8 MB | 4 | Foundation Layout with Coordinate Tables |
| `MCW P&P 1.pdf` | 3.2 MB | 3 | Main Carriageway Plan & Profile |

### 1.2 Content Map

#### GAD 1 (1) 1.pdf — General Arrangement
- **Page 0**: Master plan view (SCALE 1:1000) — Shows all piers: A1, P1–P18, A2 for main carriageway; Loop-1 through Loop-4 with ramp piers. Also shows approach portions, borehole locations (BH20-BH69), span lengths (30000 mm), and reference drawings. Contains notes with concrete grades (M55, M40, M35, M15), dimension conventions ("ALL DIMENSIONS ARE IN MILLIMETERS, LEVELS ARE IN METRES AND CHAINAGES ARE IN KILOMETRES"), and key: LHS = Left Hand Side, RHS = Right Hand Side, MCW = Main Carriageway. Lists PIER NUMBER P3 & P11 NOT USED. Reference drawings listed: substructure drawings (O24087-C-RP-MB-NU-8360-8385), superstructure drawings (O24087-C-RP-MB-NU-8350-8346).
- **Pages 1–5**: Duplicate-like title block pages (1434 chars each) — appear to be additional sheets of the GAD, but extractable text is mostly title block metadata. These are likely landscape engineering drawings with embedded vector/image content but minimal searchable text. Each references drawing no. O24087-C-RP-MB-GA-8330.
- **Pages 6–9**: Bore log details — soil profile data (depth, N-value, soil type) for boreholes BH-20 through BH-30 at CH: 54/29. These contain foundation engineering data but NO pier coordinates or section drawings.

#### GAD 1 (2) 1.pdf — Foundation Layout (PRIMARY COORDINATE SOURCE)
- **Page 0**: Foundation layout plan + coordinate tables for **RHS & LHS Main Carriageway**.
  - **Plan view**: Shows pier corner point labels (P01–P198) mapped to piers (A1, P1–P7 for RHS/LHS).
  - **Coordinate Tables** (4 tables, 2 for LHS, 2 for RHS):
    - LHS Carriageway: Pier → Points → Easting(X) → Northing(Y)
    - RHS Carriageway: Pier → Points → Easting(X) → Northing(Y)
    - Sample: P01→P01 (385993.744, 1452420.52), P02 (385999.202, 1452417.569) etc.
    - Pier A1 mapped to P01–P04; P1 mapped to P05–P10; P2 to P11–P16; etc.
  - **Title**: "FOUNDATION LAYOUT FOR INTERCHANGE - MAIN CARRIAGEWAY"
  - **Notes**: "ALL DIMENSIONS ARE IN MILLIMETERS, LEVELS AND CHAINAGES ARE IN METERS"
  - **Drawing No**: O24087-C-RP-MB-NU-8390

- **Page 1**: Continuation of Main Carriageway coordinate tables.
  - More pier-to-point mappings for LHS (Pier P8→P67-P72, P9→P73-P78, P10→P79-P84, P11→P85-P90, P12→P91-P96, P13→P97-P105, continues to P106-P132)
  - RHS tables continue similarly.
  - **Title**: "FOUNDATION LAYOUT FOR INTERCHANGE - MAIN CARRIAGEWAY"

- **Page 2**: Foundation layout + coordinate tables for **Loop-1 and Loop-2**.
  - LOOP-1 COORDINATES: Pier 1P1→L01-L04, 1P2→L05-L08, ..., 1P14→L53-L56 (56 points)
  - LOOP-2 COORDINATES: Points L57–L113 (57 points), pier labels like 2P1, 2P2, etc.
  - Plan view shows Loop-1 and Loop-2 pier/point positions.
  - **Title**: "FOUNDATION LAYOUT FOR INTERCHANGE - LOOP 1 & 2"

- **Page 3**: Foundation layout + coordinate tables for **Loop-3 and Loop-4**.
  - LOOP-3 COORDINATES: Pier 3P1→L114-L117, ..., 3P14→L166-L169 (56 points)
  - LOOP-4 COORDINATES: Points L170–L225 (56 points), pier labels like 4P1, 4P2, etc.
  - **Title**: "FOUNDATION LAYOUT FOR INTERCHANGE - LOOP 3 & 4"

#### MCW P&P 1.pdf — Main Carriageway Plan & Profile
- **Page 0**: Plan view (SCALE 1:2000) showing CH 53+000 to ~53+800 with Survey Control Points (SCPs):
  - SCP-102: E=385367.654, N=1453228.207, RL=40.287
  - SCP-103: E=385469.968, N=1453120.831, RL=40.575
  - SCP-104: E=385626.462, N=1453105.706, RL=41.543
  - SCP-105: E=..., SCP-106: E=385894.325, N=1452793.194, RL=40.968
  - SCP-107: E=385955.429, N=1452561.994, RL=41.251
  - HIP No.54/1L: X=385575.28028, Y=1453130.1256 (with curve data R=1800m)
  - HIP No.54/2R: X=386053.00623, Y=1452735.22968 (with curve data R=900m)
  - **DATUM = 36** (for vertical profile)
  - Title: "MAIN CARRIAGEWAY PLAN & PROFILE FROM Km 53+000 TO Km 54+000"
  - Notes: "ALL DIMENSIONS AND CHAINAGES ARE IN METERS UNLESS OTHERWISE SPECIFIED"

- **Page 1**: Profile continuation CH ~54+000 to ~55+000 — vertical schematic with finished road levels, existing levels, superelevation data. **DATUM = 38**.

- **Page 2**: Plan & profile continuation CH ~55+000 to ~56+000. **DATUM = 38**.

### 1.3 Key Findings

1. **Coordinate System**: The coordinates are in **Easting/Northing** format. Values like E=385993, N=1452420 are consistent with **UTM Zone 44N** (Indian subcontinent, specifically Tamil Nadu / Chennai region). The Northing values ~1,452,000 correspond to latitude ~13.1°N. The project is for Chennai Peripheral Ring Road (CPRR), Tamil Nadu. **No explicit CRS/EPSG mentioned in any PDF**. The DATUM mentioned in MCW P&P is a **vertical datum** (reference level for road profiles), not a geodetic datum.

2. **No Section 1-1 to 5-5 Drawings Found**: None of the 3 PDFs contain section drawings labeled "Section 1-1" through "Section 5-5". The GAD 1(1) pages 1-5 appear to be additional plan sheets (with mostly vector content and minimal text), and pages 6-9 are bore logs. **Pier dimensions (height, width, cap height, cap width) are NOT present** in these PDFs. The Reference Drawings list on GAD 1(1) pg0 points to separate drawing numbers for substructure details (O24087-C-RP-MB-NU-8360-8385) which are not included in the provided files.

3. **Pier-to-Point Mapping**: Clearly structured in GAD 1(2) tables. Each pier has 4-6+ corner points. The naming convention:
   - Main Carriageway: Piers A1, P1–P7 (LHS & RHS share the same pier IDs but have DIFFERENT point numbers and coordinates)
   - Loop-1: Piers 1P1–1P14, Points L01–L56
   - Loop-2: Piers 2P1–2P14, Points L57–L113
   - Loop-3: Piers 3P1–3P14, Points L114–L169
   - Loop-4: Piers 4P1–4P14, Points L170–L225

4. **Cross-PDF Overlap**: GAD 1(1) pg0 shows pier layout A1–P18+A2 (broader range than GAD 1(2)'s A1–P7). The coordinate tables in GAD 1(2) only cover A1 through P7 for the main carriageway — additional piers P8–P18, A2 are shown on the plan but their coordinates may be on pages 0-1 of GAD 1(2).

5. **P3 & P11 NOT USED**: Explicitly noted on GAD 1(1) pg0.

6. **Duplicate Tables**: pdfplumber sometimes detects the same table twice on a page (possibly due to overlapping drawing borders). Need deduplication.

7. **All PDFs have text layers** — no scanned/image-only pages. OCR is not needed for these files (but will be supported for user-uploaded files).

---

## 2. Architecture

### 2.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Web Frontend                       │
│  (HTML/CSS/JS – Upload, Results, Review, Export)     │
└────────────────────────┬─────────────────────────────┘
                         │ REST API (FastAPI)
┌────────────────────────┴─────────────────────────────┐
│                   Backend Server                      │
│  ┌─────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │ Ingest  │→│ Extract  │→│ Merge & Validate │    │
│  │ Module  │  │ Module   │  │    Module         │    │
│  └─────────┘  └──────────┘  └──────────┬───────┘    │
│                                         │            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┴──────┐    │
│  │   CRS    │  │  Compute │  │    Export       │    │
│  │ Handler  │  │  Module  │  │    Module       │    │
│  └──────────┘  └──────────┘  └─────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐     │
│  │         SQLite Database                      │     │
│  │  (pdfs, pages, tables, points, piers, logs) │     │
│  └─────────────────────────────────────────────┘     │
│                                                      │
│  ┌─────────────────────────────────────────────┐     │
│  │    Local AI & Civil Expert Synthesis Engine  │     │
│  │  • Ollama LLM integration (qwen2.5/llama3.2) │     │
│  │  • 100% Offline Civil Expert Brief Fallback  │     │
│  │  • 3D Modeling Brief & Assembly Logic        │     │
│  └─────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────┘
```

### 2.2 Folder Structure

```
e:\KC.IRL\LLM\
├── PLAN.md                        # This plan
├── README.md                      # Setup & usage guide
├── requirements.txt               # Python dependencies
├── setup.bat                      # One-time setup script
├── run.bat                        # Launch script
├── input/                         # PDF input folder (GAD 1(1) & GAD 1(2))
├── output/                        # Export folder (Flyover_3D_Master_Model.xlsx)
├── page_images/                   # Rendered 150 DPI page PNGs
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Configuration & paths
│   ├── database.py                # SQLite schema (piers, points, deck_sections, boreholes, insights)
│   ├── models.py                  # Pydantic 3D models
│   ├── routers/
│   │   ├── upload.py              # PDF upload endpoints
│   │   ├── pipeline.py            # Processing pipeline endpoints
│   │   ├── results.py             # 3D piers, deck sections, boreholes, AI insights
│   │   ├── crs.py                 # CRS management
│   │   └── export.py              # 7-sheet master 3D Excel export
│   ├── pipeline/
│   │   ├── ingest.py              # PDF ingestion & cached 150 DPI rendering
│   │   ├── extract_tables.py      # Footing coordinate schedules from GAD 1 (2)
│   │   ├── extract_text.py        # Notes & exclusions (P3/P11)
│   │   ├── extract_cad_sections.py# CAD sections 1-1, 2-2 & boreholes BH20-BH30
│   │   ├── ai_engine.py           # Local Ollama LLM & Civil Expert brief engine
│   │   ├── normalise.py           # ID normalisation
│   │   ├── compute.py             # 3D coordinates, skew angles, bounding envelopes
│   │   ├── validate.py            # Validation rules & bounds checks
│   │   ├── merge.py               # Cross-PDF merging & deduplication
│   │   └── orchestrator.py        # Pipeline runner (strictly GAD 1 & 2)
│   ├── export/
│   │   ├── excel_writer.py        # Master 7-sheet 3D BIM Excel workbook builder
│   │   └── csv_writer.py          # CSV export
│   └── static/                    # Frontend files
│       ├── index.html             # 3D Catalog, Footing Polygons, Sections, Strata, AI Brief
│       ├── css/styles.css         # Dark theme glassmorphism UI
│       └── js/app.js              # 3D data loading & interactive review
        ├── css/
│       │   └── styles.css
│       └── js/
│           ├── app.js
│           ├── upload.js
│           ├── results.js
│           ├── review.js
│           └── export.js
├── tests/
│   ├── __init__.py
│   ├── test_normalise.py
│   ├── test_compute.py
│   ├── test_crs.py
│   ├── test_merge.py
│   ├── test_validate.py
│   └── test_pipeline.py
└── page_images/                   # Rendered page images (generated)
```

---

## 3. Libraries & Dependencies

| Library | Purpose | Version |
|---------|---------|---------|
| `PyMuPDF` (pymupdf) | PDF text/image extraction, page rendering | ≥1.24 |
| `pdfplumber` | Table detection and extraction | ≥0.11 |
| `pyproj` | CRS conversion (UTM → WGS84) | ≥3.6 |
| `FastAPI` | Backend REST API | ≥0.104 |
| `uvicorn` | ASGI server | ≥0.29 |
| `openpyxl` | Excel workbook creation | ≥3.1 |
| `python-multipart` | File upload handling | ≥0.0.6 |
| `Pillow` | Image processing | ≥10.0 |
| `aiofiles` | Async file handling | ≥23.0 |
| `easyocr` | OCR for scanned pages (optional) | ≥1.7 |
| `pytest` | Testing | ≥7.0 |

### Optional (Ollama AI)
| Tool | Purpose |
|------|---------|
| `ollama` | Local LLM/VLM runtime |
| `qwen2.5:7b` | Text LLM for reasoning/matching |
| `llava:7b` or `moondream:1.8b` | VLM for drawing interpretation |

**Model Selection Rationale (RTX 3050 6GB, 16GB RAM)**:
- **Qwen2.5:7b** (Q4 quantised, ~4.5 GB VRAM): Good reasoning, fits in 6GB GPU
- **Moondream:1.8b** (VLM, ~1.5 GB): Very lightweight VLM, can run alongside text model
- Alternative: **LLaVA:7b** if only running one model at a time
- All AI is **enhancement only** — the deterministic pipeline (regex + table parsing) is the primary extraction method. AI cross-checks and handles ambiguous cases.

---

## 4. Extraction Pipeline

### Stage 1: Ingest
1. Accept PDF uploads (multiple files)
2. For each PDF:
   - Extract metadata (filename, page count, file hash)
   - Render each page to PNG (150 DPI) for display and AI analysis
   - Store in SQLite `pdfs` and `pages` tables

### Stage 2: Page Classification
For each page, classify as one or more of:
- `coordinate_table` — Contains pier corner point coordinate tables
- `plan_view` — Foundation layout plan drawing
- `profile` — Vertical profile / plan & profile sheet
- `bore_log` — Borehole/soil data
- `section_drawing` — Cross-section / pier section drawing
- `title_block` — Title/metadata only
- `unknown`

Classification method: keyword-based + table structure detection:
- If page has tables with headers containing "Easting", "Northing", "Point" → `coordinate_table`
- If text contains "LOOP-N COORDINATES" → `coordinate_table`
- If text contains "GENERAL ARRANGEMENT" or "PLAN" with pier labels → `plan_view`
- If text contains "PROFILE" and "DATUM" → `profile`
- If text contains "BH-" and "DEPTH" and "N VALUE" → `bore_log`
- If text contains "SECTION" with dimensional annotations → `section_drawing`

### Stage 3: Table Extraction
For `coordinate_table` pages:
1. Use pdfplumber to find all tables
2. Identify coordinate tables by header pattern: `[Sr. No.] | Point No. | Easting | Northing` or `PIER | POINTS | EASTING (X) | NORTHING (Y)`
3. Extract all rows, handling:
   - Multi-table pages (LHS + RHS on same page)
   - Section header rows ("LHS CARRIAGE WAY COORDINATES", "LOOP-1 COORDINATES")
   - Pier column that is blank for continuation rows (same pier, next point)
   - Truncated columns (some tables detected as 2-3 cols instead of 4 — Northing cut off)
4. Deduplicate identical tables detected twice on same page
5. Store raw extracted data in `raw_points` table

### Stage 4: Section/Carriageway Assignment
Based on table headers and page context:
- "LHS CARRIAGE WAY COORDINATES" on pg0-1 → `LHS Carriageway`
- "RHS CARRIAGE WAY COORDINATES" on pg0-1 → `RHS Carriageway`
- "LOOP-1 COORDINATES" on pg2 → `Loop-1`
- "LOOP-2 COORDINATES" on pg2 → `Loop-2`
- "LOOP-3 COORDINATES" on pg3 → `Loop-3`
- "LOOP-4 COORDINATES" on pg3 → `Loop-4`

### Stage 5: Text/Regex Extraction
For plan view pages, use regex to find:
- Pier labels and positions
- Span lengths (e.g., "30000")
- Annotations mentioning pier IDs
- CRS/datum mentions
- Notes about excluded piers (e.g., "PIER NUMBER P3 & P11 NOT USED")

### Stage 6: ID Normalisation
Normalise all extracted IDs:
- Strip whitespace: `"P 15"` → `"P15"`
- Remove dashes: `"P-15"` → `"P15"`
- Uppercase: `"p15"` → `"P15"`
- Loop pier format: `"1P1"` → `"1P1"` (keep loop prefix)
- Point IDs: `"L01"` → `"L01"`, `"P001"` → `"P01"` (normalise leading zeros)

### Stage 7: Cross-Page & Cross-PDF Merging
1. Group all raw points by normalised Point ID
2. For duplicate points (same ID from different tables/pages/PDFs):
   - If coordinates match (within tolerance of 0.01m): keep one, mark "Verified"
   - If coordinates differ: flag as "Review Required" with both values and sources
3. Build pier→points mapping by filling down the PIER column in tables
4. Assign each point to its pier and section

### Stage 8: Validation
- **Range check**: Easting ~385,000–387,000, Northing ~1,452,000–1,454,000 (expected range for this project)
- **Swap check**: If Easting > 1,000,000 or Northing < 100,000, likely swapped
- **Cluster check**: All points of one pier should be within ~50m of each other
- **Duplicate check**: Same Point ID should not have different coordinates
- **Sequence check**: Point numbering should be sequential within a pier
- **Missing pier check**: Flag if expected piers are missing (P3, P11 expected absent per notes)
- **CRS check**: If CRS not explicitly stated, mark all records "CRS Unverified"

### Stage 9: Compute
1. **Pier Centres**: For each pier, average all its corner points' Easting and Northing
2. **CRS Conversion**: Convert centre Easting/Northing to Latitude/Longitude using pyproj
   - Default assumption: UTM Zone 44N, WGS84 (EPSG:32644) — based on Chennai location
   - User can override in UI
3. **Inter-Pier Distance**: Straight-line distance between consecutive pier centres within same section
   - `dist = sqrt((E2-E1)² + (N2-N1)²)` in metres
   - First pier of each section: leave blank

### Stage 10: Export
Generate Excel workbook with 5 sheets (see Section 8).

---

## 5. CRS Strategy

### Detection
1. Search all PDF text for: "UTM", "WGS", "EPSG", "datum", "projection", "zone", "Indian"
2. Check title blocks, notes, and SCP data
3. **Finding from inspection**: No explicit CRS/EPSG found. The "DATUM = 36/38" in MCW P&P refers to vertical datum for profile plots (survey reduced level reference), NOT geodetic datum.

### Default Assumption
- Project location: Chennai Peripheral Ring Road, Tamil Nadu, India
- Coordinates: Easting ~385,000–387,000, Northing ~1,452,000–1,454,000
- This is consistent with **UTM Zone 44N, WGS84** (EPSG:32644)
  - Zone 44N covers 78°E–84°E; Chennai is at ~80.2°E ✓
  - Northing ~1,452,000 → latitude ~13.1°N ✓
- Alternative possibility: Indian projected coordinate system (Kalianpur datum / Everest ellipsoid), but UTM/WGS84 is standard for modern Indian highway projects under NHAI/state highway authorities

### Implementation
1. Mark all records as **"CRS Unverified"** by default
2. Show CRS selector in UI with:
   - Default suggestion: "UTM Zone 44N, WGS84 (EPSG:32644)" — clearly labelled as assumption
   - Option to select other CRS or enter custom EPSG code
3. Log CRS used, EPSG code, and source ("Assumed based on project location")
4. Re-convert all coordinates when CRS is changed

---

## 6. Pier Dimensions (Section Drawings)

### Current Status
**Section 1-1 through Section 5-5 drawings are NOT present in the 3 provided PDFs.** 

The Reference Drawings section on GAD 1(1) pg0 lists:
- Substructure drawings for interchange (MCW): O24087-C-RP-MB-NU-8360-8346
- Substructure drawings for interchange (LOOP): O24087-C-RP-MB-NU-8350-8385
- Superstructure drawings: O24087-C-RP-MB-NU-8360-8430

These separate drawing files would contain pier height, width, cap height, and cap width.

### Handling
1. Pier dimension columns (height, width, cap height, cap width) will be left **blank** with reason: "Section drawings not found in provided PDFs"
2. If user uploads additional PDFs containing section drawings, the AI vision module will attempt to read dimensional annotations
3. The system will support future integration when these drawings become available
4. From the plan view, we can extract span lengths (30000 mm = 30m between piers) which provides some dimensional context

---

## 7. AI Integration (Ollama)

### Role: Enhancement & Cross-Check (NOT Primary)

The AI layer is **optional** and serves as a secondary verification:

1. **VLM (Vision-Language Model) — Moondream/LLaVA**:
   - Read rendered page images to verify pier labels and positions
   - Interpret drawing annotations that regex may miss
   - Identify section drawings if present in user-uploaded PDFs
   - Extract dimensional annotations from cross-section views

2. **Text LLM (Qwen2.5 / Llama 3.1)**:
   - Reason about pier-to-point assignments when table structure is ambiguous
   - Help resolve conflicts between PDFs
   - Parse unstructured notes and annotations
   - Generate human-readable explanations for flagged items

3. **Confidence Scoring**:
   - Every AI-extracted value gets a confidence score (0.0–1.0)
   - If AI value matches deterministic extraction: confidence = 1.0
   - If AI value differs: flag for review with both values shown
   - If only AI extraction available: confidence = AI's own assessment, capped at 0.8

### Graceful Degradation
- If Ollama is not installed or models not downloaded: pipeline runs fully on deterministic extraction
- AI features show as "unavailable" in UI, not as errors
- Setup script downloads models but marks them as optional

---

## 8. Excel Workbook Layout

### Sheet 1: "Pier Centres"
| Column | Format | Notes |
|--------|--------|-------|
| Carriageway | Text | RHS/LHS/Loop-1/Loop-2/Loop-3/Loop-4 |
| Pier ID | Text | A1, P1, P2, 1P1, 2P1, etc. |
| Point Range | Text | P01-P04, L01-L04, etc. |
| Latitude | Number (8 dp) | Decimal degrees |
| Longitude | Number (8 dp) | Decimal degrees |
| Distance from Previous (m) | Number (3 dp) | Blank for first pier |
| Pier Height | Number / Blank | From section drawings |
| Pier Width | Number / Blank | From section drawings |
| Pier Cap Height | Number / Blank | From section drawings |
| Pier Cap Width | Number / Blank | From section drawings |
| Dimension Units | Text | mm / m |
| Centre Easting | Number (4 dp) | Computed average |
| Centre Northing | Number (4 dp) | Computed average |
| Source PDFs | Text | Comma-separated filenames |
| Source Pages | Text | Comma-separated page numbers |
| Status | Text | Verified / Review Required / CRS Unverified |
| Notes | Text | Any flags, reasons |

**Formatting**: Frozen header row, auto-filter, column widths auto-fit, Status column colour-coded (green=Verified, orange=Review, red=CRS Unverified).

### Sheet 2: "Corner Points"
| Column | Format |
|--------|--------|
| Point ID | Text |
| Pier ID | Text |
| Carriageway | Text |
| Easting (X) | Number (4 dp) |
| Northing (Y) | Number (2 dp) |
| Source PDF | Text |
| Source Page | Integer |
| Status | Text |
| Notes | Text |

### Sheet 3: "Section Summary"
| Column | Format |
|--------|--------|
| Carriageway/Loop | Text |
| Pier Count | Integer |
| First Pier | Text |
| Last Pier | Text |
| Total Length (m) | Number (2 dp) |
| Points Count | Integer |
| Verified Count | Integer |
| Review Required Count | Integer |

### Sheet 4: "Review Required"
| Column | Format |
|--------|--------|
| Item Type | Text (Pier/Point/CRS) |
| ID | Text |
| Issue | Text |
| Value A | Text |
| Source A | Text |
| Value B | Text |
| Source B | Text |
| Suggested Resolution | Text |
| Page Reference | Text |

### Sheet 5: "Processing Log"
| Column | Format |
|--------|--------|
| Timestamp | DateTime |
| Level | Text (INFO/WARN/ERROR) |
| Category | Text |
| Message | Text |
| File | Text |
| Page | Integer |

---

## 9. UI Screens

### 9.1 Upload Screen
- Drag-and-drop zone for multiple PDFs
- File list with size and status indicators
- "Process" button to start pipeline
- Option to load PDFs from workspace `input/` folder

### 9.2 Progress Screen
- Per-file progress bars
- Per-stage progress (Ingest → Extract → Merge → Validate → Compute)
- Live log stream
- Estimated time remaining

### 9.3 Results Table
- Interactive data table showing Pier Centres
- Column sorting and filtering
- Filter by: Carriageway, Status, Pier ID search
- Click pier ID to see details and corner points
- Colour-coded status badges

### 9.4 Review Screen
- List of flagged items (Review Required)
- Side-by-side: flagged record details + source PDF page image
- Editable fields for correction
- "Mark as Verified" / "Keep as Review Required" buttons
- Auto-recalculation on edit (centre, lat/long, distance)

### 9.5 CRS Panel
- Current CRS display with EPSG code
- CRS selector dropdown (common UTM zones for India)
- Custom EPSG input
- "Apply" button — triggers re-conversion of all coordinates
- Warning banner if CRS is unverified

### 9.6 Export Panel
- Download Excel workbook button
- Download CSV button
- Preview of what will be exported
- Options for which sheets to include

---

## 10. Test Plan

### Unit Tests
1. **ID Normalisation** (`test_normalise.py`):
   - `"P 15"` → `"P15"`, `"p-15"` → `"P15"`, `"P015"` → `"P15"`
   - `"1P1"` stays `"1P1"`, `"L01"` stays `"L01"`
   - Edge cases: empty, None, numeric-only

2. **Averaging** (`test_compute.py`):
   - Average of 4 corner points → correct centre
   - Single point → returns point itself
   - Empty list → None

3. **CRS Conversion** (`test_crs.py`):
   - Known UTM 44N point → expected lat/lon (within 0.0001°)
   - Round-trip: UTM → WGS84 → UTM matches original
   - Invalid EPSG code handling

4. **Distance Calculation** (`test_compute.py`):
   - Two known points → expected distance
   - Same point → 0.0
   - First pier → None (no previous)

5. **Range Formatting** (`test_compute.py`):
   - `[P01, P02, P03, P04]` → `"P01-P04"`
   - `[P01, P02, P05]` → `"P01-P02, P05"`
   - `[L57]` → `"L57"`

### Integration Tests
6. **Full Pipeline** (`test_pipeline.py`):
   - Process all 3 PDFs
   - Verify: correct number of piers per section
   - Verify: all expected points extracted
   - Verify: no invented data
   - Check for P3 and P11 being flagged/excluded
   - Verify cross-PDF merging handles duplicates

### Expected Results (from inspection)
| Section | Expected Piers | Expected Points |
|---------|---------------|-----------------|
| LHS Carriageway | A1, P1, P2, P4–P7 | P01–P66 (split across 2 pages) |
| RHS Carriageway | A1, P1, P2, P4–P7 | P133–P198 |
| Loop-1 | 1P1–1P14 | L01–L56 |
| Loop-2 | 2P1–2P14 | L57–L113 |
| Loop-3 | 3P1–3P14 | L114–L169 |
| Loop-4 | 4P1–4P14 | L170–L225 |

Note: P3 and P11 NOT USED (per GAD 1(1) notes).

---

## 11. Implementation Milestones

### Milestone 1: Core Infrastructure
- [x] PDF inspection (completed)
- [ ] Project folder structure
- [ ] SQLite database schema
- [ ] FastAPI app skeleton
- [ ] Configuration module
- **Test**: Server starts, database creates

### Milestone 2: Extraction Pipeline
- [ ] PDF ingestion module
- [ ] Page classification
- [ ] Table extraction (pdfplumber)
- [ ] Text/regex extraction
- [ ] ID normalisation
- **Test**: Run on 3 PDFs, verify raw extraction counts

### Milestone 3: Merge & Validate
- [ ] Cross-page merging
- [ ] Cross-PDF merging
- [ ] Duplicate detection
- [ ] Conflict flagging
- [ ] Validation rules
- **Test**: Merge results, verify duplicate handling

### Milestone 4: Compute & CRS
- [ ] Pier centre calculation
- [ ] CRS detection & conversion
- [ ] Inter-pier distance calculation
- [ ] Point range formatting
- **Test**: Unit tests for all compute functions

### Milestone 5: Excel/CSV Export
- [ ] Excel workbook builder (5 sheets)
- [ ] CSV export
- [ ] Professional formatting
- **Test**: Generate workbook, verify format

### Milestone 6: Web Frontend
- [ ] Upload page
- [ ] Progress tracking
- [ ] Results table with filters
- [ ] Review page with PDF viewer
- [ ] CRS selector
- [ ] Export buttons
- **Test**: End-to-end flow in browser

### Milestone 7: AI Enhancement (Optional)
- [ ] Ollama integration
- [ ] VLM drawing analysis
- [ ] LLM reasoning
- [ ] Confidence scoring
- **Test**: AI results vs deterministic results

### Milestone 8: Polish & Documentation
- [ ] setup.bat and run.bat
- [ ] README.md
- [ ] Error handling & edge cases
- [ ] Final test run with sample output
- **Test**: Fresh install test, full pipeline

---

## 12. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Section drawings not in provided PDFs | Pier dimensions will be blank | Document clearly; support future upload; leave columns present but empty |
| CRS not explicitly stated | Coordinates may be wrong | Default assumption with clear warning; user CRS selector; validate against known Chennai location |
| pdfplumber table detection duplicates | Over-counting data | Deduplication by content hash; cross-check with pymupdf text extraction |
| Truncated table columns (Northing cut off) | Missing coordinates | Use multiple extraction methods; merge partial tables from overlapping detections |
| Loop pier naming (1P1 vs P1) | Confusion between main carriageway and loop piers | Strict section-aware ID namespacing |
| Large PDFs from user upload | Memory/performance issues | Stream processing; page-by-page extraction; progress reporting |
| Ollama not installed | AI features unavailable | Graceful degradation; all core extraction is deterministic |
| GPU VRAM limited (6GB) | Can't run large AI models | Selected small models (Moondream 1.8B, Qwen 7B Q4); fallback to CPU |

---

## 13. Open Questions for User

1. **Pier ID convention for Loops**: The tables show `1P1`, `2P1`, `3P1`, `4P1` as pier IDs for loops. Should these be displayed as-is, or reformatted (e.g., "Loop1-P1")?

2. **MCW P&P data**: The Plan & Profile sheets have Survey Control Points with coordinates. Should these be included in the output, or are they only relevant for CRS verification?

3. **Additional PDFs**: The reference drawings mention substructure and superstructure drawings (O24087-C-RP-MB-NU-8360 etc.) which would contain pier dimensions. Do you have these files, or should I proceed with dimensions left blank?

4. **Main carriageway pier range**: GAD 1(1) shows piers up to P18 + A2, but GAD 1(2) coordinate tables only seem to cover A1 through ~P7. Should I flag missing piers (P8–P18, A2) as "coordinates not found"?

---

**Status: AWAITING APPROVAL — Please review this plan and confirm before I begin coding.**
