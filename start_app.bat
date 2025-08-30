@echo off
echo ============================================
echo Stock Analysis Tool - Application Start
echo ============================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run setup_windows.bat first
    pause
    exit /b 1
)

echo [1] Activating virtual environment...
call venv\Scripts\activate

echo [2] Starting application...
echo.
echo Access the application in your browser:
echo http://localhost:5000
echo.
echo Press Ctrl+C to stop the application
echo.

python app.py