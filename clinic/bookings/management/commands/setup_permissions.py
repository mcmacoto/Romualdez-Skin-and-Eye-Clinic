from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from bookings.models import Appointment, Patient, MedicalRecord, MedicalImage

class Command(BaseCommand):
    help = 'Setup user groups and permissions for clinic staff management'

    def handle(self, *args, **options):
        # Create groups
        staff_group, created = Group.objects.get_or_create(name='Clinic Staff')
        customer_group, created = Group.objects.get_or_create(name='Customer')
        
        # Get content types
        appointment_ct = ContentType.objects.get_for_model(Appointment)
        patient_ct = ContentType.objects.get_for_model(Patient)
        medical_record_ct = ContentType.objects.get_for_model(MedicalRecord)
        medical_image_ct = ContentType.objects.get_for_model(MedicalImage)
        user_ct = ContentType.objects.get(app_label='auth', model='user')
        group_ct = ContentType.objects.get(app_label='auth', model='group')
        
        # Define permissions for staff
        staff_permissions = [
            # Appointment permissions (full CRUD)
            Permission.objects.get(content_type=appointment_ct, codename='add_appointment'),
            Permission.objects.get(content_type=appointment_ct, codename='change_appointment'),
            Permission.objects.get(content_type=appointment_ct, codename='delete_appointment'),
            Permission.objects.get(content_type=appointment_ct, codename='view_appointment'),
            
            # Patient permissions (full CRUD)
            Permission.objects.get(content_type=patient_ct, codename='add_patient'),
            Permission.objects.get(content_type=patient_ct, codename='change_patient'),
            Permission.objects.get(content_type=patient_ct, codename='delete_patient'),
            Permission.objects.get(content_type=patient_ct, codename='view_patient'),
            
            # Medical Record permissions (full CRUD)
            Permission.objects.get(content_type=medical_record_ct, codename='add_medicalrecord'),
            Permission.objects.get(content_type=medical_record_ct, codename='change_medicalrecord'),
            Permission.objects.get(content_type=medical_record_ct, codename='delete_medicalrecord'),
            Permission.objects.get(content_type=medical_record_ct, codename='view_medicalrecord'),
            
            # Medical Image permissions (full CRUD)
            Permission.objects.get(content_type=medical_image_ct, codename='add_medicalimage'),
            Permission.objects.get(content_type=medical_image_ct, codename='change_medicalimage'),
            Permission.objects.get(content_type=medical_image_ct, codename='delete_medicalimage'),
            Permission.objects.get(content_type=medical_image_ct, codename='view_medicalimage'),
            
            # User permissions (only view and add customers, no staff creation)
            Permission.objects.get(content_type=user_ct, codename='view_user'),
            Permission.objects.get(content_type=user_ct, codename='add_user'),
            Permission.objects.get(content_type=user_ct, codename='change_user'),
        ]
        
        # Assign permissions to staff group
        staff_group.permissions.set(staff_permissions)
        
        # Customer group has minimal permissions (just view their own data)
        customer_permissions = []
        customer_group.permissions.set(customer_permissions)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created groups and permissions:\n'
                f'- Clinic Staff: {len(staff_permissions)} permissions\n'
                f'- Customer: {len(customer_permissions)} permissions'
            )
        )