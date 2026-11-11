from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CornerPointModel(BaseModel):
    id: Optional[int] = None
    point_id: str
    pier_id: str
    carriageway: str
    easting: float
    northing: float
    source_pdf: str
    source_page: int
    status: str = "Verified"
    notes: Optional[str] = None

class PierModel(BaseModel):
    id: Optional[int] = None
    carriageway: str
    pier_id: str
    point_range: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_from_previous: Optional[float] = None
    pier_height: Optional[float] = None
    pier_width: Optional[float] = None
    pier_cap_height: Optional[float] = None
    pier_cap_width: Optional[float] = None
    pier_cap_center_depth: Optional[float] = None
    pier_cap_tip_depth: Optional[float] = None
    pier_cap_cantilever: Optional[float] = None
    pier_shaft_width: Optional[float] = None
    pier_shaft_thickness: Optional[float] = None
    pedestal_height: Optional[float] = None
    bearing_offset: Optional[float] = None
    skew_angle_deg: Optional[float] = None
    footing_length: Optional[float] = None
    footing_width: Optional[float] = None
    span_length: Optional[float] = None
    dimension_units: str = "mm"
    centre_easting: Optional[float] = None
    centre_northing: Optional[float] = None
    source_pdfs: Optional[str] = None
    source_pages: Optional[str] = None
    status: str = "Verified"
    notes: Optional[str] = None
    sequence_order: Optional[int] = None

class DeckSectionModel(BaseModel):
    id: Optional[int] = None
    section_name: str
    description: Optional[str] = None
    carriageway_deck_width: Optional[float] = None
    roadway_width: Optional[float] = None
    median_gap: Optional[float] = None
    deck_slab_thk: Optional[float] = None
    wearing_coat_thk: Optional[float] = None
    cross_slope_pct: Optional[float] = None
    crash_barrier_width: Optional[float] = None
    curb_height: Optional[float] = None
    girder_type: Optional[str] = None
    girder_depth: Optional[float] = None
    concrete_grade: Optional[str] = None
    scale: Optional[str] = None

class BoreholeLogModel(BaseModel):
    id: Optional[int] = None
    borehole_id: str
    sheet_number: Optional[str] = None
    chainage: Optional[str] = None
    depth_from: float
    depth_to: float
    strata_description: str
    spt_n_value: Optional[str] = None
    water_table_m: Optional[float] = None
    foundation_depth_df: Optional[float] = None
    source_pdf: Optional[str] = None
    source_page: Optional[int] = None

class ExecutiveInsightModel(BaseModel):
    id: Optional[int] = None
    category: str
    title: str
    content: str
    generated_by: str

class CRSUpdateRequest(BaseModel):
    epsg_code: int
    name: Optional[str] = None
    is_verified: bool = True

class PointUpdateRequest(BaseModel):
    point_id: str
    pier_id: Optional[str] = None
    carriageway: Optional[str] = None
    easting: Optional[float] = None
    northing: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class PierUpdateRequest(BaseModel):
    pier_id: str
    carriageway: str
    pier_height: Optional[float] = None
    pier_width: Optional[float] = None
    pier_cap_height: Optional[float] = None
    pier_cap_width: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class ProcessingStatusResponse(BaseModel):
    status: str
    message: str
    current_stage: str
    progress_percent: int
    total_files: int
    processed_files: int

class AIQueryRequest(BaseModel):
    query: str
