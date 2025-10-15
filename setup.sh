#!/bin/bash

echo "========================================"
echo "Romualdez Clinic Setup Script"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.12 or higher"
    exit 1
fi

echo "[INFO] Found: $(python3 --version)"

echo "[1/6] Creating virtual environment..."
python3 -m venv .venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi

echo "[2/6] Activating virtual environment..."
source .venv/bin/activate

echo "[3/6] Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo "[4/6] Navigating to project directory..."
cd clinic

echo "[5/6] Applying database migrations..."
python manage.py migrate

echo "[6/6] Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "To create an admin account, run:"
echo "  python manage.py createsuperuser"
echo ""
echo "To start the server, run:"
echo "  python manage.py runserver"
echo ""
echo "Then visit: http://127.0.0.1:8000/"
echo ""
