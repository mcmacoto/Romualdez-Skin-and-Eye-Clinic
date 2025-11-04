"""
Django management command to reset database and seed with realistic test data.
Preserves superuser accounts while clearing all other data.
Usage: python manage.py reset_and_seed
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.apps import apps
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from datetime import timedelta


class Command(BaseCommand):
    help = 'Reset database (preserve superusers) and seed with realistic test data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting reset_and_seed: preserving superusers...'))
        
        # Step 1: Preserve superusers
        superusers = list(User.objects.filter(is_superuser=True).values_list('username', flat=True))
        self.stdout.write(self.style.SUCCESS(f'Preserved superusers: {", ".join(superusers)}'))
        
        # Step 2: Delete data in correct order (respecting foreign keys)
        self._clear_database()
        
        # Step 3: Create realistic test data
        self.stdout.write(self.style.WARNING('Creating realistic test data...'))
        with transaction.atomic():
            self._seed_database()
        
        self.stdout.write(self.style.SUCCESS('Reset and seed finished.'))

    def _clear_database(self):
        """Delete all data except superusers, respecting foreign key constraints"""
        
        # Get the bookings app config
        bookings_app = apps.get_app_config('bookings')
        
        # Define deletion order (child tables first, then parents)
        models_to_clear = [
            'POSSaleItem',
            'POSSale',
            'Payment',
            'Billing',
            'MedicalImage',
            'MedicalRecord',
            'Patient',
            'StockTransaction',
            'Inventory',
            'Prescription',
            'Booking',
            'Appointment',
            'Service',
        ]
        
        # Delete in order
        for model_name in models_to_clear:
            try:
                model = bookings_app.get_model(model_name)
                count = model.objects.all().delete()[0]
                if count > 0:
                    self.stdout.write(f'Deleted {count} objects from {model_name}')
            except LookupError:
                # Model doesn't exist (e.g., optional models)
                pass
        
        # Delete any remaining models in bookings app
        for model in bookings_app.get_models():
            if model._meta.model_name not in [m.lower() for m in models_to_clear]:
                count = model.objects.all().delete()[0]
                if count > 0:
                    self.stdout.write(f'Deleted {count} objects from {model._meta.model_name}')
        
        # Delete non-superuser users
        non_superusers = User.objects.filter(is_superuser=False)
        count = non_superusers.count()
        non_superusers.delete()
        self.stdout.write(f'Deleted {count} non-superuser user accounts')

    def _seed_database(self):
        """Create realistic test data across all modules"""
        
        # Import models
        from bookings.models import (
            Service, Patient, Booking, Appointment,
            MedicalRecord, Billing, Payment, Inventory, StockTransaction
        )
        
        # Try to import POS models (optional)
        try:
            from bookings.models import POSSale, POSSaleItem
            has_pos = True
        except ImportError:
            has_pos = False
        
        now = timezone.now()
        
        # === STAFF USERS ===
        staff_user = User.objects.create_user(
            username='staff_clinic',
            email='staff@clinic.local',
            password='clinic2025',
            first_name='Maria',
            last_name='Santos',
            is_staff=True
        )
        
        nurse_user = User.objects.create_user(
            username='nurse_ana',
            email='nurse@clinic.local',
            password='clinic2025',
            first_name='Ana',
            last_name='Cruz',
            is_staff=True
        )
        
        # === SERVICES ===
        service_consult = Service.objects.create(
            name='General Consultation',
            description='General medical consultation with physical examination',
            price=Decimal('500.00')
        )
        
        service_derma = Service.objects.create(
            name='Dermatology Consultation',
            description='Skin condition assessment and treatment',
            price=Decimal('800.00')
        )
        
        service_eye = Service.objects.create(
            name='Eye Checkup',
            description='Comprehensive eye examination',
            price=Decimal('600.00')
        )
        
        # === PATIENT USERS & PROFILES ===
        # Patient 1: Jane Smith (has completed consultation with records)
        user1 = User.objects.create_user(
            username='jane.smith',
            email='jane.smith@example.com',
            password='patient123',
            first_name='Jane',
            last_name='Smith'
        )
        patient1 = Patient.objects.create(
            user=user1,
            date_of_birth=timezone.datetime(1990, 5, 15).date(),
            gender='F',
            phone='+639171234567',
            address='123 Main St, Manila',
            blood_type='O+',
            allergies='Penicillin',
            emergency_contact_name='John Smith',
            emergency_contact_phone='+639171234568'
        )
        
        # Patient 2: John Doe (has pending appointment)
        user2 = User.objects.create_user(
            username='john.doe',
            email='john.doe@example.com',
            password='patient123',
            first_name='John',
            last_name='Doe'
        )
        patient2 = Patient.objects.create(
            user=user2,
            date_of_birth=timezone.datetime(1985, 8, 22).date(),
            gender='M',
            phone='+639181234567',
            address='456 Rizal Ave, Quezon City',
            blood_type='A+',
            allergies='None',
            emergency_contact_name='Mary Doe',
            emergency_contact_phone='+639181234568'
        )
        
        # Patient 3: Maria Rosa (has confirmed appointment)
        user3 = User.objects.create_user(
            username='maria.rosa',
            email='maria.rosa@example.com',
            password='patient123',
            first_name='Maria',
            last_name='Rosa'
        )
        patient3 = Patient.objects.create(
            user=user3,
            date_of_birth=timezone.datetime(1995, 3, 10).date(),
            gender='F',
            phone='+639191234567',
            address='789 Quezon Blvd, Makati',
            blood_type='B+',
            allergies='Shellfish',
            emergency_contact_name='Pedro Rosa',
            emergency_contact_phone='+639191234568'
        )
        
        # Patient 4: Alex Tan (cancelled appointment)
        user4 = User.objects.create_user(
            username='alex.tan',
            email='alex.tan@example.com',
            password='patient123',
            first_name='Alex',
            last_name='Tan'
        )
        patient4 = Patient.objects.create(
            user=user4,
            date_of_birth=timezone.datetime(1988, 11, 30).date(),
            gender='M',
            phone='+639201234567',
            address='321 Taft Ave, Pasay',
            blood_type='AB+',
            allergies='None',
            emergency_contact_name='Lisa Tan',
            emergency_contact_phone='+639201234568'
        )
        
        # Patient 5: Linda Garcia (ongoing consultation)
        user5 = User.objects.create_user(
            username='linda.garcia',
            email='linda.garcia@example.com',
            password='patient123',
            first_name='Linda',
            last_name='Garcia'
        )
        patient5 = Patient.objects.create(
            user=user5,
            date_of_birth=timezone.datetime(1992, 7, 5).date(),
            gender='F',
            phone='+639211234567',
            address='654 Espana Blvd, Manila',
            blood_type='O-',
            allergies='Latex',
            emergency_contact_name='Carlos Garcia',
            emergency_contact_phone='+639211234568'
        )
        
        # Patient 6: Robert Chen (has unpaid bill)
        user6 = User.objects.create_user(
            username='robert.chen',
            email='robert.chen@example.com',
            password='patient123',
            first_name='Robert',
            last_name='Chen'
        )
        patient6 = Patient.objects.create(
            user=user6,
            date_of_birth=timezone.datetime(1987, 2, 18).date(),
            gender='M',
            phone='+639221234567',
            address='789 Shaw Blvd, Mandaluyong',
            blood_type='A-',
            allergies='Dust, Pollen',
            emergency_contact_name='Susan Chen',
            emergency_contact_phone='+639221234568'
        )
        
        # Patient 7: Sarah Lopez (partially paid bill)
        user7 = User.objects.create_user(
            username='sarah.lopez',
            email='sarah.lopez@example.com',
            password='patient123',
            first_name='Sarah',
            last_name='Lopez'
        )
        patient7 = Patient.objects.create(
            user=user7,
            date_of_birth=timezone.datetime(1993, 9, 25).date(),
            gender='F',
            phone='+639231234567',
            address='456 Ortigas Ave, Pasig',
            blood_type='B-',
            allergies='None',
            emergency_contact_name='Miguel Lopez',
            emergency_contact_phone='+639231234568'
        )
        
        # Patient 8: David Kim (multiple visits)
        user8 = User.objects.create_user(
            username='david.kim',
            email='david.kim@example.com',
            password='patient123',
            first_name='David',
            last_name='Kim'
        )
        patient8 = Patient.objects.create(
            user=user8,
            date_of_birth=timezone.datetime(1980, 12, 8).date(),
            gender='M',
            phone='+639241234567',
            address='321 EDSA, Makati',
            blood_type='AB-',
            allergies='Aspirin',
            emergency_contact_name='Rachel Kim',
            emergency_contact_phone='+639241234568'
        )
        
        # Patient 9: Emily Reyes (upcoming appointment next week)
        user9 = User.objects.create_user(
            username='emily.reyes',
            email='emily.reyes@example.com',
            password='patient123',
            first_name='Emily',
            last_name='Reyes'
        )
        patient9 = Patient.objects.create(
            user=user9,
            date_of_birth=timezone.datetime(1998, 4, 14).date(),
            gender='F',
            phone='+639251234567',
            address='123 Commonwealth Ave, Quezon City',
            blood_type='O+',
            allergies='Seafood',
            emergency_contact_name='Antonio Reyes',
            emergency_contact_phone='+639251234568'
        )
        
        # Patient 10: Mark Santos (new patient, first appointment)
        user10 = User.objects.create_user(
            username='mark.santos',
            email='mark.santos@example.com',
            password='patient123',
            first_name='Mark',
            last_name='Santos'
        )
        patient10 = Patient.objects.create(
            user=user10,
            date_of_birth=timezone.datetime(1991, 6, 20).date(),
            gender='M',
            phone='+639261234567',
            address='987 Katipunan Ave, Quezon City',
            blood_type='A+',
            allergies='Peanuts',
            emergency_contact_name='Anna Santos',
            emergency_contact_phone='+639261234568'
        )

        
        # === BOOKINGS (various statuses and dates) ===
        # Booking 1: Jane - Completed (3 days ago)
        booking1 = Booking.objects.create(
            patient_name=f'{user1.first_name} {user1.last_name}',
            patient_email=user1.email,
            patient_phone=patient1.phone,
            service=service_consult,
            date=now.date() - timedelta(days=3),
            time=timezone.datetime.strptime('10:00', '%H:%M').time(),
            status='Confirmed',
            consultation_status='Done',
            created_by=staff_user
        )
        
        # Booking 2: John - Pending (tomorrow)
        booking2 = Booking.objects.create(
            patient_name=f'{user2.first_name} {user2.last_name}',
            patient_email=user2.email,
            patient_phone=patient2.phone,
            service=service_derma,
            date=now.date() + timedelta(days=1),
            time=timezone.datetime.strptime('14:00', '%H:%M').time(),
            status='Pending',
            consultation_status='Not Yet',
            created_by=staff_user
        )
        
        # Booking 3: Maria - Confirmed (in 5 days)
        booking3 = Booking.objects.create(
            patient_name=f'{user3.first_name} {user3.last_name}',
            patient_email=user3.email,
            patient_phone=patient3.phone,
            service=service_eye,
            date=now.date() + timedelta(days=5),
            time=timezone.datetime.strptime('09:00', '%H:%M').time(),
            status='Confirmed',
            consultation_status='Not Yet',
            created_by=staff_user
        )
        
        # Booking 4: Alex - Cancelled (was for yesterday)
        booking4 = Booking.objects.create(
            patient_name=f'{user4.first_name} {user4.last_name}',
            patient_email=user4.email,
            patient_phone=patient4.phone,
            service=service_consult,
            date=now.date() - timedelta(days=1),
            time=timezone.datetime.strptime('11:00', '%H:%M').time(),
            status='Cancelled',
            consultation_status='Not Yet',
            cancellation_reason='Patient requested cancellation - scheduling conflict',
            created_by=staff_user
        )
        
        # Booking 5: Linda - Ongoing (today)
        booking5 = Booking.objects.create(
            patient_name=f'{user5.first_name} {user5.last_name}',
            patient_email=user5.email,
            patient_phone=patient5.phone,
            service=service_derma,
            date=now.date(),
            time=timezone.datetime.strptime('15:00', '%H:%M').time(),
            status='Confirmed',
            consultation_status='Ongoing',
            created_by=staff_user
        )
        
        # Booking 6: Robert - Completed (2 weeks ago, unpaid)
        booking6 = Booking.objects.create(
            patient_name=f'{user6.first_name} {user6.last_name}',
            patient_email=user6.email,
            patient_phone=patient6.phone,
            service=service_eye,
            date=now.date() - timedelta(days=14),
            time=timezone.datetime.strptime('11:00', '%H:%M').time(),
            status='Confirmed',
            consultation_status='Done',
            created_by=staff_user
        )
        
        # Booking 7: Sarah - Completed (1 week ago, partially paid)
        booking7 = Booking.objects.create(
            patient_name=f'{user7.first_name} {user7.last_name}',
            patient_email=user7.email,
            patient_phone=patient7.phone,
            service=service_derma,
            date=now.date() - timedelta(days=7),
            time=timezone.datetime.strptime('13:00', '%H:%M').time(),
            status='Confirmed',
            consultation_status='Done',
            created_by=staff_user
        )
        
        # Booking 8: David - Completed (1 month ago, paid)
        booking8 = Booking.objects.create(
            patient_name=f'{user8.first_name} {user8.last_name}',
            patient_email=user8.email,
            patient_phone=patient8.phone,
            service=service_consult,
            date=now.date() - timedelta(days=30),
            time=timezone.datetime.strptime('10:30', '%H:%M').time(),
            status='Confirmed',
            consultation_status='Done',
            created_by=staff_user
        )
        
        # Booking 9: Emily - Confirmed (next week)
        booking9 = Booking.objects.create(
            patient_name=f'{user9.first_name} {user9.last_name}',
            patient_email=user9.email,
            patient_phone=patient9.phone,
            service=service_eye,
            date=now.date() + timedelta(days=7),
            time=timezone.datetime.strptime('09:30', '%H:%M').time(),
            status='Confirmed',
            consultation_status='Not Yet',
            created_by=staff_user
        )
        
        # Booking 10: Mark - Pending (3 days from now)
        booking10 = Booking.objects.create(
            patient_name=f'{user10.first_name} {user10.last_name}',
            patient_email=user10.email,
            patient_phone=patient10.phone,
            service=service_consult,
            date=now.date() + timedelta(days=3),
            time=timezone.datetime.strptime('14:30', '%H:%M').time(),
            status='Pending',
            consultation_status='Not Yet',
            created_by=staff_user
        )

        
        # === MEDICAL RECORDS (for completed bookings) ===
        medical_record1 = MedicalRecord.objects.create(
            patient=patient1,
            visit_date=timezone.make_aware(
                timezone.datetime.combine(
                    now.date() - timedelta(days=3),
                    timezone.datetime.strptime('10:00', '%H:%M').time()
                )
            ),
            chief_complaint='Sore throat and persistent cough',
            symptoms='Sore throat, cough, mild fever',
            diagnosis='Acute Upper Respiratory Tract Infection',
            treatment_plan='Prescribed antibiotics and rest for 5 days. Advised to return if symptoms persist.',
            temperature=Decimal('37.8'),
            blood_pressure_systolic=120,
            blood_pressure_diastolic=80,
            heart_rate=72,
            weight=Decimal('58.5'),
            height=Decimal('165.0'),
            additional_notes='Patient responded well to examination. No complications observed.',
            created_by=staff_user
        )
        
        # Medical Record 2: Robert (Eye checkup)
        medical_record2 = MedicalRecord.objects.create(
            patient=patient6,
            visit_date=timezone.make_aware(
                timezone.datetime.combine(
                    now.date() - timedelta(days=14),
                    timezone.datetime.strptime('11:00', '%H:%M').time()
                )
            ),
            chief_complaint='Blurred vision and eye strain',
            symptoms='Difficulty reading, eye fatigue, headaches',
            diagnosis='Myopia (Nearsightedness)',
            treatment_plan='Prescribed corrective eyeglasses. Recommended computer screen breaks every 20 minutes.',
            temperature=Decimal('36.5'),
            blood_pressure_systolic=118,
            blood_pressure_diastolic=78,
            heart_rate=68,
            weight=Decimal('72.0'),
            height=Decimal('175.0'),
            additional_notes='Vision test shows -2.00 diopters both eyes. No other complications.',
            created_by=staff_user
        )
        
        # Medical Record 3: Sarah (Dermatology)
        medical_record3 = MedicalRecord.objects.create(
            patient=patient7,
            visit_date=timezone.make_aware(
                timezone.datetime.combine(
                    now.date() - timedelta(days=7),
                    timezone.datetime.strptime('13:00', '%H:%M').time()
                )
            ),
            chief_complaint='Skin rash and itching',
            symptoms='Red itchy rash on arms and neck',
            diagnosis='Contact Dermatitis',
            treatment_plan='Topical corticosteroid cream, antihistamines. Avoid known allergens.',
            temperature=Decimal('36.8'),
            blood_pressure_systolic=115,
            blood_pressure_diastolic=75,
            heart_rate=70,
            weight=Decimal('62.0'),
            height=Decimal('160.0'),
            additional_notes='Likely reaction to new laundry detergent. Advised to switch brands.',
            created_by=staff_user
        )
        
        # Medical Record 4: David (General consultation)
        medical_record4 = MedicalRecord.objects.create(
            patient=patient8,
            visit_date=timezone.make_aware(
                timezone.datetime.combine(
                    now.date() - timedelta(days=30),
                    timezone.datetime.strptime('10:30', '%H:%M').time()
                )
            ),
            chief_complaint='Annual health checkup',
            symptoms='No specific symptoms, routine checkup',
            diagnosis='Healthy - No significant issues',
            treatment_plan='Continue healthy lifestyle. Scheduled follow-up in 1 year.',
            temperature=Decimal('36.6'),
            blood_pressure_systolic=122,
            blood_pressure_diastolic=82,
            heart_rate=74,
            weight=Decimal('78.5'),
            height=Decimal('178.0'),
            additional_notes='All vital signs normal. Blood work results within normal range.',
            created_by=staff_user
        )

        
        # === BILLING & PAYMENT ===
        # Billing 1: Jane - Fully paid
        billing1 = Billing.objects.create(
            booking=booking1,
            service_fee=service_consult.price,
            medicine_fee=Decimal('150.00'),
            additional_fee=Decimal('0.00'),
            discount=Decimal('0.00'),
            total_amount=Decimal('650.00'),
            is_paid=True,
            amount_paid=Decimal('650.00'),
            balance=Decimal('0.00'),
            updated_by=staff_user
        )
        
        payment1 = Payment.objects.create(
            billing=billing1,
            amount_paid=Decimal('650.00'),
            payment_method='Cash',
            reference_number='PAY-2025-001',
            notes='Full payment received',
            recorded_by=staff_user,
            is_verified=True,
            verified_by=staff_user,
            verified_at=now
        )
        
        # Billing 2: Robert - Unpaid
        billing2 = Billing.objects.create(
            booking=booking6,
            service_fee=service_eye.price,
            medicine_fee=Decimal('200.00'),
            additional_fee=Decimal('0.00'),
            discount=Decimal('0.00'),
            total_amount=Decimal('800.00'),
            is_paid=False,
            amount_paid=Decimal('0.00'),
            balance=Decimal('800.00'),
            updated_by=staff_user
        )
        
        # Billing 3: Sarah - Partially paid
        billing3 = Billing.objects.create(
            booking=booking7,
            service_fee=service_derma.price,
            medicine_fee=Decimal('300.00'),
            additional_fee=Decimal('0.00'),
            discount=Decimal('50.00'),
            total_amount=Decimal('1050.00'),
            is_paid=False,
            amount_paid=Decimal('500.00'),
            balance=Decimal('550.00'),
            updated_by=staff_user
        )
        
        payment2 = Payment.objects.create(
            billing=billing3,
            amount_paid=Decimal('500.00'),
            payment_method='GCash',
            reference_number='GCASH-2025-042',
            notes='Initial payment - balance to be paid next visit',
            recorded_by=staff_user,
            is_verified=True,
            verified_by=staff_user,
            verified_at=now - timedelta(days=7)
        )
        
        # Billing 4: David - Fully paid
        billing4 = Billing.objects.create(
            booking=booking8,
            service_fee=service_consult.price,
            medicine_fee=Decimal('0.00'),
            additional_fee=Decimal('100.00'),
            discount=Decimal('0.00'),
            total_amount=Decimal('600.00'),
            is_paid=True,
            amount_paid=Decimal('600.00'),
            balance=Decimal('0.00'),
            updated_by=staff_user
        )
        
        payment3 = Payment.objects.create(
            billing=billing4,
            amount_paid=Decimal('600.00'),
            payment_method='Credit Card',
            reference_number='CC-2025-128',
            notes='Full payment via Visa',
            recorded_by=staff_user,
            is_verified=True,
            verified_by=staff_user,
            verified_at=now - timedelta(days=30)
        )

        
        # === INVENTORY ITEMS ===
        inv1 = Inventory.objects.create(
            name='Paracetamol 500mg',
            description='Pain reliever and fever reducer',
            category='Medicine',
            quantity=500,
            stock=100,
            price=Decimal('5.00'),
            expiry_date=(now + timedelta(days=365)).date()
        )
        
        inv2 = Inventory.objects.create(
            name='Sunscreen SPF50',
            description='Dermatologist-recommended sunscreen',
            category='Miscellaneous',
            quantity=50,
            stock=20,
            price=Decimal('450.00'),
            expiry_date=(now + timedelta(days=730)).date()
        )
        
        inv3 = Inventory.objects.create(
            name='Ophthalmic Drops',
            description='Eye lubricant drops',
            category='Medicine',
            quantity=30,
            stock=10,
            price=Decimal('120.00'),
            expiry_date=(now + timedelta(days=180)).date()
        )
        
        inv4 = Inventory.objects.create(
            name='Sterile Gauze Pack',
            description='Sterile gauze for wound dressing',
            category='Equipment',
            quantity=200,
            stock=50,
            price=Decimal('15.00'),
            expiry_date=(now + timedelta(days=1095)).date()
        )
        
        # === STOCK TRANSACTIONS ===
        StockTransaction.objects.create(
            inventory_item=inv1,
            transaction_type='Stock In',
            quantity=500,
            notes='Initial stock - bulk purchase',
            performed_by=staff_user,
            is_approved=True,
            approved_by=staff_user,
            approved_at=now - timedelta(days=10)
        )
        
        StockTransaction.objects.create(
            inventory_item=inv2,
            transaction_type='Stock In',
            quantity=50,
            notes='Monthly restock',
            performed_by=staff_user,
            is_approved=True,
            approved_by=staff_user,
            approved_at=now - timedelta(days=7)
        )
        
        StockTransaction.objects.create(
            inventory_item=inv3,
            transaction_type='Stock In',
            quantity=30,
            notes='Emergency restock',
            performed_by=nurse_user,
            is_approved=True,
            approved_by=staff_user,
            approved_at=now - timedelta(days=5)
        )
        
        StockTransaction.objects.create(
            inventory_item=inv4,
            transaction_type='Stock In',
            quantity=200,
            notes='Quarterly supply order',
            performed_by=staff_user,
            is_approved=True,
            approved_by=staff_user,
            approved_at=now - timedelta(days=15)
        )
        
        # === POS SALE (if POS module exists) ===
        if has_pos:
            pos_sale = POSSale.objects.create(
                customer_name='Walk-in Customer',
                sale_type='Walk-in',
                subtotal=Decimal('460.00'),
                discount_percent=Decimal('0.00'),
                discount_amount=Decimal('0.00'),
                tax_percent=Decimal('0.00'),
                tax_amount=Decimal('0.00'),
                total_amount=Decimal('460.00'),
                payment_method='Cash',
                amount_received=Decimal('500.00'),
                change_amount=Decimal('40.00'),
                status='Completed',
                created_by=staff_user
            )
            
            POSSaleItem.objects.create(
                sale=pos_sale,
                inventory_item=inv1,
                quantity=2,
                unit_price=inv1.price,
                line_total=Decimal('10.00')
            )
            
            POSSaleItem.objects.create(
                sale=pos_sale,
                inventory_item=inv2,
                quantity=1,
                unit_price=inv2.price,
                line_total=Decimal('450.00')
            )
        
        # === SUMMARY ===
        self.stdout.write(self.style.SUCCESS('Seeding complete:'))
        self.stdout.write(f'  Staff created: 2 ({staff_user.username}, {nurse_user.username})')
        self.stdout.write(f'  Patients created: 10 (jane.smith, john.doe, maria.rosa, alex.tan, linda.garcia, robert.chen, sarah.lopez, david.kim, emily.reyes, mark.santos)')
        self.stdout.write(f'  Services created: {Service.objects.count()}')
        self.stdout.write(f'  Bookings created: {Booking.objects.count()} (various statuses: Pending, Confirmed, Cancelled, Done, Ongoing)')
        self.stdout.write(f'  Medical records: {MedicalRecord.objects.count()}')
        self.stdout.write(f'  Billings created: {Billing.objects.count()} (2 fully paid, 1 partially paid, 1 unpaid)')
        self.stdout.write(f'  Payments created: {Payment.objects.count()}')
        self.stdout.write(f'  Inventory items: {Inventory.objects.count()}')
        self.stdout.write(f'  Stock transactions: {StockTransaction.objects.count()}')
        if has_pos:
            self.stdout.write(f'  POS sales: {POSSale.objects.count()}')

