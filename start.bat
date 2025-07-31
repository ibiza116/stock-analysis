@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ===============================================
echo Stock Analysis Tool Startup
echo ===============================================
echo Working Directory: %CD%
echo.

if exist "myenv\Scripts\python.exe" (
    echo [1/4] Activating virtual environment...
    call myenv\Scripts\activate.bat
    
    echo [2/4] Installing dependencies...
    myenv\Scripts\pip.exe install -r requirements.txt -q
    
    echo [3/4] Starting Flask server...
    echo.
    echo Stock Analysis Tool is ready!
    echo Default stock: Toyota Motor (7203)
    echo Access URL: http://localhost:5000
    echo.
    echo Browser will open automatically in 3 seconds...
    echo Press Ctrl+C to stop the server
    echo.
    
    REM Open browser after 3 seconds in background
    start /b cmd /c "ping 127.0.0.1 -n 4 >nul && start http://localhost:5000"
    
    echo [4/4] Launching Flask application...
    echo.
    myenv\Scripts\python.exe app.py
    
) else (
    echo ERROR: Virtual environment not found
    echo.
    echo Please run the following commands first:
    echo   python -m venv myenv
    echo   myenv\Scripts\pip.exe install -r requirements.txt
    echo.
    pause
    exit /b 1
)