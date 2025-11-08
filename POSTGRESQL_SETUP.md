# PostgreSQL Setup & Migration Guide
## Romualdez Skin & Eye Clinic Management System

This guide provides complete instructions for setting up PostgreSQL database for the clinic management system.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [PostgreSQL Installation](#postgresql-installation)
3. [Database Setup](#database-setup)
4. [Environment Configuration](#environment-configuration)
5. [Running Migrations](#running-migrations)
6. [Creating Superuser](#creating-superuser)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have:
- Python 3.11 or higher installed
- pip (Python package manager)
- Administrative privileges on your system

---

## PostgreSQL Installation

### Windows

1. **Download PostgreSQL:**
   - Visit https://www.postgresql.org/download/windows/
   - Download PostgreSQL 17 or latest stable version
   - Choose the Windows x86-64 installer

2. **Run the Installer:**
   - Execute the downloaded `.exe` file
   - Keep default installation directory: `C:\Program Files\PostgreSQL\17`
   - **Important:** Remember the password you set for the `postgres` superuser
   - Default port: `5432` (keep this unless you have a conflict)
   - Install all components (PostgreSQL Server, pgAdmin 4, Stack Builder, Command Line Tools)

3. **Verify Installation:**
   ```bash
   # Open Command Prompt and type:
   psql --version
   ```
   Should display: `psql (PostgreSQL) 17.x`

### macOS

1. **Using Homebrew:**
   ```bash
   brew install postgresql@17
   brew services start postgresql@17
   ```

2. **Or download from:**
   - https://www.postgresql.org/download/macosx/
   - Or use Postgres.app: https://postgresapp.com/

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

---

## Database Setup

### Step 1: Access PostgreSQL

**Windows:**
```bash
# Option 1: Using SQL Shell (psql)
# Search for "SQL Shell (psql)" in Start Menu

# Option 2: Using Command Prompt
psql -U postgres
```

**macOS/Linux:**
```bash
sudo -u postgres psql
```

### Step 2: Create Database and User

Once in the PostgreSQL prompt (`postgres=#`), execute:

```sql
-- Create the database
CREATE DATABASE clinic_db;

-- Create the user with a secure password
CREATE USER clinic_user WITH PASSWORD 'clinic_secure_password_2025';

-- Grant all privileges on the database to the user
GRANT ALL PRIVILEGES ON DATABASE clinic_db TO clinic_user;

-- Connect to the database
\c clinic_db

-- Grant schema privileges (PostgreSQL 15+)
GRANT ALL ON SCHEMA public TO clinic_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO clinic_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO clinic_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO clinic_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO clinic_user;

-- Exit PostgreSQL
\q
```

### Step 3: Verify Database Creation

```bash
# List all databases
psql -U postgres -c "\l"

# Should show clinic_db in the list
```

---

## Environment Configuration

### Step 1: Create Environment File

Create a `.env` file in the project root directory (same level as `requirements.txt`):

```bash
# Navigate to project root
cd C:\Users\Admin\Documents\GitHub\Romualdez-Skin-and-Eye-Clinic

# Create .env file (Windows)
type nul > .env

# Or create .env file (macOS/Linux)
touch .env
```

### Step 2: Configure Environment Variables

Open `.env` in a text editor and add:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=clinic_db
DB_USER=clinic_user
DB_PASSWORD=clinic_secure_password_2025
DB_HOST=localhost
DB_PORT=5432

# Security Settings (Optional)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Email Configuration (Optional - for future use)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**Important Security Notes:**
- Never commit the `.env` file to version control
- Change `SECRET_KEY` to a unique random string for production
- Use strong passwords for `DB_PASSWORD`

### Step 3: Install Python Dependencies

```bash
# Navigate to project root
cd C:\Users\Admin\Documents\GitHub\Romualdez-Skin-and-Eye-Clinic

# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

---

## Running Migrations

### Step 1: Verify Database Connection

```bash
# Navigate to the Django project directory
cd clinic

# Test database connection
python manage.py check --database default
```

Expected output: `System check identified no issues (0 silenced).`

### Step 2: Apply All Migrations

```bash
# Show all migrations
python manage.py showmigrations

# Apply migrations
python manage.py migrate

# Expected output:
# Operations to perform:
#   Apply all migrations: admin, auth, axes, bookings, contenttypes, sessions
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   ... (all migrations will be listed)
```

### Step 3: Verify Migrations

```bash
# Check migration status
python manage.py showmigrations

# All migrations should have [X] next to them
```

### Migration List (47 total):
- **admin**: 3 migrations
- **auth**: 12 migrations
- **axes**: 8 migrations (login security)
- **bookings**: 21 migrations (core clinic features)
- **contenttypes**: 2 migrations
- **sessions**: 1 migration

---

## Creating Superuser

### Step 1: Create Admin Account

```bash
# Create superuser interactively
python manage.py createsuperuser

# You will be prompted:
# Username: admin
# Email address: admin@clinic.com
# Password: admin123 (or choose your own)
# Password (again): admin123
```

### Step 2: Verify Superuser

```bash
# Start development server
python manage.py runserver

# Open browser and navigate to:
# http://127.0.0.1:8000/admin/

# Login with the credentials you just created
```

---

## Seeding Test Data (Optional)

### Option 1: Use Provided Seed Script

```bash
# Navigate to clinic directory
cd clinic

# Run the minimal seed script
python seed_minimal.py
```

This creates:
- **7 Services**: General Consultation, Acne Treatment, Laser Hair Removal, etc.
- **7 Patient Profiles**: With test users (password: `patient123`)
- **11 Bookings**: Mix of completed, confirmed, and pending appointments

### Option 2: Manual Data Entry

Use the admin dashboard at `http://127.0.0.1:8000/admin/` to:
1. Add services
2. Create patient profiles
3. Schedule appointments

---

## Running the Application

### Start Development Server

```bash
# Make sure you're in the clinic directory
cd clinic

# Start server
python manage.py runserver

# Or specify a port
python manage.py runserver 8002
```

### Access Points:
- **Homepage**: http://127.0.0.1:8000/
- **Admin Login**: http://127.0.0.1:8000/admin/login/
- **Staff Login**: http://127.0.0.1:8000/admin/staff-login/
- **Patient Login**: http://127.0.0.1:8000/admin/login/
- **Admin Dashboard**: http://127.0.0.1:8000/admin/ (after login)

---

## Troubleshooting

### Common Issues

#### 1. "psql: command not found"

**Solution:**
- Windows: Add PostgreSQL bin directory to PATH:
  ```
  C:\Program Files\PostgreSQL\17\bin
  ```
- macOS/Linux: Install PostgreSQL client tools

#### 2. "FATAL: password authentication failed"

**Solution:**
```bash
# Reset PostgreSQL password
psql -U postgres

# In PostgreSQL prompt:
ALTER USER clinic_user WITH PASSWORD 'new_password';

# Update .env file with new password
```

#### 3. "django.db.utils.OperationalError: FATAL: database does not exist"

**Solution:**
```sql
-- Create the database if it doesn't exist
CREATE DATABASE clinic_db;
GRANT ALL PRIVILEGES ON DATABASE clinic_db TO clinic_user;
```

#### 4. "relation does not exist" errors

**Solution:**
```bash
# Reset and reapply migrations
python manage.py migrate --run-syncdb
```

#### 5. "port 5432 is already in use"

**Solution:**
```bash
# Windows: Stop PostgreSQL service
net stop postgresql-x64-17

# Or change port in .env:
DB_PORT=5433
```

#### 6. ImportError: No module named 'psycopg2'

**Solution:**
```bash
pip install psycopg2-binary
```

### Checking PostgreSQL Service Status

**Windows:**
```bash
# Check if service is running
sc query postgresql-x64-17

# Start service
net start postgresql-x64-17

# Stop service
net stop postgresql-x64-17
```

**macOS:**
```bash
brew services list
brew services start postgresql@17
```

**Linux:**
```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
```

---

## Database Backup & Restore

### Backup Database

```bash
# Create backup
pg_dump -U clinic_user -d clinic_db -F c -f clinic_backup.dump

# Or create SQL backup
pg_dump -U clinic_user -d clinic_db > clinic_backup.sql
```

### Restore Database

```bash
# Restore from custom format
pg_restore -U clinic_user -d clinic_db clinic_backup.dump

# Or restore from SQL
psql -U clinic_user -d clinic_db < clinic_backup.sql
```

---

## Production Deployment Checklist

When deploying to production:

1. **Security:**
   - [ ] Change `SECRET_KEY` to a unique random value
   - [ ] Set `DEBUG=False` in `.env`
   - [ ] Use strong passwords for database user
   - [ ] Enable SSL/HTTPS (`SECURE_SSL_REDIRECT=True`)
   - [ ] Set proper `ALLOWED_HOSTS`

2. **Database:**
   - [ ] Use a separate production database
   - [ ] Enable regular automated backups
   - [ ] Restrict database access to application server only

3. **Static Files:**
   ```bash
   python manage.py collectstatic --noinput
   ```

4. **Email:**
   - [ ] Configure production email backend
   - [ ] Update EMAIL_HOST settings in `.env`

5. **Server:**
   - [ ] Use Gunicorn or uWSGI instead of `runserver`
   - [ ] Configure Nginx or Apache as reverse proxy
   - [ ] Set up process manager (Supervisor/systemd)

---

## Additional Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **Project README**: See `README.md` for feature overview
- **Quick Start Guide**: See `docs/QUICKSTART.md`

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Django logs: Look for error messages in terminal
3. Check PostgreSQL logs: Located in `PostgreSQL\17\data\log\`

---

**Last Updated**: November 8, 2025
**PostgreSQL Version**: 17
**Django Version**: 5.2.7
**Python Version**: 3.11+
