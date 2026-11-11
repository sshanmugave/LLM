@echo off
echo ============================================================
echo   Flyover Pier Coordinate Extractor - Windows 11 Setup
echo ============================================================

REM Check Python 3.11+
py -3.11 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.11 is required. Please install Python 3.11 and add to PATH.
    pause
    exit /b 1
)

echo [1/3] Installing Python dependencies...
py -3.11 -m pip install --upgrade pip
py -3.11 -m pip install -r requirements.txt

echo [2/3] Initializing SQLite Database and schema...
py -3.11 -c "from app.database import init_db; init_db(); print('Database initialized successfully.')"

echo [3/3] Running automated unit and integration tests...
py -3.11 -m pytest tests/

echo ============================================================
echo   Setup Complete! You can now start the application using:
echo   run.bat
echo ============================================================
pause
