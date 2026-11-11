import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import BASE_DIR, PAGE_IMAGES_DIR, INPUT_DIR
from app.database import init_db, clear_extracted_data
from app.routers import upload, pipeline, results, export, crs

app = FastAPI(
    title="Flyover Pier Coordinate Extractor",
    description="Offline Document AI System for extracting pier coordinates and dimensions",
    version="1.0.0"
)

# CORS middleware for local frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folders
static_path = BASE_DIR / "app" / "static"
static_path.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

if PAGE_IMAGES_DIR.exists():
    app.mount("/page_images", StaticFiles(directory=str(PAGE_IMAGES_DIR)), name="page_images")

# Mount input directory so uploaded files can be previewed in browser
if INPUT_DIR.exists():
    app.mount("/input-files", StaticFiles(directory=str(INPUT_DIR)), name="input_files")

# Include Routers
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["Pipeline"])
app.include_router(results.router, prefix="/api/results", tags=["Results"])
app.include_router(crs.router, prefix="/api/crs", tags=["CRS"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])

@app.on_event("startup")
def on_startup():
    init_db()
    clear_extracted_data()   # Fresh session — wipe pipeline results on every server start

@app.get("/")
def read_root():
    index_file = static_path / "index.html"
    if index_file.exists():
        resp = FileResponse(str(index_file))
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp
    return HTMLResponse("<h1>Flyover Pier Coordinate Extractor API is Running</h1>")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "Flyover Pier Coordinate Extractor"}
