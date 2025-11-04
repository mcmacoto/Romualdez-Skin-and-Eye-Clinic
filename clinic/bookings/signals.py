"""
Signals for automatic billing, patient, and medical record management
"""
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from .models import Booking, Billing, Payment, Patient, MedicalRecord, Prescription
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Booking)
def check_booking_confirmation(sender, instance, **kwargs):
    """
    Check if booking status is changing to Confirmed or consultation_status is changing to Done
    Store previous state in database to avoid race conditions
    """
    if instance.pk:
        try:
            old_instance = Booking.objects.select_for_update().get(pk=instance.pk)
            
            # Store flags in a thread-safe way by checking actual database state
            # Check if consultation_status changed to 'Done'
            if old_instance.consultation_status != 'Done' and instance.consultation_status == 'Done':
                # Mark for consultation completion handling
                instance._consultation_just_completed = True
                logger.info(f"Booking {instance.id} consultation marked as Done - will create records")
            
            # Check if status changed from non-Confirmed to Confirmed
            elif old_instance.status != 'Confirmed' and instance.status == 'Confirmed':
                # Mark for appointment creation
                instance._booking_just_confirmed = True
                logger.info(f"Booking {instance.id} confirmed - will create Appointment record")
                
        except Booking.DoesNotExist:
            pass


@receiver(post_save, sender=Booking)
def create_appointment_or_patient_records(sender, instance, created, **kwargs):
    """
    Handle two scenarios with proper transaction management:
    1. When booking is confirmed: Create Appointment record only
    2. When consultation_status = 'Done': Create Patient, MedicalRecord, and Billing
    """
    # Scenario 1: Booking confirmed - Create Appointment record
    if hasattr(instance, '_booking_just_confirmed') and instance._booking_just_confirmed:
        try:
            with transaction.atomic():
                from .models import Appointment
                
                # Use get_or_create to prevent duplicates
                appointment, appointment_created = Appointment.objects.get_or_create(
                    name=instance.patient_name,
                    email=instance.patient_email,
                    date=instance.date,
                    time=instance.time,
                    defaults={
                        'phone': instance.patient_phone,
                        'message': instance.notes,
                        'status': 'Confirmed',
                        'consultation_status': 'Not Yet'
                    }
                )
                
                if appointment_created:
                    logger.info(f"[OK] Created Appointment #{appointment.id} for confirmed booking #{instance.id}")
                else:
                    logger.info(f"[INFO] Appointment already exists for booking #{instance.id}")
            
            # Clean up the flag
            delattr(instance, '_booking_just_confirmed')
            
        except Exception as e:
            logger.error(f"[ERROR] Error creating Appointment for booking {instance.id}: {str(e)}")
    
    # Scenario 2: Consultation Done - Create Patient, MedicalRecord, and Billing
    elif hasattr(instance, '_consultation_just_completed') and instance._consultation_just_completed:
        try:
            with transaction.atomic():
                # 1. Create or get User account for the patient
                username = instance.patient_email.split('@')[0].lower()
                base_username = username
                counter = 1
                
                # Ensure unique username with database lock
                while User.objects.select_for_update().filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Split patient name into first and last name
                name_parts = instance.patient_name.strip().split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                user, user_created = User.objects.get_or_create(
                    email=instance.patient_email,
                    defaults={
                        'username': username,
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_active': True,
                        'is_staff': False,
                    }
                )
                
                if user_created:
                    # Generate a random secure password instead of hardcoded one
                    import secrets
                    import string
                    alphabet = string.ascii_letters + string.digits + string.punctuation
                    temp_password = ''.join(secrets.choice(alphabet) for i in range(16))
                    user.set_password(temp_password)
                    user.save()
                    logger.info(f"[OK] Created new user account: {user.username} with temporary password")
                    # TODO: Send password reset email to user
                    # from django.core.mail import send_mail
                    # send_password_reset_email(user, temp_password)
                
                # 2. Create Patient profile if it doesn't exist
                patient, patient_created = Patient.objects.get_or_create(
                    user=user,
                    defaults={
                        'phone': instance.patient_phone,
                        'date_of_birth': timezone.now().date(),  # Placeholder - should be updated
                        'gender': 'O',  # Unknown
                        'created_by': instance.created_by,
                    }
                )
                
                if patient_created:
                    logger.info(f"[OK] Created new patient profile for {user.get_full_name()}")
                
                # 3. Create Medical Record for this visit
                medical_record = MedicalRecord.objects.create(
                    patient=patient,
                    visit_date=timezone.now(),
                    chief_complaint=instance.notes or f"Scheduled appointment for {instance.service.name}",
                    symptoms=f"Appointment Type: {instance.service.name}",
                    diagnosis="Consultation completed",
                    treatment_plan="As prescribed by the doctor",
                    created_by=instance.created_by,
                )
                logger.info(f"[OK] Created medical record #{medical_record.id} for {patient}")
                
                # 4. Create Billing (only when consultation is Done)
                # Use get_or_create to prevent duplicate billings
                from django.conf import settings
                default_fee = getattr(settings, 'DEFAULT_SERVICE_FEE', 500.00)
                
                # Determine service fee
                service_fee = default_fee
                if instance.service and hasattr(instance.service, 'price') and instance.service.price > 0:
                    service_fee = float(instance.service.price)
                
                billing, billing_created = Billing.objects.get_or_create(
                    booking=instance,
                    defaults={
                        'service_fee': service_fee,
                        'medicine_fee': 0.00,
                        'additional_fee': 0.00,
                        'discount': 0.00,
                        'notes': f"Consultation fee for {instance.service.name if instance.service else 'General Consultation'}"
                    }
                )
                
                if billing_created:
                    logger.info(f"[OK] Created billing #{billing.id} with service fee PHP{service_fee}, total PHP{billing.total_amount}")
                else:
                    logger.info(f"[INFO] Billing already exists for booking #{instance.id}: #{billing.id}")
                
                # Update booking status to Completed
                Booking.objects.filter(pk=instance.pk).update(status='Completed')
                instance.status = 'Completed'
                
                logger.info(f"[OK] TRANSACTION COMPLETE: All records created for booking #{instance.id} after consultation completion")
            
            # Clean up the flag
            delattr(instance, '_consultation_just_completed')
            
        except Exception as e:
            logger.error(f"[ERROR] TRANSACTION FAILED: Error creating records for booking {instance.id}: {str(e)}")
            # Transaction will be rolled back automatically


@receiver(post_save, sender=Payment)
def update_billing_on_payment(sender, instance, created, **kwargs):
    """
    Update billing payment status whenever a payment is created or modified
    """
    if created:
        instance.billing.update_payment_status()
        logger.info(f"Updated billing status after payment #{instance.id}")


@receiver(post_save, sender=Billing)
def recalculate_billing_totals(sender, instance, created, **kwargs):
    """
    Recalculate billing totals when fees are updated
    Only runs if NOT created to avoid recursion
    """
    # Skip if this is a new billing (created=True) or if we're already in update_payment_status
    if not created and not hasattr(instance, '_updating'):
        # Set flag to prevent recursion
        instance._updating = True
        try:
            instance.update_payment_status()
        finally:
            # Clean up flag
            if hasattr(instance, '_updating'):
                delattr(instance, '_updating')


@receiver(post_save, sender=Prescription)
def update_billing_medicine_fee(sender, instance, created, **kwargs):
    """
    Automatically update billing medicine fee when prescriptions are added
    Uses transaction.atomic() for data consistency
    """
    if created:
        try:
            with transaction.atomic():
                # Get the booking associated with this medical record
                medical_record = instance.medical_record
                patient = medical_record.patient
                
                # Find the most recent booking for this patient
                booking = Booking.objects.filter(
                    patient_email=patient.user.email,
                    status__in=['Confirmed', 'Completed']
                ).order_by('-date', '-time').first()
                
                if booking and hasattr(booking, 'billing'):
                    # Calculate total prescription cost
                    total_prescription_cost = sum(
                        prescription.total_price
                        for prescription in medical_record.prescriptions.all()
                    )
                    
                    # Update billing
                    billing = booking.billing
                    billing.medicine_fee = total_prescription_cost
                    billing.save()
                    
                    logger.info(f"✅ Updated billing #{billing.id} medicine fee to ₱{total_prescription_cost}")
        except Exception as e:
            logger.error(f"❌ Error updating billing for prescription: {str(e)}")


@receiver(post_delete, sender=Prescription)
def update_billing_on_prescription_delete(sender, instance, **kwargs):
    """
    Update billing when a prescription is deleted
    Uses transaction.atomic() for data consistency
    """
    try:
        with transaction.atomic():
            medical_record = instance.medical_record
            patient = medical_record.patient
            
            # Find the most recent booking for this patient
            booking = Booking.objects.filter(
                patient_email=patient.user.email,
                status__in=['Confirmed', 'Completed']
            ).order_by('-date', '-time').first()
            
            if booking and hasattr(booking, 'billing'):
                # Recalculate total prescription cost
                total_prescription_cost = sum(
                    prescription.total_price
                    for prescription in medical_record.prescriptions.all()
                )
                
                # Update billing
                billing = booking.billing
                billing.medicine_fee = total_prescription_cost
                billing.save()
                
                logger.info(f"✅ Updated billing #{billing.id} after prescription deletion")
    except Exception as e:
        logger.error(f"❌ Error updating billing after prescription deletion: {str(e)}")

