import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
PAGE_IMAGES_DIR = BASE_DIR / "page_images"
DB_PATH = BASE_DIR / "flyover_data.db"

# Ensure runtime directories exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PAGE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# CRS Defaults
DEFAULT_EPSG = 32644  # WGS 84 / UTM Zone 44N (Chennai/Tamil Nadu region)
DEFAULT_CRS_NAME = "WGS 84 / UTM zone 44N"

# Plausible bounds for Easting/Northing in Zone 44N around project location
VALID_EASTING_MIN = 300000.0
VALID_EASTING_MAX = 500000.0
VALID_NORTHING_MIN = 1300000.0
VALID_NORTHING_MAX = 1600000.0

# Supported carriageways
CARRIAGEWAYS = [
    "RHS Carriageway",
    "LHS Carriageway",
    "Loop-1",
    "Loop-2",
    "Loop-3",
    "Loop-4",
]
