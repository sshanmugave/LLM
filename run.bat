@echo off
echo ============================================================
echo   Starting Flyover Pier Coordinate Extractor Web Server
echo ============================================================
echo Application running at: http://127.0.0.1:8000
echo Press Ctrl+C in this window to stop the server.
echo.

start http://127.0.0.1:8000
py -3.11 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
