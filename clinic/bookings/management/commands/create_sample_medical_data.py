from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from bookings.models import Patient, MedicalRecord
from datetime import date, datetime
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create sample medical records data for testing'

    def handle(self, *args, **options):
        # Get or create a customer user
        customer_group = Group.objects.get(name='Customer')
        
        # Create a sample customer if doesn't exist
        user, created = User.objects.get_or_create(
            username='john_doe',
            defaults={
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com'
            }
        )
        
        if created:
            user.set_password('patient123')
            user.save()
            user.groups.add(customer_group)
            self.stdout.write(f'Created customer user: {user.username}')
        
        # Create patient profile
        patient, created = Patient.objects.get_or_create(
            user=user,
            defaults={
                'date_of_birth': date(1990, 5, 15),
                'gender': 'M',
                'phone': '+1234567890',
                'address': '123 Main Street, Anytown, AT 12345',
                'emergency_contact_name': 'Jane Doe',
                'emergency_contact_phone': '+1234567891',
                'blood_type': 'O+',
                'allergies': 'None known',
                'current_medications': 'None',
                'medical_history': 'No significant medical history',
                'created_by': User.objects.filter(is_superuser=True).first()
            }
        )
        
        if created:
            self.stdout.write(f'Created patient profile for: {patient.user.get_full_name()}')
        
        # Create a sample medical record
        medical_record, created = MedicalRecord.objects.get_or_create(
            patient=patient,
            visit_date=timezone.now(),
            defaults={
                'chief_complaint': 'Routine skin check and mole examination',
                'symptoms': 'Patient reports no specific symptoms. Routine preventive care visit.',
                'diagnosis': 'Normal skin examination. No concerning lesions found.',
                'treatment_plan': 'Continue routine skin care. Annual follow-up recommended.',
                'temperature': 36.8,
                'blood_pressure_systolic': 120,
                'blood_pressure_diastolic': 80,
                'heart_rate': 72,
                'weight': 75.5,
                'height': 180.0,
                'follow_up_date': date(2025, 12, 18),
                'additional_notes': 'Patient educated on sun protection and skin self-examination.',
                'created_by': User.objects.filter(is_superuser=True).first()
            }
        )
        
        if created:
            self.stdout.write(f'Created medical record for: {patient.user.get_full_name()}')
        
        self.stdout.write(
            self.style.SUCCESS(
                'Sample medical records data created successfully!\n'
                f'Patient: {user.get_full_name()} ({user.username})\n'
                f'Login: {user.username} / patient123'
            )
        )