"""
Ultra-Simple Seed Script - Works with actual models
"""
import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic.settings'); django.setup()

from django.contrib.auth.models import User
from bookings.models import Patient, Service, Booking
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
import random

# Clear data except superusers
User.objects.filter(is_superuser=False).delete()

print("Creating Services...")
services = [
    Service.objects.create(name='General Consultation', description='Skin & eye exam by specialist. 30 min.', price=Decimal('800.00')),
    Service.objects.create(name='Acne Treatment', description='Acne treatment with medication. 45 min.', price=Decimal('1200.00')),
    Service.objects.create(name='Laser Hair Removal', description='Permanent hair removal. 60 min.', price=Decimal('2500.00')),
    Service.objects.create(name='Chemical Peel', description='Skin rejuvenation treatment. 60 min.', price=Decimal('3000.00')),
    Service.objects.create(name='Eye Examination', description='Complete eye check-up. 30 min.', price=Decimal('600.00')),
    Service.objects.create(name='Botox Injection', description='Anti-aging wrinkle treatment. 30 min.', price=Decimal('8000.00')),
    Service.objects.create(name='Derma Facial', description='Deep cleansing facial. 60 min.', price=Decimal('1500.00')),
]

print(f"Creating 7 Patients...")
patients = []
data = [
    ('maria.santos', 'Maria', 'Santos', 'maria.santos@email.com', '09171234567', datetime(1995, 3, 15), 'F'),
    ('juan.delacruz', 'Juan', 'Dela Cruz', 'juan.delacruz@email.com', '09281234568', datetime(1988, 7, 22), 'M'),
    ('ana.reyes', 'Ana', 'Reyes', 'ana.reyes@email.com', '09391234569', datetime(2000, 11, 8), 'F'),
    ('pedro.garcia', 'Pedro', 'Garcia', 'pedro.garcia@email.com', '09451234570', datetime(1975, 5, 30), 'M'),
    ('rosa.martinez', 'Rosa', 'Martinez', 'rosa.martinez@email.com', '09561234571', datetime(1992, 9, 14), 'F'),
    ('carlos.lopez', 'Carlos', 'Lopez', 'carlos.lopez@email.com', '09671234572', datetime(1985, 12, 25), 'M'),
    ('elena.cruz', 'Elena', 'Cruz', 'elena.cruz@email.com', '09781234573', datetime(1998, 4, 18), 'F'),
]

for username, fn, ln, email, phone, dob, gender in data:
    user = User.objects.create_user(username=username, email=email, first_name=fn, last_name=ln, password='patient123')
    patient = Patient.objects.create(user=user, date_of_birth=dob, gender=gender, phone=phone, blood_type='O+')
    patients.append(patient)

print(f"Creating Bookings...")
# 5 past completed
for i in range(5):
    p = random.choice(patients)
    s = random.choice(services)
    d = timezone.now().date() - timedelta(days=random.randint(7, 60))
    t = datetime.strptime(random.choice(['09:00', '10:00', '14:00']), '%H:%M').time()
    Booking.objects.create(service=s, date=d, time=t, patient_name=p.user.get_full_name(),
                          patient_email=p.user.email, patient_phone=p.phone,
                          status='Completed', consultation_status='Done')

# 3 upcoming
for i in range(3):
    p = random.choice(patients)
    s = random.choice(services)
    d = timezone.now().date() + timedelta(days=random.randint(1, 14))
    t = datetime.strptime(random.choice(['10:00', '11:00', '14:00']), '%H:%M').time()
    Booking.objects.create(service=s, date=d, time=t, patient_name=p.user.get_full_name(),
                          patient_email=p.user.email, patient_phone=p.phone,
                          status='Confirmed', consultation_status='Not Yet')

# 2 pending
for i in range(2):
    p = random.choice(patients)
    s = random.choice(services)
    d = timezone.now().date() + timedelta(days=random.randint(3, 21))
    t = datetime.strptime('10:00', '%H:%M').time()
    Booking.objects.create(service=s, date=d, time=t, patient_name=p.user.get_full_name(),
                          patient_email=p.user.email, patient_phone=p.phone,
                          status='Pending', consultation_status='Not Yet')

print()
print("=" * 70)
print("✅ DATABASE SEEDED SUCCESSFULLY!")
print("=" * 70)
print(f"Services: {Service.objects.count()}")
print(f"Patients: {Patient.objects.count()}")
print(f"Bookings: {Booking.objects.count()}")
print()
print("LOGIN CREDENTIALS:")
print("  Admin: admin / admin123")
print("  Patients: maria.santos, juan.delacruz, ana.reyes, pedro.garcia,")
print("            rosa.martinez, carlos.lopez, elena.cruz / patient123")
print()
print("🌐 Server: http://127.0.0.1:8002/")
print("=" * 70)
