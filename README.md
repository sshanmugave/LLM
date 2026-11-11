# Flyover 3D Studio — Autonomous CAD/BIM Infrastructure AI

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Offline AI](https://img.shields.io/badge/AI-100%25%20Offline%20Ready-orange.svg)]()
[![CRS](https://img.shields.io/badge/CRS-EPSG%3A32644%20(UTM%2044N)-purple.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%2011%20%2F%2010-lightgrey.svg)]()

**Flyover 3D Studio** is an offline, enterprise-grade Document AI and spatial geometry reconstruction platform designed for civil, structural, and highway infrastructure projects.

It converts complex 2D multi-sheet engineering drawings (General Arrangement Drawings `GAD` and Plan & Profile `P&P` sheets) into millimeter-accurate, 3D-ready CAD/BIM parametric datasets, complete with centroid coordinates, skew azimuth angles, footing extrusion polygons, cross-section profiles, and subsurface geotechnical strata logs.

---

## 📑 Table of Contents

- [Key Capabilities](#-key-capabilities)
- [System Architecture](#-system-architecture)
- [Prerequisites](#-prerequisites)
- [Quick Start Guide](#-quick-start-guide)
- [Web Interface & Navigation](#-web-interface--navigation)
- [Master Deliverables](#-master-deliverables)
- [Document Integrity & Validation (LLM-DOD-02)](#-document-integrity--validation-llm-dod-02)
- [Engineering Document Governance (LLM-DOD-03 to 06)](#-engineering-document-governance-llm-dod-03-to-06)
  - [LLM-DOD-03: Document Classification](#llm-dod-03-engineering-document-classification)
  - [LLM-DOD-04: Multi-Page & Sheet Processing](#llm-dod-04-multi-page-and-drawing-sheet-processing)
  - [LLM-DOD-05: Revision & Metadata Tracking](#llm-dod-05-drawing-revision-and-metadata-identification)
  - [LLM-DOD-06: Document Relationship Management](#llm-dod-06-engineering-document-relationship-management)
- [REST API Reference](#-rest-api-reference)
- [Automated Testing](#-automated-testing)
- [Project Directory Structure](#-project-directory-structure)
- [License](#-license)

---

## 🌟 Key Capabilities

1. **100% Offline Operation & Zero Cloud Leaks**:
   - Engineered for secure defense, public-works, and critical infrastructure environments.
   - Zero cloud API dependency. Runs entirely on local compute using deterministic vector table extraction, PyMuPDF (`fitz`), local OCR (`rapidocr-onnxruntime`), `pyproj` geodetic transforms, and local Ollama (`qwen2.5` / `llama3.2`) with built-in Civil Expert rule engines.

2. **2D-to-3D Parametric BIM Extraction**:
   - Extracts coordinates for **RHS**, **LHS**, and **Loops 1 to 4** carriageways.
   - Computes millimeter-exact pier centroids, span chainages, clear spans, and **Pier Skew Angles (Azimuth rotation)**.
   - Reconstructs structural cross-sections from CAD vector text:
     - **Pier Cap**: $13,600\,\text{mm}$ width, $2,500\,\text{mm}$ center depth, $1,500\,\text{mm}$ tip depth, $3,000\,\text{mm}$ cantilever overhang.
     - **Pier Shaft**: $5,000\,\text{mm}$ width $\times$ $2,500\,\text{mm}$ thickness ($750 + 1000 + 750\,\text{mm}$ curved web).
     - **Deck Superstructure**: $15,050\,\text{mm}$ standard / $18,550\,\text{mm}$ widened merge width, $300\,\text{mm}$ slab, $54\,\text{mm}$ wearing coat, $525\,\text{mm}$ crash barriers, $2.50\%$ and $2.42\%$ cross-fall slopes.
     - **Pedestals & Bearings**: $600 \times 600 \times 900\,\text{mm}$ pedestals with elastomeric bearings spaced $750\,\text{mm}$ from pier centerline.
     - **Spans**: $30,000\,\text{mm}$ Main Carriageway ($28,500\,\text{mm}$ clear) and $20,000\,\text{mm}$ Loops ($18,700\,\text{mm}$ clear).

3. **Footing Extrusion Polygon Vertices**:
   - Reconstructs 483 distinct 3D corner vertices ordered clockwise for direct solid CAD/BIM polygon extrusion in AutoCAD, Civil 3D, Revit, or Bentley OpenBridge.

4. **Subsurface Geotechnical Strata Modeling**:
   - Extracts complete soil stratification logs for Boreholes **BH-20 to BH-30** from GAD sheets, including depth intervals, lithological descriptions, SPT 'N' values, groundwater table, and design foundation embedment depth ($D_f = 2.50\,\text{m}$).

5. **Strict Geodetic CRS Coordinate Strategy**:
   - Maps UTM Zone 44N (`EPSG:32644`) Easting/Northing coordinates to high-precision WGS84 Latitude and Longitude (8 decimal places) with coordinate plausibility checks.

6. **Conversational Drawing AI Assistant**:
   - Interactive structural Q&A terminal powered by offline semantic reasoning.
   - Answers technical queries regarding dimensions, cap geometry, camber slopes, bearing offsets, borehole strata, concrete grades, and drawing exclusion rules (such as excluded piers `P3` and `P11`).

---

## 🏛️ System Architecture

```text
  ┌────────────────────────────────────────────────────────────────────────┐
  │                           INPUT DOCUMENTS                              │
  │     CAD Vector PDFs (GAD & P&P)   ·   Excel Workbooks   ·   JSON       │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │             1. DOCUMENT INTEGRITY & VALIDATION (LLM-DOD-02)            │
  │    Format Check · Corruption Detection · Password/Encryption Check     │
  │                     Audit Logging (SQLite WAL)                         │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │ [Valid Files]
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                 2. EXTRACTION & PARSING PIPELINE                       │
  │  PyMuPDF Vector Table Parser · Coordinate Extraction · Notes & SCPs    │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │              3. GEOMETRY, CRS & NORMALIZATION ENGINE                   │
  │   ID Normalization · Carriageway Splitting · Centroid Calculation      │
  │    Skew Azimuth Angles · pyproj Geodetic Transform (UTM to WGS84)      │
  │            Cross-PDF Merging & Conflict Deduplication                  │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
         ┌────────────────────────────┴───────────────────────────┐
         ▼                                                        ▼
┌─────────────────────────────────┐           ┌───────────────────────────────────┐
│     4. MASTER DELIVERABLES      │           │     5. MODERN WEB WORKSTATION     │
│ 7-Sheet 3D Model Workbook .xlsx │           │ Top Navigation Tabs · Telemetry   │
│ Pier Centroids & Points CSVs    │           │ QC Sheet Review · 3D Pier Modal   │
│ AutoCAD 3D Extrusion Scripts    │           │ Offline Conversational AI         │
└─────────────────────────────────┘           └───────────────────────────────────┘
```

---

## 💻 Prerequisites

- **Operating System**: Windows 11 / Windows 10 (64-bit)
- **Python**: Python 3.11+ installed and added to PATH
- **Git**: Git 2.30+ installed
- **Hardware**: 4 GB RAM minimum (8 GB+ recommended), 500 MB free disk space

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/sshanmugave/LLM.git
cd LLM
```

### 2. Automated One-Click Setup
Run the setup script from PowerShell or Command Prompt:
```cmd
setup.bat
```
This automated script will:
- Validate Python 3.11+
- Install dependencies from `requirements.txt`
- Initialize the local SQLite database schema
- Run the full unit and regression test suite

*Or install manually using pip:*
```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Launch the Application
Run the launch script:
```cmd
run.bat
```
*Or launch manually via Uvicorn:*
```bash
py -3.11 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The application server will start immediately at:
🌐 **Web Interface**: [http://127.0.0.1:8000](http://127.0.0.1:8000)  
📚 **Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
🔍 **Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 🖥️ Web Interface & Navigation

The frontend is a self-contained, enterprise dark-themed workstation. It features **11 high-visibility Top Navigation Tabs** and a synchronized left sidebar for instant access to every engineering domain:

| Tab | Purpose | Key Actions |
|---|---|---|
| **📂 Documents & Ingestion** | Upload engineering drawings, workbooks, or JSON coordinates. | Drag & drop upload, workspace folder scanner, LLM-DOD-02 validation audit logs modal, document preview & delete. |
| **⚡ Run Pipeline** | Autonomous extraction console. | Trigger full extraction, view real-time stage progress, live color-coded execution terminal, extraction summary metrics. |
| **🏗️ 3D Pier Master** | Master structural catalog of all extracted piers. | Search by pier ID/chainage, carriageway filter, skew azimuth viewing, detailed 3D dimension modal inspector. |
| **📐 Footing Vertices** | Footing polygon corner coordinates. | 483 ordered 3D vertices table for solid CAD polygon extrusion. |
| **🏛️ CAD Cross-Sections** | Superstructure deck geometry. | Section 1-1 & Section 2-2 widths, camber slopes, girder typologies, crash barriers, and pedestals. |
| **🌍 Geotechnical Strata** | Subsurface borehole logging. | Boreholes BH-20 to BH-30 soil layers, SPT N-values, groundwater table, and foundation embedment depth ($D_f$). |
| **🔍 Drawing Review & QC** | High-resolution drawing inspector. | Multi-sheet switcher, full-resolution pan/zoom CAD canvas with bounding box overlays. |
| **🤖 Engineering AI** | Offline drawing intelligence terminal. | Interactive queries, structural rule validation, pre-canned prompt suggestions, and conversion briefs. |
| **💾 Export Deliverables** | Production-ready export center. | One-click downloads for 7-sheet Master Excel workbook, AutoCAD 3D extrusion scripts, CSV coordinate tables, and GeoJSON. |
| **🌐 Geodetic CRS** | Coordinate Reference System settings. | Active EPSG:32644 (UTM Zone 44N) transformation verification and projection parameters. |
| **📜 Run Archives** | Historical extraction archives. | Snapshot logs of previous pipeline runs with one-click restore and inspection. |

---

## 📊 Master Deliverables

Running the pipeline generates a suite of deliverables in the `output/` directory:

1. **`Flyover_3D_Master_Model.xlsx`** (Executive 7-Sheet BIM Workbook):
   - `3D_Pier_Master_Catalog`: Spatial insertion coordinates, skew angles, spans, footing dimensions, pier cap and shaft parameters.
   - `3D_Footing_Polygons`: 483 ordered footing corner vertices for solid CAD extrusion.
   - `Superstructure_3D_Deck`: Section 1-1 and Section 2-2 widths, slopes, and slab parameters.
   - `Span_&_Longitudinal_Profile`: Span sequence, clear spans, bearing seats, and expansion joints.
   - `Geotechnical_Subsurface_3D`: BH-20 to BH-30 soil layers, SPT N-values, and embedment depth ($D_f = 2.50\,\text{m}$).
   - `Materials_&_Engineering_Specs`: Concrete grades (M15–M55), Fe500D rebar, and drawing register.
   - `Executive_Summary_&_Insights`: 8 AI & Civil Engineering technical conversion guidelines.

2. **AutoCAD & GIS Formats**:
   - `Flyover_Pier_Centres.csv`: Pier ID, carriageway, easting, northing, elevation, latitude, longitude, skew azimuth.
   - `Flyover_Corner_Points.csv`: Footing vertex coordinates, point IDs, and sequence.

---

## 🛡️ Document Integrity & Validation (LLM-DOD-02)

The system enforces automated pre-processing validation on all uploaded files:

- **US-LLM-005 (Unopenable/Unreadable Files)**: Validates header magic bytes, PyMuPDF parsing integrity, and file size (>0 bytes).
- **US-LLM-006 (Corrupted Files)**: Catches damaged xref tables, truncated PDF containers, or malformed Excel zip files, flags them as `FAILED`, and presents descriptive error messages.
- **US-LLM-007 (Password Protection & Encryption)**: Detects encrypted/password-locked PDFs (`doc.is_encrypted`, `doc.needs_pass`) and encrypted Excel OLE compound packages, blocking unverified ingestion.
- **US-LLM-008 (Unsupported Formats)**: Rejects unsupported extensions (only `.pdf`, `.xlsx`, `.xls`, `.json` allowed) with explicit format guidance.
- **Audit Logging**: Every validation event is permanently recorded in SQLite `processing_logs` with `category='VALIDATION'` and accessible via the **📋 Validation Logs** button in the web UI.

---

## 📐 Engineering Document Governance (LLM-DOD-03 to 06)

### LLM-DOD-03: Engineering Document Classification
Automatically identifies and categorizes civil engineering documents to route each file into its optimal extraction pipeline:
- **US-LLM-009 (GAD Identification)**: Recognizes General Arrangement Drawings (GAD) containing elevation views, span arrangements, and bridge general layout plans.
- **US-LLM-010 (MCW Plan & Profile)**: Identifies Main Carriageway alignment, profile curves, chainages (e.g. `CH: 54+281`), VIP/HIP tangent points, and finished road levels.
- **US-LLM-011 (Foundation Layout & Structural Drawings)**: Distinguishes footing coordinate schedules, pile group layouts, pier shaft geometry, pier cap details, and reinforcement sections.
- **US-LLM-012 (Cross-Sections & Uncertainty Flagging)**: Identifies cross-sections (camber slopes, deck slabs, wearing course) and flags ambiguous/unrecognized drawings with status `UNCERTAIN` for engineer sign-off.
- **Official Deliverable**: **Classification test report** (`GET /api/governance/classification-report`), viewable in the Web UI via the **🏷️ Classification** button.

### LLM-DOD-04: Multi-Page and Drawing Sheet Processing
Ensures no drawings, tables, or sheets are omitted or silently skipped:
- **US-LLM-013 (Every Page Tracked)**: Logs page-by-page processing status (`SUCCESS`, `FAILED`, `SKIPPED`, `NEEDS_REVIEW`) across all multi-page PDFs.
- **US-LLM-014 (Engineering Table Identification)**: Identifies coordinate schedules, borehole logs, chainage/level tables, and dimension schedules.
- **US-LLM-015 (Multi-Sheet Drawing Sets)**: Extracts sheet numbers (`Sheet 01 of 10`), sheet titles, and contributes data across the complete set.
- **US-LLM-016 (Failure & Skip Reporting)**: Explicitly surfaces failed or omitted pages with actionable diagnostic reasons.
- **Official Deliverable**: **Page-level processing report** (`GET /api/governance/page-processing-report`), viewable in the Web UI via the **📑 Sheet Process** button.

### LLM-DOD-05: Drawing Revision and Metadata Identification
Extracts title block metadata to prevent version collisions and track engineering revisions:
- **US-LLM-017 (Drawing Number & Title Extraction)**: Extracts official drawing numbers (e.g. `O24087-C-RP-MB-GA-8330`), titles, scales, and client information.
- **US-LLM-018 (Strict Revision Extraction Without Inference)**: Revision codes (e.g. `RC`, `REV.C`, `R1.0`) are captured strictly from drawing title blocks; when absent, revision is recorded as `None` and never silently guessed or assumed.
- **US-LLM-019 (Drawing Dates Linked to Source)**: Captures recorded revision/plot dates with explicit sheet and file references.
- **US-LLM-020 (Superseding Version Distinction)**: Distinguishes drawing revisions to alert engineers of updated revisions.
- **Official Deliverable**: **Drawing metadata comparison** (`GET /api/governance/metadata-comparison`), viewable in the Web UI via the **🔍 Revisions** button.

### LLM-DOD-06: Engineering Document Relationship Management
Discovers, maps, and validates multi-file relationships across the project repository:
- **US-LLM-021 (Drawing Cross-References)**: Discovers explicit drawing cross-references (`THIS DRAWING SHALL BE READ IN CONJUNCTION WITH DRAWING NO. ...`).
- **US-LLM-022 (Structure ID Grouping)**: Groups drawings by civil structure asset ID (e.g. `FLYOVER-INTERCHANGE-CH54+281`).
- **US-LLM-023 (Common Element Linking & Ambiguity Flagging)**: Links shared structural entities (piers, footings, boreholes, sections); flags excluded elements (such as omitted piers `P3` and `P11`) as `is_ambiguous = True` for engineering review.
- **US-LLM-024 (Element Provenance & Traceability)**: Full backwards provenance tracing for any structural element back to its exact source drawings, sheets, and coordinates.
- **Official Deliverable**: **Document relationship records** (`GET /api/governance/relationship-records`) and **Trace Provenance** (`GET /api/governance/trace/{element_id}`), accessible via the **🔗 Relationships** and **🔗 Trace** buttons in the web UI.

---

## 🔌 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload/files` | Upload and validate engineering files. |
| `POST` | `/api/upload/load-existing` | Scan workspace `input/` folder and register valid files. |
| `GET` | `/api/upload/list` | List all registered documents with integrity and category badges. |
| `GET` | `/api/upload/validation-logs` | Fetch file validation audit trail (LLM-DOD-02). |
| `GET` | `/api/upload/validation-summary` | Summary metrics of file validation status. |
| `GET` | `/api/governance/classification-report` | Classification test report (LLM-DOD-03). |
| `GET` | `/api/governance/page-processing-report` | Page-level processing report (LLM-DOD-04). |
| `GET` | `/api/governance/metadata-comparison` | Drawing metadata comparison report (LLM-DOD-05). |
| `GET` | `/api/governance/relationship-records` | Document relationship records report (LLM-DOD-06). |
| `GET` | `/api/governance/trace/{element_id}` | Trace element origin provenance back to source sheets. |
| `POST` | `/api/governance/run-all` | Run all classification, sheet processing, metadata & relationship stages. |
| `POST` | `/api/pipeline/run` | Launch full autonomous extraction pipeline in background. |
| `GET` | `/api/pipeline/status` | Real-time status, progress percentage, and log messages. |
| `GET` | `/api/results/piers` | Retrieve master pier list with 3D coordinates and dimensions. |
| `GET` | `/api/results/points` | Retrieve footing polygon corner vertices. |
| `GET` | `/api/results/deck` | Retrieve superstructure deck cross-sections (1-1 & 2-2). |
| `GET` | `/api/results/geotechnical` | Retrieve borehole strata logs (BH-20 to BH-30). |
| `GET` | `/api/results/stats` | Global extraction telemetry and QA flag counts. |
| `POST` | `/api/ai/query` | Submit natural-language civil engineering queries. |
| `GET` | `/api/export/excel` | Download `Flyover_3D_Master_Model.xlsx`. |
| `GET` | `/api/export/csv/piers` | Download pier centers CSV. |
| `GET` | `/api/export/csv/points` | Download footing vertices CSV. |
| `GET` | `/api/crs/current` | View active Coordinate Reference System (`EPSG:32644`). |
| `POST` | `/api/crs/set` | Configure custom target CRS. |

---

## 🧪 Automated Testing

The platform includes a test suite covering database operations, geodetic transformations, spatial arithmetic, structural AI rules, normalisation, deduplication, document integrity validation, document classification, multi-page sheet tracking, metadata revision comparison, and document relationship management:

Run the full test suite:
```bash
py -3.11 -m pytest -v
```

Run specific Definition of Done suites:
```bash
# LLM-DOD-02: Document Integrity and Format Validation
py -3.11 -m pytest tests/test_document_validation.py -v

# LLM-DOD-03: Engineering Document Classification
py -3.11 -m pytest tests/test_document_classification.py -v

# LLM-DOD-04: Multi-Page and Drawing Sheet Processing
py -3.11 -m pytest tests/test_multi_page_processing.py -v

# LLM-DOD-05: Drawing Revision and Metadata Identification
py -3.11 -m pytest tests/test_metadata_revisions.py -v

# LLM-DOD-06: Engineering Document Relationship Management
py -3.11 -m pytest tests/test_relationship_management.py -v
```

**All 49 automated tests execute with 100% pass rate** across all DoD criteria.

---

## 📂 Project Directory Structure

```text
E:\KC.IRL\LLM\
├── app/
│   ├── config.py                     # Paths, coordinate bounds, CRS definitions
│   ├── database.py                   # SQLite schema, WAL mode, migrations, logging
│   ├── models.py                     # Pydantic schema validation models
│   ├── main.py                       # FastAPI application, static mounts, CORS
│   ├── pipeline/
│   │   ├── file_validator.py         # Document integrity & encryption engine (LLM-DOD-02)
│   │   ├── document_classifier.py    # Document & sheet classifier (LLM-DOD-03)
│   │   ├── sheet_processor.py        # Multi-page & table tracking engine (LLM-DOD-04)
│   │   ├── metadata_extractor.py     # Drawing number, revision, date extractor (LLM-DOD-05)
│   │   ├── relationship_manager.py   # Cross-drawing reference & link manager (LLM-DOD-06)
│   │   ├── ingest.py                 # PDF rendering and page classification
│   │   ├── extract_tables.py         # PDF vector coordinate table extractor
│   │   ├── extract_text.py           # Drawing notes, excluded piers (P3 & P11), SCPs
│   │   ├── normalise.py              # Standardisation of IDs, carriageways, and sections
│   │   ├── crs_handler.py            # pyproj UTM 44N to Lat/Lon transformations
│   │   ├── compute.py                # Centroid arithmetic, distances, skew azimuths
│   │   ├── validate.py               # Plausible coordinate checks & cluster bounds
│   │   ├── merge.py                  # Cross-PDF duplicate and conflict resolution
│   │   └── orchestrator.py           # Full extraction pipeline runner
│   ├── export/
│   │   ├── excel_writer.py           # 7-sheet openpyxl master BIM workbook builder
│   │   └── csv_writer.py             # CSV exporter for CAD/GIS interoperability
│   ├── routers/
│   │   ├── upload.py                 # File upload, scanner, and validation endpoints
│   │   ├── governance.py             # Governance reports (DOD-03..06) & provenance trace
│   │   ├── pipeline.py               # Pipeline triggers, progress polling, session resets
│   │   ├── results.py                # Data catalog endpoints (piers, points, deck, geo)
│   │   ├── export.py                 # File download endpoints
│   │   └── crs.py                    # Geodetic CRS configuration endpoints
│   └── static/                       # Production Web UI
│       ├── index.html                # Single-page interface with inlined production CSS
│       ├── css/styles.css            # Precision Slate & Cobalt Navy design system
│       └── js/app.js                 # Client controller, top-tab sync, audit & report modals
├── input/                            # Input directory for drawings and datasets
├── output/                           # Output deliverables (.xlsx, .csv)
├── page_images/                      # Rendered 150 DPI page PNGs
├── tests/                            # Automated Pytest suite (49 tests)
│   ├── test_infra.py
│   ├── test_crs.py
│   ├── test_compute.py
│   ├── test_ai_engine.py
│   ├── test_normalise.py
│   ├── test_validate.py
│   ├── test_merge.py
│   ├── test_document_validation.py    # LLM-DOD-02 test suite (7 tests)
│   ├── test_document_classification.py# LLM-DOD-03 test suite (5 tests)
│   ├── test_multi_page_processing.py  # LLM-DOD-04 test suite (5 tests)
│   ├── test_metadata_revisions.py     # LLM-DOD-05 test suite (5 tests)
│   └── test_relationship_management.py# LLM-DOD-06 test suite (5 tests)
├── .gitignore                        # Git ignore specifications
├── PLAN.md                           # Comprehensive technical specification & roadmap
├── requirements.txt                  # Production Python dependencies
├── setup.bat                         # Windows automated setup script
└── run.bat                           # Windows server launch script
```
├── .gitignore                    # Git ignore specifications
├── PLAN.md                       # Comprehensive technical specification & roadmap
├── requirements.txt              # Production Python dependencies
├── setup.bat                     # Windows automated setup script
└── run.bat                       # Windows server launch script
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
