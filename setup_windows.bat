@echo off
echo ============================================
echo Stock Analysis Tool - Windows Setup
echo ============================================
echo.

echo [1] Creating Python virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create Python virtual environment
    echo Please ensure Python 3.8+ is installed and added to PATH
    pause
    exit /b 1
)

echo [2] Activating virtual environment...
call venv\Scripts\activate

echo [3] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo [4] Creating data directories...
if not exist "data\database" mkdir data\database
if not exist "data\database\backups" mkdir data\database\backups
if not exist "data\cache" mkdir data\cache
if not exist "data\exports" mkdir data\exports
if not exist "logs" mkdir logs

echo [5] Setting up environment configuration...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env
        echo Created .env file from .env.example
    ) else (
        echo # Stock Analysis Tool Configuration > .env
        echo SECRET_KEY=your-secret-key-here >> .env
        echo Created basic .env file
    )
)

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo To start the application, run:
echo   start_app.bat
echo.
echo Or manually start with:
echo   venv\Scripts\activate
echo   python app.py
echo.
echo Then access: http://localhost:5000
echo.
pause