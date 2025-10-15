# Quick Start Guide - Romualdez Skin and Eye Clinic

## For New Developers

### Option 1: Automated Setup (Recommended)

**Windows (PowerShell):**
```powershell
.\setup.ps1
```

**Windows (Command Prompt):**
```cmd
setup.bat
```

**macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

1. **Create virtual environment:**
   ```bash
   python -m venv .venv
   ```

2. **Activate virtual environment:**
   - Windows PowerShell: `.\.venv\Scripts\Activate.ps1`
   - Windows CMD: `.venv\Scripts\activate.bat`
   - macOS/Linux: `source .venv/bin/activate`

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Navigate to project:**
   ```bash
   cd clinic
   ```

5. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Create admin account:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect static files:**
   ```bash
   python manage.py collectstatic
   ```

8. **Run server:**
   ```bash
   python manage.py runserver
   ```

9. **Open browser:**
   Go to http://127.0.0.1:8000/

## Daily Development Workflow

```bash
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1  # Windows PowerShell

# 2. Navigate to project
cd clinic

# 3. Pull latest changes (if working in a team)
git pull origin main

# 4. Run server
python manage.py runserver
```

## Common Commands

### Server Management
```bash
# Start development server
python manage.py runserver

# Start on different port
python manage.py runserver 8080

# Start with different IP
python manage.py runserver 0.0.0.0:8000
```

### Database Management
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Access Django shell
python manage.py shell
```

### Static Files
```bash
# Collect static files
python manage.py collectstatic

# Clear and recollect
python manage.py collectstatic --clear --noinput
```

### Sample Data
```bash
# Create sample medical data
python manage.py create_sample_medical_data

# Create staff accounts
python manage.py create_staff

# Clean database (development only!)
python manage.py clear_database
```

## Troubleshooting

### Virtual Environment Issues
```bash
# Deactivate current environment
deactivate

# Remove and recreate
Remove-Item -Recurse -Force .venv  # Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Package Issues
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Reinstall all packages
pip install -r requirements.txt --force-reinstall
```

### Database Issues
```bash
# Delete database and start fresh
Remove-Item db.sqlite3  # Windows
rm db.sqlite3          # macOS/Linux

# Recreate
python manage.py migrate
python manage.py createsuperuser
```

### Static Files Not Loading
```bash
# Recollect static files
python manage.py collectstatic --clear --noinput

# Check STATIC_URL in settings.py
# Check that files are in clinic/static/ directory
```

## Access Points

- **Main Site**: http://127.0.0.1:8000/
- **Admin Portal**: http://127.0.0.1:8000/admin/
- **Landing Page**: http://127.0.0.1:8000/landing/

## Default Admin Credentials (if using sample data)

Check with your team lead for default credentials or create your own using:
```bash
python manage.py createsuperuser
```

## Need Help?

1. Check README.md for detailed documentation
2. See CONTRIBUTING.md for development guidelines
3. Contact the development team
4. Create an issue on GitHub

---

**Pro Tip:** Keep your virtual environment activated while developing to avoid import errors!
