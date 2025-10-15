@echo off
echo ========================================
echo Romualdez Clinic Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.12 or higher from python.org
    pause
    exit /b 1
)

echo [1/6] Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/6] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [3/6] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/6] Navigating to project directory...
cd clinic

echo [5/6] Applying database migrations...
python manage.py migrate

echo [6/6] Collecting static files...
python manage.py collectstatic --noinput

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To create an admin account, run:
echo   python manage.py createsuperuser
echo.
echo To start the server, run:
echo   python manage.py runserver
echo.
echo Then visit: http://127.0.0.1:8000/
echo.
pause
