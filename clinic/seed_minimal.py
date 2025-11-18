"""
Comprehensive Seed Script - Full Module Coverage
Creates test data for all system modules to ensure complete functionality testing
"""
import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic.settings'); django.setup()

from django.contrib.auth.models import User
from bookings.models import (
    Patient, Service, Booking, Doctor, MedicalRecord, Billing, Payment,
    Inventory, StockTransaction, POSSale, POSSaleItem, Prescription,
    ActivityLog, ClinicSettings
)
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.utils import timezone
import random

# Clear data except superusers
print("Clearing existing data...")
print("  - Clearing prescriptions (must be deleted before inventory)...")
Prescription.objects.all().delete()
print("  - Clearing bookings, medical records, billing...")
Booking.objects.all().delete()  # Cascades to Billing, MedicalRecord
print("  - Clearing POS sales...")
POSSale.objects.all().delete()  # Cascades to POSSaleItem
print("  - Clearing inventory transactions...")
StockTransaction.objects.all().delete()
print("  - Clearing inventory items...")
Inventory.objects.all().delete()
print("  - Clearing doctors and services...")
Doctor.objects.all().delete()
Service.objects.all().delete()
print("  - Clearing activity logs...")
ActivityLog.objects.all().delete()
print("  - Clearing users (keeping superusers)...")
User.objects.filter(is_superuser=False).delete()  # Cascades to Patient

# Ensure admin user exists
print("Checking admin user...")
admin_user = User.objects.filter(username='admin').first()
if not admin_user:
    print("Creating admin user...")
    admin_user = User.objects.create_superuser(
        username='admin',
        email='admin@clinic.com',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    print("✅ Admin user created: admin / admin123")
else:
    print(f"✅ Admin user exists: {admin_user.username}")

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

print(f"Creating 17 Patients...")
patients = []
blood_types = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']
data = [
    ('maria.santos', 'Maria', 'Santos', 'maria.santos@email.com', '09171234567', datetime(1995, 3, 15), 'F', 'O+'),
    ('juan.delacruz', 'Juan', 'Dela Cruz', 'juan.delacruz@email.com', '09281234568', datetime(1988, 7, 22), 'M', 'A+'),
    ('ana.reyes', 'Ana', 'Reyes', 'ana.reyes@email.com', '09391234569', datetime(2000, 11, 8), 'F', 'B+'),
    ('pedro.garcia', 'Pedro', 'Garcia', 'pedro.garcia@email.com', '09451234570', datetime(1975, 5, 30), 'M', 'O-'),
    ('rosa.martinez', 'Rosa', 'Martinez', 'rosa.martinez@email.com', '09561234571', datetime(1992, 9, 14), 'F', 'A-'),
    ('carlos.lopez', 'Carlos', 'Lopez', 'carlos.lopez@email.com', '09671234572', datetime(1985, 12, 25), 'M', 'AB+'),
    ('elena.cruz', 'Elena', 'Cruz', 'elena.cruz@email.com', '09781234573', datetime(1998, 4, 18), 'F', 'B-'),
    ('luis.fernandez', 'Luis', 'Fernandez', 'luis.fernandez@email.com', '09181234574', datetime(1990, 1, 10), 'M', 'O+'),
    ('sofia.ramirez', 'Sofia', 'Ramirez', 'sofia.ramirez@email.com', '09191234575', datetime(1997, 6, 25), 'F', 'A+'),
    ('miguel.torres', 'Miguel', 'Torres', 'miguel.torres@email.com', '09201234576', datetime(1982, 8, 14), 'M', 'B+'),
    ('clara.mendoza', 'Clara', 'Mendoza', 'clara.mendoza@email.com', '09211234577', datetime(2001, 12, 3), 'F', 'AB-'),
    ('diego.valencia', 'Diego', 'Valencia', 'diego.valencia@email.com', '09221234578', datetime(1978, 4, 20), 'M', 'O-'),
    ('isabela.morales', 'Isabela', 'Morales', 'isabela.morales@email.com', '09231234579', datetime(1994, 10, 7), 'F', 'A-'),
    ('ricardo.castro', 'Ricardo', 'Castro', 'ricardo.castro@email.com', '09241234580', datetime(1986, 2, 28), 'M', 'B-'),
    ('camila.ortiz', 'Camila', 'Ortiz', 'camila.ortiz@email.com', '09251234581', datetime(1999, 7, 16), 'F', 'AB+'),
    ('gabriel.ramos', 'Gabriel', 'Ramos', 'gabriel.ramos@email.com', '09261234582', datetime(1991, 11, 22), 'M', 'O+'),
    ('valentina.silva', 'Valentina', 'Silva', 'valentina.silva@email.com', '09271234583', datetime(1996, 5, 9), 'F', 'A+'),
]

for username, fn, ln, email, phone, dob, gender, blood in data:
    user = User.objects.create_user(username=username, email=email, first_name=fn, last_name=ln, password='patient123')
    patient = Patient.objects.create(user=user, date_of_birth=dob, gender=gender, phone=phone, blood_type=blood)
    patients.append(patient)

print("Creating Doctors...")
doctors_data = [
    ('Sarah', 'Johnson', 'Dermatologist', 'LIC-DERM-2018-001', '09171234500', 'dr.sarah.johnson@clinic.com', 'Mon-Fri 9AM-5PM'),
    ('Michael', 'Chen', 'Ophthalmologist', 'LIC-OPTH-2015-002', '09281234501', 'dr.michael.chen@clinic.com', 'Mon-Sat 10AM-6PM'),
    ('Patricia', 'Rivera', 'Dermatologist', 'LIC-DERM-2019-003', '09391234502', 'dr.patricia.rivera@clinic.com', 'Tue-Sat 9AM-4PM'),
    ('David', 'Santos', 'Ophthalmologist', 'LIC-OPTH-2017-004', '09451234503', 'dr.david.santos@clinic.com', 'Mon-Fri 8AM-5PM'),
]

doctors = []
admin_user = User.objects.filter(is_superuser=True).first()
for first_name, last_name, specialization, license_num, phone, email, schedule in doctors_data:
    doctor = Doctor.objects.create(
        first_name=first_name,
        last_name=last_name,
        specialization=specialization,
        license_number=license_num,
        phone_number=phone,
        email=email,
        is_available=True,
        schedule_notes=schedule,
        created_by=admin_user
    )
    doctors.append(doctor)

print(f"Creating Bookings...")
# Track used date/time combinations to avoid duplicates
used_slots = set()

def get_unique_slot(base_date, time_choices):
    """Generate a unique date/time slot"""
    max_attempts = 50
    for _ in range(max_attempts):
        d = base_date + timedelta(days=random.randint(0, 30))
        t = datetime.strptime(random.choice(time_choices), '%H:%M').time()
        slot = (d, t)
        if slot not in used_slots:
            used_slots.add(slot)
            return d, t
    # Fallback: use a guaranteed unique timestamp
    return base_date, datetime.strptime(f'{random.randint(9, 16)}:00', '%H:%M').time()

# 12 past completed bookings
for i in range(12):
    p = random.choice(patients)
    s = random.choice(services)
    base_date = timezone.now().date() - timedelta(days=60)
    d, t = get_unique_slot(base_date, ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00'])
    doc = random.choice(doctors) if random.random() > 0.15 else None  # 85% chance to have a doctor
    Booking.objects.create(service=s, date=d, time=t, patient_name=p.user.get_full_name(),
                          patient_email=p.user.email, patient_phone=p.phone,
                          status='Completed', consultation_status='Done', doctor=doc)

# 8 upcoming confirmed appointments
for i in range(8):
    p = random.choice(patients)
    s = random.choice(services)
    base_date = timezone.now().date() + timedelta(days=1)
    d, t = get_unique_slot(base_date, ['09:00', '10:00', '11:00', '13:00', '14:00', '15:00', '16:00'])
    doc = random.choice(doctors) if random.random() > 0.15 else None  # 85% chance to have a doctor
    Booking.objects.create(service=s, date=d, time=t, patient_name=p.user.get_full_name(),
                          patient_email=p.user.email, patient_phone=p.phone,
                          status='Confirmed', consultation_status='Not Yet', doctor=doc)

# 5 pending appointments (awaiting confirmation)
for i in range(5):
    p = random.choice(patients)
    s = random.choice(services)
    base_date = timezone.now().date() + timedelta(days=7)
    d, t = get_unique_slot(base_date, ['09:00', '10:00', '11:00', '14:00', '15:00'])
    doc = random.choice(doctors) if random.random() > 0.25 else None  # 75% chance to have a doctor
    Booking.objects.create(service=s, date=d, time=t, patient_name=p.user.get_full_name(),
                          patient_email=p.user.email, patient_phone=p.phone,
                          status='Pending', consultation_status='Not Yet', doctor=doc)

# 3 cancelled appointments (for realistic data)
for i in range(3):
    p = random.choice(patients)
    s = random.choice(services)
    base_date = timezone.now().date() - timedelta(days=20)
    d, t = get_unique_slot(base_date, ['09:00', '10:00', '11:00', '14:00'])
    Booking.objects.create(service=s, date=d, time=t, patient_name=p.user.get_full_name(),
                          patient_email=p.user.email, patient_phone=p.phone,
                          status='Cancelled', consultation_status='Not Yet', doctor=None,
                          cancellation_reason='Patient requested cancellation')

print()
print("=" * 50)
print("ADDING COMPREHENSIVE TEST DATA")
print("=" * 50)

# ============================================================================
# MEDICAL RECORDS & PRESCRIPTIONS
# ============================================================================
print("\n📋 Creating Medical Records & Prescriptions...")

# First, create inventory items for medicines (needed for prescriptions)
medicines = []
medicine_data = [
    ('Tretinoin Cream 0.05%', 'Topical retinoid for acne treatment', Decimal('450.00'), date(2026, 12, 31), 50),
    ('Hydrocortisone 1%', 'Anti-inflammatory cream', Decimal('180.00'), date(2027, 3, 15), 100),
    ('Clindamycin Gel', 'Antibiotic gel for acne', Decimal('520.00'), date(2026, 9, 30), 40),
    ('Artificial Tears', 'Lubricating eye drops', Decimal('150.00'), date(2026, 6, 20), 150),
    ('Antibiotic Eye Drops', 'For bacterial eye infections', Decimal('280.00'), date(2026, 11, 10), 75),
    ('Vitamin C Serum', 'Brightening serum', Decimal('850.00'), date(2027, 1, 25), 30),
    ('Salicylic Acid Cleanser', 'Acne cleanser', Decimal('380.00'), date(2027, 4, 5), 60),
    ('Sunscreen SPF 50', 'Broad spectrum sunscreen', Decimal('650.00'), date(2026, 8, 18), 80),
]

for name, desc, price, expiry, stock_level in medicine_data:
    med = Inventory.objects.create(
        name=name,
        description=desc,
        price=price,
        category='Medicine',
        expiry_date=expiry,
        quantity=stock_level + random.randint(10, 50),
        stock=stock_level,
        status='In Stock'
    )
    medicines.append(med)

# Create medical records for completed bookings
completed_bookings = list(Booking.objects.filter(status='Completed'))
medical_records_created = 0

diagnoses = [
    ('Acne Vulgaris', 'Moderate acne breakouts on face', 'Comedones, papules, pustules on forehead and cheeks', 
     'Prescribed topical retinoid and antibiotic gel. Advised gentle cleansing routine.'),
    ('Contact Dermatitis', 'Allergic reaction to cosmetic product', 'Erythema and pruritus on facial area',
     'Advised to discontinue product. Prescribed anti-inflammatory cream.'),
    ('Dry Eye Syndrome', 'Patient reports eye dryness and irritation', 'Reduced tear production, mild conjunctival injection',
     'Prescribed artificial tears. Recommended environmental modifications.'),
    ('Conjunctivitis', 'Bacterial infection of eye', 'Red, watery eyes with discharge',
     'Prescribed antibiotic eye drops. Follow-up in 1 week.'),
    ('Melasma', 'Hyperpigmentation on face', 'Brown patches on cheeks and forehead',
     'Prescribed vitamin C serum and sunscreen. Advised sun protection.'),
    ('Seborrheic Dermatitis', 'Scalp and facial seborrhea', 'Flaky, scaly patches with mild erythema',
     'Prescribed medicated shampoo and topical treatment.'),
]

for i, booking in enumerate(completed_bookings[:8]):  # Create records for 8 completed bookings
    diagnosis_data = random.choice(diagnoses)
    
    # Find matching patient by email
    matching_patient = None
    for p in patients:
        if p.user.email == booking.patient_email:
            matching_patient = p
            break
    if not matching_patient:
        matching_patient = random.choice(patients)
    
    med_record = MedicalRecord.objects.create(
        patient=matching_patient,
        visit_date=timezone.make_aware(datetime.combine(booking.date, booking.time)),
        chief_complaint=diagnosis_data[1],
        symptoms=diagnosis_data[2],
        diagnosis=diagnosis_data[0],
        treatment_plan=diagnosis_data[3],
        additional_notes=f'Patient presented with {diagnosis_data[1].lower()}. Examination revealed {diagnosis_data[2].lower()}.',
        follow_up_date=booking.date + timedelta(days=random.randint(7, 30)),
        temperature=Decimal(random.uniform(36.5, 37.2)),
        blood_pressure_systolic=random.randint(110, 130),
        blood_pressure_diastolic=random.randint(70, 85),
        heart_rate=random.randint(60, 90),
        created_by=admin_user
    )
    medical_records_created += 1
    
    # Add 1-3 prescriptions per medical record
    num_prescriptions = random.randint(1, 3)
    for _ in range(num_prescriptions):
        medicine = random.choice(medicines)
        quantity = random.randint(1, 3)
        unit_price = medicine.price
        
        Prescription.objects.create(
            medical_record=med_record,
            medicine=medicine,
            quantity=quantity,
            dosage=random.choice([
                'Apply twice daily', 
                '1 drop 3 times daily',
                'Apply once at bedtime',
                'Use as needed',
                '1 application twice daily'
            ]),
            duration=random.choice(['7 days', '14 days', '1 month', '2 weeks']),
            instructions='Take as directed by physician. Complete full course.',
            unit_price=unit_price,
            total_price=unit_price * quantity,
            prescribed_by=admin_user,
            expiry_date=timezone.now().date() + timedelta(days=90),
            is_filled=random.choice([True, False])
        )

print(f"  ✅ Created {medical_records_created} medical records with prescriptions")

# ============================================================================
# BILLING & PAYMENTS
# ============================================================================
print("\n💰 Creating Billing Records & Payments...")

billing_records_created = 0
payments_created = 0

# Create billing for completed bookings
for booking in completed_bookings[:10]:
    service_fee = booking.service.price if booking.service else Decimal('800.00')
    medicine_fee = Decimal(random.randint(200, 1000))
    additional_fee = Decimal(random.choice([0, 0, 100, 200, 500]))
    discount = Decimal(random.choice([0, 0, 0, 50, 100, 200]))
    
    total = service_fee + medicine_fee + additional_fee - discount
    
    billing = Billing.objects.create(
        booking=booking,
        service_fee=service_fee,
        medicine_fee=medicine_fee,
        additional_fee=additional_fee,
        discount=discount,
        total_amount=total,
        notes='Regular billing' if additional_fee == 0 else 'Includes additional consultation fee',
        updated_by=admin_user
    )
    billing_records_created += 1
    
    # Create payments (some fully paid, some partial, some unpaid)
    payment_scenario = random.choice(['full', 'full', 'partial', 'unpaid'])
    
    if payment_scenario == 'full':
        # Single full payment
        Payment.objects.create(
            billing=billing,
            amount_paid=total,
            payment_method=random.choice(['Cash', 'GCash', 'Bank Transfer', 'Card']),
            reference_number=f'PAY-{random.randint(100000, 999999)}',
            notes='Full payment received',
            recorded_by=admin_user,
            is_verified=True,
            verified_by=admin_user,
            verified_at=timezone.now()
        )
        payments_created += 1
    elif payment_scenario == 'partial':
        # Partial payment
        partial_amount = total * Decimal('0.5')
        Payment.objects.create(
            billing=billing,
            amount_paid=partial_amount,
            payment_method='Cash',
            reference_number=f'PAY-{random.randint(100000, 999999)}',
            notes='Partial payment - balance due',
            recorded_by=admin_user,
            is_verified=True,
            verified_by=admin_user,
            verified_at=timezone.now()
        )
        payments_created += 1
    # 'unpaid' scenario: no payment records created

print(f"  ✅ Created {billing_records_created} billing records")
print(f"  ✅ Created {payments_created} payment transactions")

# ============================================================================
# INVENTORY ITEMS (Equipment & Miscellaneous)
# ============================================================================
print("\n📦 Creating Additional Inventory Items...")

equipment_data = [
    ('Dermatoscope', 'Digital skin examination tool', Decimal('15000.00'), None, 2, 1),
    ('Slit Lamp', 'Eye examination microscope', Decimal('45000.00'), None, 1, 1),
    ('Autoclave Sterilizer', 'Medical equipment sterilizer', Decimal('28000.00'), None, 1, 1),
    ('UV Lamp', 'For skin examination', Decimal('8500.00'), None, 2, 1),
    ('Cryotherapy Device', 'Liquid nitrogen applicator', Decimal('12000.00'), None, 1, 1),
]

misc_data = [
    ('Disposable Gloves (Box)', 'Latex-free examination gloves', Decimal('250.00'), None, 100, 20),
    ('Face Masks (Box)', 'Surgical masks', Decimal('180.00'), None, 150, 30),
    ('Alcohol Swabs (Box)', 'Antiseptic wipes', Decimal('120.00'), None, 80, 15),
    ('Cotton Rolls', 'Dental cotton rolls', Decimal('95.00'), None, 120, 25),
    ('Gauze Pads (Pack)', 'Sterile gauze', Decimal('150.00'), None, 90, 20),
    ('Medical Tape', 'Adhesive tape', Decimal('85.00'), None, 60, 15),
]

inventory_items = []

for name, desc, price, expiry, qty, stock in equipment_data:
    item = Inventory.objects.create(
        name=name,
        description=desc,
        price=price,
        category='Equipment',
        expiry_date=expiry,
        quantity=qty,
        stock=stock,
        status='In Stock'
    )
    inventory_items.append(item)

for name, desc, price, expiry, qty, stock in misc_data:
    item = Inventory.objects.create(
        name=name,
        description=desc,
        price=price,
        category='Miscellaneous',
        expiry_date=expiry,
        quantity=qty,
        stock=stock,
        status='In Stock'
    )
    inventory_items.append(item)

print(f"  ✅ Created {len(equipment_data)} equipment items")
print(f"  ✅ Created {len(misc_data)} miscellaneous items")

# ============================================================================
# STOCK TRANSACTIONS
# ============================================================================
print("\n📊 Creating Stock Transactions...")

transactions_created = 0

# Create stock-in transactions for all inventory items
all_inventory = list(Inventory.objects.all())
for item in all_inventory[:15]:  # Create transactions for first 15 items
    # Stock in transaction
    StockTransaction.objects.create(
        inventory_item=item,
        transaction_type='Stock In',
        quantity=random.randint(10, 50),
        performed_by=admin_user,
        notes=f'Initial stock-in for {item.name}',
        requires_approval=False,
        is_approved=True,
        approved_by=admin_user,
        approved_at=timezone.now()
    )
    transactions_created += 1
    
    # Some items have stock-out transactions
    if random.random() > 0.5:
        StockTransaction.objects.create(
            inventory_item=item,
            transaction_type='Stock Out',
            quantity=random.randint(1, 10),
            performed_by=admin_user,
            notes=f'Dispensed {item.name} to patient',
            requires_approval=False,
            is_approved=True,
            approved_by=admin_user,
            approved_at=timezone.now()
        )
        transactions_created += 1

# Create some pending approval transactions
for item in random.sample(all_inventory, min(3, len(all_inventory))):
    StockTransaction.objects.create(
        inventory_item=item,
        transaction_type='Stock Out',
        quantity=random.randint(5, 20),
        performed_by=admin_user,
        notes=f'Large quantity adjustment - requires approval',
        requires_approval=True,
        is_approved=False
    )
    transactions_created += 1

print(f"  ✅ Created {transactions_created} stock transactions")

# ============================================================================
# POS SALES
# ============================================================================
print("\n🛒 Creating POS Sales Transactions...")

pos_sales_created = 0
pos_items_created = 0

# Create walk-in sales
walk_in_names = [
    'John Doe', 'Jane Smith', 'Robert Brown', 'Emily Davis', 
    'Michael Wilson', 'Sarah Johnson', 'David Lee'
]

for i in range(5):
    sale = POSSale.objects.create(
        receipt_number=f'POS-{timezone.now().strftime("%Y%m%d")}-{random.randint(1000, 9999)}',
        sale_type='Walk-in',
        customer_name=random.choice(walk_in_names),
        discount_percent=Decimal(random.choice([0, 0, 5, 10])),
        tax_percent=Decimal('0.00'),
        payment_method=random.choice(['Cash', 'GCash', 'Card']),
        status='Completed',
        created_by=admin_user
    )
    pos_sales_created += 1
    
    # Add 1-4 items to the sale
    num_items = random.randint(1, 4)
    for _ in range(num_items):
        item = random.choice(medicines + inventory_items[:5])  # Select from medicines and some misc items
        qty = random.randint(1, 3)
        
        POSSaleItem.objects.create(
            sale=sale,
            inventory_item=item,
            quantity=qty,
            unit_price=item.price,
            line_total=item.price * qty
        )
        pos_items_created += 1

# Create patient sales
for i in range(3):
    patient = random.choice(patients)
    sale = POSSale.objects.create(
        receipt_number=f'POS-{timezone.now().strftime("%Y%m%d")}-{random.randint(1000, 9999)}',
        sale_type='Patient',
        patient=patient,
        customer_name=patient.user.get_full_name(),
        discount_percent=Decimal(random.choice([5, 10, 15])),  # Patients get more discount
        tax_percent=Decimal('0.00'),
        payment_method=random.choice(['Cash', 'GCash', 'Bank Transfer']),
        status='Completed',
        created_by=admin_user
    )
    pos_sales_created += 1
    
    # Add items
    num_items = random.randint(2, 5)
    for _ in range(num_items):
        item = random.choice(medicines)
        qty = random.randint(1, 2)
        
        POSSaleItem.objects.create(
            sale=sale,
            inventory_item=item,
            quantity=qty,
            unit_price=item.price,
            line_total=item.price * qty
        )
        pos_items_created += 1

print(f"  ✅ Created {pos_sales_created} POS sales")
print(f"  ✅ Created {pos_items_created} POS sale items")

# ============================================================================
# ACTIVITY LOGS
# ============================================================================
print("\n📝 Creating Activity Logs...")

activity_logs_created = 0

# Create sample activity logs
activities = [
    ('CREATE', 'Booking', 'Created new appointment for patient'),
    ('UPDATE', 'Patient', 'Updated patient profile information'),
    ('CREATE', 'MedicalRecord', 'Added medical record after consultation'),
    ('UPDATE', 'Billing', 'Updated billing amount'),
    ('CREATE', 'Payment', 'Processed payment transaction'),
    ('DELETE', 'Booking', 'Cancelled appointment'),
    ('CREATE', 'POSSale', 'Completed POS transaction'),
    ('UPDATE', 'Inventory', 'Adjusted inventory stock levels'),
    ('CREATE', 'Prescription', 'Added prescription to medical record'),
    ('VIEW', 'Patient', 'Viewed patient medical history'),
]

for action, model, description in activities:
    ActivityLog.objects.create(
        user=admin_user,
        action=action,
        model_name=model,
        object_id=random.randint(1, 50),
        description=description,
        ip_address='127.0.0.1'
    )
    activity_logs_created += 1

# Add login/logout logs
ActivityLog.objects.create(
    user=admin_user,
    action='LOGIN',
    model_name='User',
    object_id=admin_user.id,
    description='Admin user logged in',
    ip_address='127.0.0.1'
)
activity_logs_created += 1

print(f"  ✅ Created {activity_logs_created} activity log entries")

# ============================================================================
# CLINIC SETTINGS
# ============================================================================
print("\n⚙️  Creating Clinic Settings...")

# Delete existing settings (singleton model)
ClinicSettings.objects.all().delete()

ClinicSettings.objects.create(
    clinic_name='Romualdez Skin and Eye Clinic',
    clinic_address='123 Medical Center Drive, Quezon City, Metro Manila 1100',
    clinic_phone='+63 2 8123 4567',
    clinic_email='info@romualdez-clinic.com',
    opening_time='09:00',
    closing_time='17:00',
    appointment_slot_duration=60
)

print("  ✅ Configured clinic settings")

# ============================================================================
# ENHANCE PATIENT DATA
# ============================================================================
print("\n👥 Enhancing Patient Profiles...")

enhanced_patients = 0
allergies_list = [
    'Penicillin', 'Latex', 'None', 'Aspirin', 'Peanuts',
    'Shellfish', 'None', 'None', 'Sulfa drugs'
]

medical_histories = [
    'No significant medical history',
    'Hypertension, controlled with medication',
    'Type 2 Diabetes, diet-controlled',
    'Asthma, uses inhaler as needed',
    'Previous surgery: Appendectomy (2018)',
    'Seasonal allergies',
]

for patient in patients[:10]:  # Enhance first 10 patients
    patient.allergies = random.choice(allergies_list)
    patient.medical_history = random.choice(medical_histories)
    patient.current_medications = random.choice([
        'None',
        'Losartan 50mg once daily',
        'Metformin 500mg twice daily',
        'Multivitamins daily',
    ])
    patient.address = f'{random.randint(100, 999)} {random.choice(["Main", "Oak", "Pine", "Maple", "Cedar"])} Street, Quezon City'
    patient.emergency_contact_name = f'{random.choice(["Maria", "Juan", "Rosa", "Pedro"])} {random.choice(["Santos", "Cruz", "Reyes", "Garcia"])}'
    patient.emergency_contact_phone = f'09{random.randint(100000000, 999999999)}'
    patient.save()
    enhanced_patients += 1

print(f"  ✅ Enhanced {enhanced_patients} patient profiles")

print()
print("=" * 70)
print("✅ DATABASE SEEDED SUCCESSFULLY WITH COMPREHENSIVE TEST DATA!")
print("=" * 70)
print()
print("📊 DATABASE SUMMARY")
print("=" * 70)
print(f"👥 Users & Authentication:")
print(f"   - Admin Users: {User.objects.filter(is_superuser=True).count()}")
print(f"   - Patients: {Patient.objects.count()}")
print(f"   - Doctors: {Doctor.objects.count()}")
print()
print(f"📅 Appointments & Services:")
print(f"   - Services: {Service.objects.count()}")
print(f"   - Total Bookings: {Booking.objects.count()}")
print(f"     • Completed: {Booking.objects.filter(status='Completed').count()}")
print(f"     • Confirmed: {Booking.objects.filter(status='Confirmed').count()}")
print(f"     • Pending: {Booking.objects.filter(status='Pending').count()}")
print(f"     • Cancelled: {Booking.objects.filter(status='Cancelled').count()}")
print()
print(f"🏥 Medical Records:")
print(f"   - Medical Records: {MedicalRecord.objects.count()}")
print(f"   - Prescriptions: {Prescription.objects.count()}")
print(f"     • Filled: {Prescription.objects.filter(is_filled=True).count()}")
print(f"     • Pending: {Prescription.objects.filter(is_filled=False).count()}")
print()
print(f"💰 Billing & Payments:")
print(f"   - Billing Records: {Billing.objects.count()}")
print(f"   - Payments: {Payment.objects.count()}")
print(f"     • Paid Bills: {Billing.objects.filter(is_paid=True).count()}")
print(f"     • Unpaid Bills: {Billing.objects.filter(is_paid=False).count()}")
print()
print(f"📦 Inventory Management:")
print(f"   - Total Inventory Items: {Inventory.objects.count()}")
print(f"     • Medicines: {Inventory.objects.filter(category='Medicine').count()}")
print(f"     • Equipment: {Inventory.objects.filter(category='Equipment').count()}")
print(f"     • Miscellaneous: {Inventory.objects.filter(category='Miscellaneous').count()}")
print(f"   - Stock Transactions: {StockTransaction.objects.count()}")
print(f"     • Approved: {StockTransaction.objects.filter(is_approved=True).count()}")
print(f"     • Pending Approval: {StockTransaction.objects.filter(requires_approval=True, is_approved=False).count()}")
print()
print(f"🛒 Point of Sale:")
print(f"   - POS Sales: {POSSale.objects.count()}")
print(f"   - POS Sale Items: {POSSaleItem.objects.count()}")
print(f"     • Walk-in Sales: {POSSale.objects.filter(sale_type='Walk-in').count()}")
print(f"     • Patient Sales: {POSSale.objects.filter(sale_type='Patient').count()}")
print()
print(f"📝 System Logs:")
print(f"   - Activity Logs: {ActivityLog.objects.count()}")
print(f"   - Clinic Settings: {ClinicSettings.objects.count()} (configured)")
print()
print("=" * 70)
print("🔐 LOGIN CREDENTIALS")
print("=" * 70)
print("Admin Portal (Staff Login):")
print("  Username: admin")
print("  Password: admin123")
print()
print("Patient Portal (Sample Accounts - Password: patient123):")
print("  - maria.santos, juan.delacruz, ana.reyes, pedro.garcia")
print("  - rosa.martinez, carlos.lopez, elena.cruz, luis.fernandez")
print("  - sofia.ramirez, miguel.torres, clara.mendoza, diego.valencia")
print("  - isabela.morales, ricardo.castro, camila.ortiz, gabriel.ramos")
print("  - valentina.silva")
print()
print("=" * 70)
print("👨‍⚕️ MEDICAL STAFF")
print("=" * 70)
print("Doctors:")
print("  1. Dr. Sarah Johnson (Dermatologist)")
print("     License: LIC-DERM-2018-001 | Schedule: Mon-Fri 9AM-5PM")
print("  2. Dr. Michael Chen (Ophthalmologist)")
print("     License: LIC-OPTH-2015-002 | Schedule: Mon-Sat 10AM-6PM")
print("  3. Dr. Patricia Rivera (Dermatologist)")
print("     License: LIC-DERM-2019-003 | Schedule: Tue-Sat 9AM-4PM")
print("  4. Dr. David Santos (Ophthalmologist)")
print("     License: LIC-OPTH-2017-004 | Schedule: Mon-Fri 8AM-5PM")
print()
print("=" * 70)
print("🎯 MODULE COVERAGE")
print("=" * 70)
print("✅ Authentication & User Management")
print("✅ Patient Management")
print("✅ Doctor Management")
print("✅ Services & Bookings")
print("✅ Medical Records & Prescriptions")
print("✅ Billing & Payments")
print("✅ Inventory Management")
print("✅ Stock Transactions")
print("✅ Point of Sale (POS)")
print("✅ Activity Logging")
print("✅ Clinic Settings")
print()
print("=" * 70)
print("🌐 ACCESS THE SYSTEM")
print("=" * 70)
print("Local Server: http://127.0.0.1:8000/")
print("Admin Dashboard: http://127.0.0.1:8000/admin-dashboard/")
print("Patient Portal: http://127.0.0.1:8000/")
print()
print("=" * 70)
print("All modules are now fully populated with realistic test data!")
print("You can now test all features of the clinic management system.")
print("=" * 70)
