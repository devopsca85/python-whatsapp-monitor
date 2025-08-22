@echo off
echo ========================================
echo    Server Monitor - Starting...
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Check if config.json exists
if not exist "config.json" (
    echo ERROR: config.json not found
    echo Please run the setup first
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting server monitor...
echo Press Ctrl+C to stop monitoring
echo.

REM Start the monitoring script
python server_monitor.py

pause


