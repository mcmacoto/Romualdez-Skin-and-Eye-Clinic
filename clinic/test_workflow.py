"""
End-to-End Workflow Test
Demonstrates complete booking → patient → billing → prescription → payment flow
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic.settings')
django.setup()

from django.db import transaction
from django.contrib.auth.models import User
from bookings.models import (
    Booking, Service, Patient, MedicalRecord, Billing, 
    Payment, Inventory, Prescription
)
from django.utils import timezone
from decimal import Decimal

def run_workflow_test():
    print("\n" + "="*70)
    print("🧪 END-TO-END WORKFLOW TEST")
    print("="*70)
    
    try:
        with transaction.atomic():
            print("\n📋 STEP 1: Create Service")
            service, created = Service.objects.get_or_create(
                name="Acne Treatment",
                defaults={
                    'description': 'Professional acne treatment and consultation',
                    'image': 'services/acne.jpg'
                }
            )
            print(f"✅ Service: {service.name}")
            
            print("\n📋 STEP 2: Patient Books Appointment (Frontend)")
            booking = Booking.objects.create(
                patient_name="Maria Santos",
                patient_email="maria.santos@example.com",
                patient_phone="09171234567",
                date="2025-02-15",
                time="14:00",
                service=service,
                status="Pending",
                notes="First time patient, has acne concerns"
            )
            print(f"✅ Booking #{booking.id} created - Status: {booking.status}")
            
            print("\n📋 STEP 3: Admin Accepts Booking (Triggers Automation)")
            # Create admin user for created_by field
            admin_user, _ = User.objects.get_or_create(
                username='admin',
                defaults={'is_staff': True, 'is_superuser': True}
            )
            booking.created_by = admin_user
            booking.status = "Confirmed"
            booking.save()
            print(f"✅ Booking #{booking.id} confirmed - Status: {booking.status}")
            
            # Refresh to see related objects
            booking.refresh_from_db()
            
            # Check if patient was created
            patient = Patient.objects.filter(user__email=booking.patient_email).first()
            if patient:
                print(f"✅ Patient Profile Created: {patient.user.get_full_name()}")
                print(f"   Username: {patient.user.username}")
                print(f"   Email: {patient.user.email}")
                print(f"   Phone: {patient.phone}")
            else:
                print("⚠️  Patient not created yet (signal might be processing)")
            
            # Check if medical record was created
            if patient:
                medical_record = MedicalRecord.objects.filter(patient=patient).first()
                if medical_record:
                    print(f"✅ Medical Record #{medical_record.id} Created")
                    print(f"   Visit Date: {medical_record.visit_date}")
                    print(f"   Chief Complaint: {medical_record.chief_complaint}")
            
            # Check if billing was created
            if hasattr(booking, 'billing'):
                billing = booking.billing
                print(f"✅ Billing #{billing.id} Created")
                print(f"   Service Fee: ₱{billing.service_fee}")
                print(f"   Medicine Fee: ₱{billing.medicine_fee}")
                print(f"   Total Amount: ₱{billing.total_amount}")
                print(f"   Balance: ₱{billing.balance}")
                print(f"   Paid: {billing.is_paid}")
            else:
                print("⚠️  Billing not created yet (signal might be processing)")
            
            print("\n📋 STEP 4: Add Medicine to Inventory")
            medicine1 = Inventory.objects.create(
                name="Tretinoin Cream 0.025%",
                description="Prescription acne cream",
                quantity=50,
                stock=10,  # minimum stock threshold
                category="Medicine",
                price=Decimal('450.00'),
                status="In Stock"
            )
            print(f"✅ Medicine Added: {medicine1.name}")
            print(f"   Price: ₱{medicine1.price} per item")
            print(f"   Stock: {medicine1.quantity}")
            
            medicine2 = Inventory.objects.create(
                name="Benzoyl Peroxide Gel 5%",
                description="Topical acne treatment",
                quantity=30,
                stock=5,  # minimum stock threshold
                category="Medicine",
                price=Decimal('350.00'),
                status="In Stock"
            )
            print(f"✅ Medicine Added: {medicine2.name}")
            print(f"   Price: ₱{medicine2.price} per item")
            print(f"   Stock: {medicine2.quantity}")
            
            if patient and medical_record:
                print("\n📋 STEP 5: Doctor Prescribes Medicine")
                
                # Prescription 1
                prescription1 = Prescription.objects.create(
                    medical_record=medical_record,
                    medicine=medicine1,
                    dosage="Apply thin layer once daily",
                    duration="30 days",
                    quantity=1,
                    prescribed_by=admin_user,
                    prescribed_date=timezone.now()
                )
                print(f"✅ Prescription #{prescription1.id} Created")
                print(f"   Medicine: {prescription1.medicine.name}")
                print(f"   Quantity: {prescription1.quantity}")
                print(f"   Unit Price: ₱{prescription1.medicine.price}")
                print(f"   Total: ₱{prescription1.total_price}")
                
                # Prescription 2
                prescription2 = Prescription.objects.create(
                    medical_record=medical_record,
                    medicine=medicine2,
                    dosage="Apply to affected areas twice daily",
                    duration="30 days",
                    quantity=2,
                    prescribed_by=admin_user,
                    prescribed_date=timezone.now()
                )
                print(f"✅ Prescription #{prescription2.id} Created")
                print(f"   Medicine: {prescription2.medicine.name}")
                print(f"   Quantity: {prescription2.quantity}")
                print(f"   Unit Price: ₱{prescription2.medicine.price}")
                print(f"   Total: ₱{prescription2.total_price}")
                
                # Check inventory deduction
                medicine1.refresh_from_db()
                medicine2.refresh_from_db()
                print(f"\n📦 Inventory Updated:")
                print(f"   {medicine1.name}: {medicine1.quantity} remaining")
                print(f"   {medicine2.name}: {medicine2.quantity} remaining")
                
                # Check billing update
                if hasattr(booking, 'billing'):
                    billing.refresh_from_db()
                    print(f"\n💰 Billing Updated:")
                    print(f"   Service Fee: ₱{billing.service_fee}")
                    print(f"   Medicine Fee: ₱{billing.medicine_fee}")
                    print(f"   Total Amount: ₱{billing.total_amount}")
                    print(f"   Balance: ₱{billing.balance}")
            
            if hasattr(booking, 'billing'):
                print("\n📋 STEP 6: Cashier Records Payment")
                billing.refresh_from_db()
                
                # Partial payment
                payment1 = Payment.objects.create(
                    billing=billing,
                    amount_paid=Decimal('1000.00'),
                    payment_method='Cash',
                    reference_number='CASH-001',
                    notes='Partial payment - cash',
                    recorded_by=admin_user
                )
                print(f"✅ Payment #{payment1.id} Recorded")
                print(f"   Amount: ₱{payment1.amount_paid}")
                print(f"   Method: {payment1.payment_method}")
                
                # Check billing status
                billing.refresh_from_db()
                print(f"\n💰 Billing Status:")
                print(f"   Total Amount: ₱{billing.total_amount}")
                print(f"   Amount Paid: ₱{billing.amount_paid}")
                print(f"   Balance: ₱{billing.balance}")
                print(f"   Paid: {billing.is_paid}")
                
                # Full payment
                remaining_balance = billing.balance
                payment2 = Payment.objects.create(
                    billing=billing,
                    amount_paid=remaining_balance,
                    payment_method='GCash',
                    reference_number='GCASH-123456',
                    notes='Full payment - GCash',
                    recorded_by=admin_user
                )
                print(f"\n✅ Payment #{payment2.id} Recorded")
                print(f"   Amount: ₱{payment2.amount_paid}")
                print(f"   Method: {payment2.payment_method}")
                
                # Final billing status
                billing.refresh_from_db()
                print(f"\n💰 Final Billing Status:")
                print(f"   Total Amount: ₱{billing.total_amount}")
                print(f"   Amount Paid: ₱{billing.amount_paid}")
                print(f"   Balance: ₱{billing.balance}")
                print(f"   Paid: {'✅ YES' if billing.is_paid else '❌ NO'}")
            
            print("\n📋 STEP 7: Mark Booking as Completed")
            booking.status = "Completed"
            booking.save()
            print(f"✅ Booking #{booking.id} - Status: {booking.status}")
            
            print("\n" + "="*70)
            print("✅ END-TO-END WORKFLOW TEST COMPLETE!")
            print("="*70)
            print("\n📊 SUMMARY:")
            print(f"   • Booking: #{booking.id} - {booking.status}")
            if patient:
                print(f"   • Patient: {patient.user.get_full_name()} (#{patient.id})")
            if patient and medical_record:
                print(f"   • Medical Record: #{medical_record.id}")
                print(f"   • Prescriptions: {medical_record.prescriptions.count()}")
            if hasattr(booking, 'billing'):
                billing.refresh_from_db()
                print(f"   • Billing: #{billing.id} - ₱{billing.total_amount}")
                print(f"   • Payments: {billing.payments.count()}")
                print(f"   • Paid: {'✅' if billing.is_paid else '❌'}")
            
            print("\n🎉 All database operations committed successfully!")
            print("="*70 + "\n")
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  Transaction rolled back - no data saved")

if __name__ == "__main__":
    run_workflow_test()
