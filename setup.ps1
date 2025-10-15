# Romualdez Clinic Setup Script for PowerShell
Write-Host "========================================" -ForegroundColor Green
Write-Host "Romualdez Clinic Setup Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[INFO] Found: $pythonVersion" -ForegroundColor Cyan
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.12 or higher from python.org" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "[1/6] Creating virtual environment..." -ForegroundColor Yellow
python -m venv .venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "[2/6] Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

Write-Host "[3/6] Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "[4/6] Navigating to project directory..." -ForegroundColor Yellow
Set-Location clinic

Write-Host "[5/6] Applying database migrations..." -ForegroundColor Yellow
python manage.py migrate

Write-Host "[6/6] Collecting static files..." -ForegroundColor Yellow
python manage.py collectstatic --noinput

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To create an admin account, run:" -ForegroundColor Cyan
Write-Host "  python manage.py createsuperuser" -ForegroundColor White
Write-Host ""
Write-Host "To start the server, run:" -ForegroundColor Cyan
Write-Host "  python manage.py runserver" -ForegroundColor White
Write-Host ""
Write-Host "Then visit: http://127.0.0.1:8000/" -ForegroundColor Yellow
Write-Host ""
pause
