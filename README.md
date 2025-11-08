# Romualdez Skin and Eye Clinic Management System

A comprehensive clinic management system built with **Django 5.2.7**, **PostgreSQL 17**, **Bootstrap 5.3.2**, **HTMX 1.9.10**, and **Alpine.js 3.13.3** for managing appointments, patients, medical records, inventory, and billing. Features a modern professional interface with full mobile responsiveness and enhanced user experience.

**📚 Important:** For PostgreSQL database setup, see [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) for complete installation and configuration instructions.

## Features

### Core Functionality
- **Patient Management**: Track patient information, medical history, and demographics
- **Appointment Scheduling**: Manage appointments with real-time status tracking
- **Medical Records**: Store and manage patient medical records with image support
- **Inventory Management**: Track clinic inventory, stock levels, and transactions
- **Billing System**: Handle billing, payments, and invoice generation
- **POS System**: Point-of-sale functionality for clinic services and products
- **Prescription Management**: Create and manage patient prescriptions

### V2 Modern Dashboard
- **HTMX Integration**: Dynamic content loading without page refreshes
- **Modal-Based CRUD**: Create, read, update, delete operations in modals
- **Image Cropper**: Professional image cropping for service photos with aspect ratio controls
- **Toast Notifications**: Real-time feedback for user actions
- **Enhanced UI/UX**: Modern, responsive design with improved navigation
- **Template Tags**: Custom formatting for service descriptions with bullet points
- **Performance Optimized**: Database query optimization with prefetch_related

### Admin Features
- **Staff Portal**: Comprehensive admin interface for clinic operations
- **User Management**: Create and manage staff and patient accounts
- **Role-Based Access**: Permission system for different user types
- **Service Management**: Add and edit clinic services with image upload
- **Dashboard Analytics**: Quick overview of appointments, patients, and billing

## Technology Stack

- **Backend:** Django 5.2.7, Python 3.11+
- **Database:** PostgreSQL 17
- **Frontend:** Bootstrap 5.3.2, HTMX 1.9.10, Alpine.js 3.13.3
- **Icons:** Font Awesome 6.4.0
- **Image Processing:** Cropper.js 1.6.1
- **Security:** Django Axes 6.1.1 (login protection)
- **Animations:** AOS (Animate On Scroll)

## Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.11 or higher**
- **PostgreSQL 17** (see [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md))
- **pip** (Python package manager)
- **Git**

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/mcmacoto/Romualdez-Skin-and-Eye-Clinic.git
cd Romualdez-Skin-and-Eye-Clinic
```

### 2. Create a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Navigate to the Project Directory

```bash
cd clinic
```

### 5. Set Up PostgreSQL Database

**Important:** PostgreSQL 17 must be installed and configured. Follow the complete guide:

📖 **[PostgreSQL Setup Guide](POSTGRESQL_SETUP.md)** - Complete instructions for:
- Installing PostgreSQL
- Creating database and user
- Configuring environment variables
- Running migrations
- Troubleshooting common issues

**Quick setup summary:**
```sql
-- In PostgreSQL prompt (psql -U postgres):
CREATE DATABASE clinic_db;
CREATE USER clinic_user WITH PASSWORD 'clinic_secure_password_2025';
GRANT ALL PRIVILEGES ON DATABASE clinic_db TO clinic_user;
```

### 6. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (PostgreSQL)
DB_NAME=clinic_db
DB_USER=clinic_user
DB_PASSWORD=clinic_secure_password_2025
DB_HOST=localhost
DB_PORT=5432
```

Generate a SECRET_KEY:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 7. Apply Database Migrations

```bash
python manage.py migrate
```

Expected: 47 migrations (admin, auth, axes, bookings, contenttypes, sessions)

### 8. Create a Superuser (Admin Account)

```bash
python manage.py createsuperuser

# Recommended credentials for development:
# Username: admin
# Email: admin@clinic.com
# Password: admin123 (or choose your own)
```

### 9. (Optional) Seed Test Data

```bash
# Load sample data for testing
python seed_minimal.py
```

This creates:
- 7 services (consultations, treatments)
- 7 patient profiles (password: patient123)
- 11 bookings (completed, confirmed, pending)

### 10. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 11. Run the Development Server

```bash
python manage.py runserver

# Or specify a port:
python manage.py runserver 8002
```

The application will be available at: **http://127.0.0.1:8000/**

## Access Points

- **Landing Page**: http://127.0.0.1:8000/landing/
- **Main Site**: http://127.0.0.1:8000/
- **Services Page**: http://127.0.0.1:8000/services/
- **Admin Dashboard (V2)**: http://127.0.0.1:8000/admin/admin-dashboard/
- **Staff Login**: http://127.0.0.1:8000/admin/staff-login/
- **Django Admin**: http://127.0.0.1:8000/admin/

## Environment Configuration

### 1. Copy the example environment file

```bash
cp .env.example .env
```

### 2. Edit .env and configure:

```bash
# Generate a new SECRET_KEY (required)
SECRET_KEY=your-secret-key-here-use-python-get-random-secret-key

# Set DEBUG (False for production)
DEBUG=True

# Add your domain for production
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
```

### 3. Generate a SECRET_KEY

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Quick Start Commands

After initial setup, you only need to run these commands:

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
# OR
source .venv/bin/activate      # macOS/Linux

# Navigate to project
cd clinic

# Run server
python manage.py runserver
```

## Project Structure

```
Romualdez-Skin-and-Eye-Clinic/
├── .venv/                      # Virtual environment (not in git)
├── clinic/                     # Main project directory
│   ├── bookings/               # Main application
│   │   ├── models/             # Database models (modular)
│   │   │   ├── appointments.py # Appointment & Booking models
│   │   │   ├── patients.py     # Patient & MedicalRecord models
│   │   │   ├── billing.py      # Billing & Payment models
│   │   │   ├── inventory.py    # Inventory & Stock models
│   │   │   ├── prescriptions.py# Prescription models
│   │   │   ├── pos.py          # POS Sale models
│   │   │   └── base.py         # Service model
│   │   ├── views_v2/           # V2 view logic (modular)
│   │   │   ├── admin_management_views.py
│   │   │   ├── patient_views.py
│   │   │   ├── appointment_views.py
│   │   │   ├── billing_views.py
│   │   │   └── inventory_views.py
│   │   ├── templates/          # HTML templates
│   │   │   └── bookings_v2/    # V2 templates
│   │   │       ├── admin_dashboard_v2.html
│   │   │       └── htmx_partials/  # HTMX partial templates
│   │   ├── static/             # Static files (CSS, JS, images)
│   │   │   ├── css/            # Stylesheets
│   │   │   ├── js/             # JavaScript files
│   │   │   │   └── global_cropper.js  # Image cropper module
│   │   │   └── images/         # Static images
│   │   ├── templatetags/       # Custom template tags
│   │   │   └── description_filters.py
│   │   ├── utils/              # Utility functions
│   │   ├── management/         # Custom management commands
│   │   │   └── commands/       # Django commands
│   │   ├── migrations/         # Database migrations
│   │   ├── middleware.py       # Custom middleware
│   │   ├── signals.py          # Django signals
│   │   └── urls_v2.py          # V2 URL configurations
│   ├── clinic/                 # Project settings
│   │   ├── settings.py         # Django settings
│   │   ├── urls.py             # Main URL configurations
│   │   └── wsgi.py             # WSGI config
│   ├── media/                  # User uploaded files
│   │   ├── services/           # Service images
│   │   └── medical_records/    # Patient medical images
│   ├── static/                 # Additional static files
│   ├── staticfiles/            # Collected static files (generated)
│   ├── templates/              # Base templates
│   ├── db.sqlite3              # SQLite database (development)
│   ├── manage.py               # Django management script
│   ├── test_filter.py          # Template filter tests
│   ├── test_workflow.py        # Workflow tests
│   └── verify_database.py      # Database verification script
├── docs/                       # Documentation
│   ├── QUICKSTART.md           # Quick start guide
│   └── CONTRIBUTING.md         # Contribution guidelines
├── tools/                      # Development tools
│   └── test_description_format.py
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
├── setup.ps1                   # Windows PowerShell setup script
├── setup.bat                   # Windows CMD setup script
├── setup.sh                    # macOS/Linux setup script
└── README.md                   # This file
```

## Managing the Database

### Create Sample Data

```bash
python manage.py create_sample_medical_data
```

### Create Staff Accounts

```bash
python manage.py create_staff
```

### Clear Database (Development Only)

```bash
python manage.py clear_database
```

### Reset and Setup

```bash
python manage.py cleanup_system
```

## Common Issues & Solutions

### Issue: "No module named django"

**Solution:** Make sure your virtual environment is activated and Django is installed:
```bash
.\.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

### Issue: "manage.py: No such file or directory"

**Solution:** Make sure you're in the `clinic` directory:
```bash
cd clinic
```

### Issue: Static files not loading

**Solution:** Run collectstatic:
```bash
python manage.py collectstatic --noinput
```

### Issue: Database errors

**Solution:** Apply migrations:
```bash
python manage.py migrate
```

## Development

### Installing New Packages

When you install a new package, update requirements.txt:
```bash
pip install <package-name>
pip freeze > requirements.txt
```

### Making Database Changes

1. Modify models in `bookings/models.py`
2. Create migrations: `python manage.py makemigrations`
3. Apply migrations: `python manage.py migrate`

## Configuration

Key settings can be found in `clinic/clinic/settings.py`:

- **DEBUG**: Set to `False` in production
- **ALLOWED_HOSTS**: Add your domain in production
- **SECRET_KEY**: Change this in production
- **DATABASES**: Configure your database (default: SQLite)

## Security Notes

⚠️ **Important for Production:**

1. Set `DEBUG = False` in `settings.py`
2. Change `SECRET_KEY` to a new, random value
3. Update `ALLOWED_HOSTS` with your domain
4. Use a production database (PostgreSQL, MySQL)
5. Configure HTTPS
6. Set up proper media file handling
7. Enable CSRF protection
8. Configure proper logging

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## Technology Stack

- **Backend**: Django 5.2.7
- **Database**: SQLite (development), PostgreSQL (production recommended)
- **Frontend**: HTML, CSS, JavaScript
- **Image Processing**: Pillow 11.3.0

## License

This project is proprietary software for Romualdez Skin and Eye Clinic.

## Support

For issues or questions, please contact the development team or create an issue in the repository.

## Authors

- **Development Team**: [Your Name/Team]
- **Client**: Romualdez Skin and Eye Clinic

---

**Last Updated**: November 3, 2025
**Version**: 2.0.0
