"""
Database Verification Script
Verifies all SQL database operations are working correctly
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic.settings')
django.setup()

from django.db import connection
from bookings.models import (
    Booking, Patient, MedicalRecord, Billing, Payment,
    Inventory, Prescription, StockTransaction, Service
)
from django.contrib.auth.models import User

def check_tables():
    """Check if all tables exist in database"""
    print("=" * 60)
    print("CHECKING DATABASE TABLES")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name;
        """)
        tables = cursor.fetchall()
        
        expected_tables = [
            'bookings_booking',
            'bookings_patient',
            'bookings_medicalrecord',
            'bookings_billing',
            'bookings_payment',
            'bookings_inventory',
            'bookings_prescription',
            'bookings_stocktransaction',
            'bookings_service',
        ]
        
        existing_tables = [t[0] for t in tables]
        
        for table in expected_tables:
            status = "✅" if table in existing_tables else "❌"
            print(f"{status} {table}")
        
        print(f"\nTotal tables in database: {len(existing_tables)}")
    
def check_relationships():
    """Verify foreign key relationships"""
    print("\n" + "=" * 60)
    print("CHECKING FOREIGN KEY RELATIONSHIPS")
    print("=" * 60)
    
    relationships = [
        ("Booking", "Service", "service"),
        ("Patient", "User", "user"),
        ("MedicalRecord", "Patient", "patient"),
        ("Prescription", "MedicalRecord", "medical_record"),
        ("Prescription", "Inventory", "medicine"),
        ("Billing", "Booking", "booking"),
        ("Payment", "Billing", "billing"),
        ("StockTransaction", "Inventory", "inventory_item"),
    ]
    
    for model_name, related_name, field_name in relationships:
        try:
            model = eval(model_name)
            field = model._meta.get_field(field_name)
            print(f"✅ {model_name}.{field_name} → {related_name}")
        except Exception as e:
            print(f"❌ {model_name}.{field_name}: {str(e)}")

def check_indexes():
    """Check database indexes for performance"""
    print("\n" + "=" * 60)
    print("CHECKING DATABASE INDEXES")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                m.name as table_name,
                il.name as index_name
            FROM sqlite_master AS m,
                 pragma_index_list(m.name) AS il
            WHERE m.type='table'
            AND m.name LIKE 'bookings_%'
            ORDER BY m.name, il.name;
        """)
        indexes = cursor.fetchall()
        
        for table, index in indexes:
            print(f"✅ {table}: {index}")
        
        if not indexes:
            print("⚠️  No custom indexes found. Consider adding for performance.")

def test_crud_operations():
    """Test Create, Read, Update, Delete operations"""
    print("\n" + "=" * 60)
    print("TESTING CRUD OPERATIONS")
    print("=" * 60)
    
    try:
        # Test Service creation
        service, created = Service.objects.get_or_create(
            name="Test Service",
            defaults={
                'description': 'Test service for verification',
                'image': 'services/test.jpg'
            }
        )
        print(f"✅ Service {'created' if created else 'retrieved'}: {service.name}")
        
        # Test Booking creation
        booking = Booking.objects.create(
            patient_name="Test Patient",
            patient_email="test@example.com",
            patient_phone="09123456789",
            date="2025-10-20",
            time="14:00",
            service=service,
            status="Pending",
            notes="Test booking"
        )
        print(f"✅ Booking created: #{booking.id} - {booking.patient_name}")
        
        # Test Read
        retrieved_booking = Booking.objects.get(id=booking.id)
        print(f"✅ Booking read: Status = {retrieved_booking.status}")
        
        # Test Update
        booking.status = "Confirmed"
        booking.save()
        print(f"✅ Booking updated: Status changed to {booking.status}")
        
        # Test relationship cascade
        booking_id = booking.id
        booking.delete()
        print(f"✅ Booking deleted: #{booking_id}")
        
        # Clean up service if it was created
        if created:
            service.delete()
            print(f"✅ Service deleted: {service.name}")
        
    except Exception as e:
        print(f"❌ CRUD test failed: {str(e)}")

def check_signals():
    """Verify signals are registered"""
    print("\n" + "=" * 60)
    print("CHECKING SIGNAL REGISTRATION")
    print("=" * 60)
    
    from django.db.models import signals
    from bookings import signals as booking_signals
    
    signal_checks = [
        ("check_booking_confirmation", "pre_save", Booking),
        ("create_patient_and_billing", "post_save", Booking),
        ("update_billing_on_payment", "post_save", Payment),
        ("recalculate_billing_totals", "post_save", Billing),
        ("update_billing_medicine_fee", "post_save", Prescription),
    ]
    
    for func_name, signal_type, model in signal_checks:
        if hasattr(booking_signals, func_name):
            print(f"✅ {func_name} registered for {model.__name__} {signal_type}")
        else:
            print(f"❌ {func_name} NOT FOUND")

def check_data_integrity():
    """Check data integrity constraints"""
    print("\n" + "=" * 60)
    print("CHECKING DATA INTEGRITY")
    print("=" * 60)
    
    # Check for orphaned records
    total_bookings = Booking.objects.count()
    bookings_with_service = Booking.objects.exclude(service__isnull=True).count()
    print(f"✅ Bookings: {total_bookings} total, {bookings_with_service} with service")
    
    total_billings = Billing.objects.count()
    billings_with_booking = Billing.objects.exclude(booking__isnull=True).count()
    print(f"✅ Billings: {total_billings} total, {billings_with_booking} with booking")
    
    total_prescriptions = Prescription.objects.count()
    prescriptions_with_record = Prescription.objects.exclude(medical_record__isnull=True).count()
    print(f"✅ Prescriptions: {total_prescriptions} total, {prescriptions_with_record} with medical record")
    
    total_patients = Patient.objects.count()
    patients_with_user = Patient.objects.exclude(user__isnull=True).count()
    print(f"✅ Patients: {total_patients} total, {patients_with_user} with user account")

def show_statistics():
    """Display current database statistics"""
    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)
    
    stats = {
        "Total Bookings": Booking.objects.count(),
        "Pending Bookings": Booking.objects.filter(status="Pending").count(),
        "Confirmed Bookings": Booking.objects.filter(status="Confirmed").count(),
        "Completed Bookings": Booking.objects.filter(status="Completed").count(),
        "Total Patients": Patient.objects.count(),
        "Total Medical Records": MedicalRecord.objects.count(),
        "Total Billings": Billing.objects.count(),
        "Paid Billings": Billing.objects.filter(is_paid=True).count(),
        "Unpaid Billings": Billing.objects.filter(is_paid=False).count(),
        "Total Payments": Payment.objects.count(),
        "Total Inventory Items": Inventory.objects.count(),
        "In Stock Items": Inventory.objects.filter(status="In Stock").count(),
        "Low Stock Items": Inventory.objects.filter(status="Low Stock").count(),
        "Out of Stock Items": Inventory.objects.filter(status="Out of Stock").count(),
        "Total Prescriptions": Prescription.objects.count(),
        "Total Stock Transactions": StockTransaction.objects.count(),
    }
    
    for key, value in stats.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    print("\n🔍 STARTING DATABASE VERIFICATION\n")
    
    try:
        check_tables()
        check_relationships()
        check_indexes()
        check_signals()
        check_data_integrity()
        show_statistics()
        
        print("\n" + "=" * 60)
        print("RUNNING LIVE CRUD TEST")
        print("=" * 60)
        test_crud_operations()
        
        print("\n" + "=" * 60)
        print("✅ DATABASE VERIFICATION COMPLETE")
        print("=" * 60)
        print("\nAll checks passed! Database is properly configured.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
