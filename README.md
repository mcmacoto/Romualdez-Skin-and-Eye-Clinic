# Romualdez Skin and Eye Clinic Management System

A comprehensive clinic management system built with Django for managing appointments, patients, medical records, inventory, and billing.

## Features

- **Patient Management**: Track patient information and medical history
- **Appointment Scheduling**: Manage appointments with status tracking
- **Medical Records**: Store and manage patient medical records and images
- **Inventory Management**: Track clinic inventory and stock transactions
- **Billing System**: Handle billing, payments, and invoices
- **POS System**: Point-of-sale functionality for clinic services and products
- **Staff Portal**: Admin interface for staff to manage clinic operations

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.12 or higher
- pip (Python package manager)
- Git

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

### 5. Apply Database Migrations

```bash
python manage.py migrate
```

### 6. Create a Superuser (Admin Account)

```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 8. Run the Development Server

```bash
python manage.py runserver
```

The application will be available at: **http://127.0.0.1:8000/**

## Access Points

- **Main Site**: http://127.0.0.1:8000/
- **Admin Portal**: http://127.0.0.1:8000/admin/
- **Staff Dashboard**: http://127.0.0.1:8000/admin/ (login required)

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
│   │   ├── models.py           # Database models
│   │   ├── views.py            # View logic
│   │   ├── admin.py            # Admin configurations
│   │   ├── templates/          # HTML templates
│   │   └── management/         # Custom management commands
│   ├── clinic/                 # Project settings
│   │   ├── settings.py         # Django settings
│   │   ├── urls.py             # URL configurations
│   │   └── wsgi.py             # WSGI config
│   ├── static/                 # Static files (CSS, JS, images)
│   ├── staticfiles/            # Collected static files (generated)
│   ├── templates/              # Base templates
│   ├── db.sqlite3              # SQLite database
│   └── manage.py               # Django management script
├── requirements.txt            # Python dependencies
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

**Last Updated**: October 15, 2025
