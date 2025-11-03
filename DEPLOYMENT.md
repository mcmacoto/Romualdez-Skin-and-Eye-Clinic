# Deployment Guide

This guide provides comprehensive instructions for deploying the Romualdez Skin and Eye Clinic Management System to a production environment.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [Option 1: Docker Deployment](#option-1-docker-deployment-recommended)
4. [Option 2: Manual Ubuntu/Debian Deployment](#option-2-manual-ubuntudebian-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Database Setup](#database-setup)
7. [Static and Media Files](#static-and-media-files)
8. [HTTPS/SSL Setup](#httpsssl-setup)
9. [Post-Deployment Steps](#post-deployment-steps)
10. [Monitoring and Maintenance](#monitoring-and-maintenance)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required
- **Server**: Ubuntu 20.04+ / Debian 11+ (or Docker-compatible host)
- **Python**: 3.10 or higher
- **Database**: PostgreSQL 13+ (recommended) or MySQL 8.0+
- **Domain**: Registered domain name with DNS configured
- **SSL Certificate**: Let's Encrypt or commercial certificate

### Recommended
- **Memory**: 2GB RAM minimum (4GB+ recommended)
- **Storage**: 20GB minimum (for database, media files, logs)
- **Backup**: Automated backup solution configured

---

## Deployment Options

### Comparison

| Feature | Docker | Manual |
|---------|--------|--------|
| **Setup Time** | 15-30 minutes | 1-2 hours |
| **Complexity** | Low | Medium |
| **Isolation** | High (containerized) | Medium |
| **Resource Usage** | Slightly higher | Optimized |
| **Updates** | Easy (rebuild image) | Manual |
| **Best For** | Quick deployment, CI/CD | Full control, optimization |

---

## Option 1: Docker Deployment (Recommended)

### Step 1: Install Docker

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Add user to docker group (logout and login after)
sudo usermod -aG docker $USER
```

### Step 2: Prepare Application Files

```bash
# Clone repository
git clone https://github.com/mcmacoto/Romualdez-Skin-and-Eye-Clinic.git
cd Romualdez-Skin-and-Eye-Clinic

# Create environment file
cp .env.example .env
```

### Step 3: Configure Environment Variables

Edit `.env` file with production settings:

```bash
nano .env
```

**Critical Production Settings:**

```env
# Django Settings
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (PostgreSQL with Docker)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=clinic_db
DB_USER=clinic_user
DB_PASSWORD=your-secure-db-password
DB_HOST=db
DB_PORT=5432

# Email (Production SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-clinic-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

### Step 4: Create Docker Files

**Create `Dockerfile`:**

```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project files
COPY . /app/

# Collect static files
RUN python clinic/manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--chdir", "clinic", "clinic.wsgi:application"]
```

**Create `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    restart: always

  web:
    build: .
    command: gunicorn --bind 0.0.0.0:8000 --chdir clinic clinic.wsgi:application
    volumes:
      - ./clinic:/app/clinic
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
    restart: always

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - /etc/letsencrypt:/etc/letsencrypt
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web
    restart: always

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

**Create `nginx.conf`:**

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    upstream django {
        server web:8000;
    }

    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL Configuration
        ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers on;

        client_max_body_size 10M;

        # Static files
        location /static/ {
            alias /app/staticfiles/;
        }

        # Media files
        location /media/ {
            alias /app/media/;
        }

        # Django application
        location / {
            proxy_pass http://django;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### Step 5: Deploy with Docker

```bash
# Build and start containers
docker-compose up -d --build

# Run migrations
docker-compose exec web python clinic/manage.py migrate

# Create superuser
docker-compose exec web python clinic/manage.py createsuperuser

# Collect static files (if not done in Dockerfile)
docker-compose exec web python clinic/manage.py collectstatic --noinput

# Check logs
docker-compose logs -f
```

---

## Option 2: Manual Ubuntu/Debian Deployment

### Step 1: System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip \
    postgresql postgresql-contrib nginx git \
    build-essential libpq-dev python3-dev
```

### Step 2: Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE clinic_db;
CREATE USER clinic_user WITH PASSWORD 'your-secure-password';
ALTER ROLE clinic_user SET client_encoding TO 'utf8';
ALTER ROLE clinic_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE clinic_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE clinic_db TO clinic_user;
\q
```

### Step 3: Application Setup

```bash
# Create application user
sudo useradd -m -s /bin/bash clinic
sudo su - clinic

# Clone repository
git clone https://github.com/mcmacoto/Romualdez-Skin-and-Eye-Clinic.git
cd Romualdez-Skin-and-Eye-Clinic

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
cp .env.example .env
nano .env  # Edit with production settings
```

### Step 4: Django Configuration

```bash
# Run migrations
cd clinic
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Test application
python manage.py runserver 0.0.0.0:8000
```

### Step 5: Gunicorn Setup

**Create systemd service file:**

```bash
sudo nano /etc/systemd/system/clinic.service
```

**Content:**

```ini
[Unit]
Description=Romualdez Clinic Gunicorn Daemon
After=network.target

[Service]
User=clinic
Group=www-data
WorkingDirectory=/home/clinic/Romualdez-Skin-and-Eye-Clinic/clinic
ExecStart=/home/clinic/Romualdez-Skin-and-Eye-Clinic/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/home/clinic/Romualdez-Skin-and-Eye-Clinic/clinic.sock \
    clinic.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Start service:**

```bash
sudo systemctl start clinic
sudo systemctl enable clinic
sudo systemctl status clinic
```

### Step 6: Nginx Configuration

**Create Nginx config:**

```bash
sudo nano /etc/nginx/sites-available/clinic
```

**Content:**

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 10M;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /home/clinic/Romualdez-Skin-and-Eye-Clinic/staticfiles/;
    }

    location /media/ {
        alias /home/clinic/Romualdez-Skin-and-Eye-Clinic/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/clinic/Romualdez-Skin-and-Eye-Clinic/clinic.sock;
    }
}
```

**Enable site:**

```bash
sudo ln -s /etc/nginx/sites-available/clinic /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

---

## HTTPS/SSL Setup

### Using Let's Encrypt (Free)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

**Certbot will automatically update Nginx config for HTTPS.**

---

## Post-Deployment Steps

### 1. Security Checklist

```bash
# Verify DEBUG is False
grep DEBUG .env

# Check ALLOWED_HOSTS
grep ALLOWED_HOSTS .env

# Verify SECRET_KEY is unique
grep SECRET_KEY .env
```

### 2. Create Initial Staff Accounts

```bash
# Access Django shell
python clinic/manage.py shell

# Create staff users
from django.contrib.auth.models import User
User.objects.create_user('staff1', 'staff1@clinic.com', 'secure-password', is_staff=True)
```

Or use management command:

```bash
python clinic/manage.py create_staff
```

### 3. Configure Firewall

```bash
# Allow HTTP/HTTPS
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

### 4. Set Up Backups

**Database Backup Script (`backup_db.sh`):**

```bash
#!/bin/bash
BACKUP_DIR="/home/clinic/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U clinic_user clinic_db > $BACKUP_DIR/db_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /home/clinic/Romualdez-Skin-and-Eye-Clinic/media

# Delete backups older than 7 days
find $BACKUP_DIR -mtime +7 -delete
```

**Add to crontab:**

```bash
crontab -e
# Add: 0 2 * * * /home/clinic/backup_db.sh
```

---

## Monitoring and Maintenance

### Application Logs

```bash
# Gunicorn logs
sudo journalctl -u clinic -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### System Monitoring

**Install monitoring tools:**

```bash
sudo apt install htop iotop nethogs -y
```

**Check system resources:**

```bash
htop  # CPU and memory
df -h  # Disk usage
free -h  # Memory usage
```

### Regular Maintenance

**Weekly:**
- Check application logs for errors
- Verify backup completion
- Monitor disk space

**Monthly:**
- Update system packages: `sudo apt update && sudo apt upgrade -y`
- Update Python dependencies: `pip install --upgrade -r requirements.txt`
- Review database size and performance
- Test backup restoration

---

## Troubleshooting

### Issue: Static Files Not Loading

```bash
# Verify static files collected
ls -la /home/clinic/Romualdez-Skin-and-Eye-Clinic/staticfiles

# Re-collect static files
python clinic/manage.py collectstatic --noinput

# Check Nginx permissions
sudo chown -R www-data:www-data /home/clinic/Romualdez-Skin-and-Eye-Clinic/staticfiles
```

### Issue: 502 Bad Gateway

```bash
# Check Gunicorn status
sudo systemctl status clinic

# Restart Gunicorn
sudo systemctl restart clinic

# Check socket file exists
ls -la /home/clinic/Romualdez-Skin-and-Eye-Clinic/clinic.sock

# Check Gunicorn logs
sudo journalctl -u clinic -n 50
```

### Issue: Database Connection Error

```bash
# Verify PostgreSQL is running
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -d clinic_db -U clinic_user

# Check .env database settings
grep DB_ .env
```

### Issue: Permission Denied Errors

```bash
# Fix application permissions
sudo chown -R clinic:www-data /home/clinic/Romualdez-Skin-and-Eye-Clinic
sudo chmod -R 755 /home/clinic/Romualdez-Skin-and-Eye-Clinic

# Fix media directory
sudo chmod -R 775 /home/clinic/Romualdez-Skin-and-Eye-Clinic/media
```

---

## Performance Optimization

### Enable Gzip Compression (Nginx)

Add to `nginx.conf`:

```nginx
http {
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss 
               application/javascript application/json;
}
```

### Database Query Optimization

```bash
# Install pgBouncer for connection pooling
sudo apt install pgbouncer -y

# Configure in .env
DB_HOST=localhost
DB_PORT=6432  # pgBouncer port
```

### Caching with Redis

```bash
# Install Redis
sudo apt install redis-server -y

# Add to .env
CACHE_BACKEND=django_redis.cache.RedisCache
CACHE_LOCATION=redis://127.0.0.1:6379/1

# Install django-redis
pip install django-redis
```

---

## Support

- **Documentation**: See `README.md` and `CONTRIBUTING.md`
- **Issues**: [GitHub Issues](https://github.com/mcmacoto/Romualdez-Skin-and-Eye-Clinic/issues)
- **Security**: See `SECURITY.md` for vulnerability reporting

---

**Last Updated**: November 3, 2025  
**Version**: 2.0.0
