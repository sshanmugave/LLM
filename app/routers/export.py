from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from app.export.excel_writer import create_excel_export
from app.export.csv_writer import create_csv_export

router = APIRouter()

@router.get("/excel")
def download_excel():
    """Generates and serves the master 7-sheet 3D BIM/CAD modeling Excel workbook."""
    try:
        path = create_excel_export()
        return FileResponse(
            path=str(path),
            filename=path.name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Excel workbook: {str(e)}")

@router.get("/csv")
def download_csv(table_type: str = Query("piers", pattern="^(piers|corner_points)$")):
    """Generates and serves CSV export of piers or corner points."""
    try:
        path = create_csv_export(table_type=table_type)
        return FileResponse(
            path=str(path),
            filename=path.name,
            media_type="text/csv"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV: {str(e)}")
