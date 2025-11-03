"""
Patient and medical record models
Handles patient information, medical records, and medical images
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# Phone number validator
phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)

# Email validator
from django.core.validators import EmailValidator
email_validator = EmailValidator(message="Enter a valid email address.")


class Patient(models.Model):
    """Extended patient information linked to User account"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    
    # Personal Information
    date_of_birth = models.DateField()
    gender_choices = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=gender_choices)
    
    # Contact Information
    phone = models.CharField(
        validators=[phone_validator], 
        max_length=17, 
        blank=True,
        unique=True,
        null=True,
        help_text="Patient's primary phone number (must be unique)"
    )
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(validators=[phone_validator], max_length=17, blank=True)
    
    # Medical Information
    blood_type_choices = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('UK', 'Unknown'),
    ]
    blood_type = models.CharField(max_length=3, choices=blood_type_choices, default='UK')
    allergies = models.TextField(blank=True, help_text="List any known allergies")
    current_medications = models.TextField(blank=True, help_text="Current medications and dosages")
    medical_history = models.TextField(blank=True, help_text="Previous medical conditions and surgeries")
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_patients')
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.user.email}"


class MedicalRecord(models.Model):
    """Individual medical record entries for patients"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    
    # Visit Information
    visit_date = models.DateTimeField(db_index=True)
    chief_complaint = models.TextField(help_text="Patient's main concern or reason for visit")
    
    # Clinical Findings
    symptoms = models.TextField(blank=True, help_text="Observed symptoms")
    diagnosis = models.TextField(blank=True, help_text="Clinical diagnosis")
    treatment_plan = models.TextField(blank=True, help_text="Prescribed treatment and recommendations")
    
    # Vital Signs (optional)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True, help_text="°C")
    blood_pressure_systolic = models.IntegerField(blank=True, null=True)
    blood_pressure_diastolic = models.IntegerField(blank=True, null=True)
    heart_rate = models.IntegerField(blank=True, null=True, help_text="BPM")
    weight = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, help_text="kg")
    height = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, help_text="cm")
    
    # Follow-up and Notes
    follow_up_date = models.DateField(blank=True, null=True)
    additional_notes = models.TextField(blank=True)
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_records')
    
    class Meta:
        ordering = ['-visit_date']
    
    def __str__(self):
        return f"{self.patient.user.get_full_name()} - {self.visit_date.strftime('%Y-%m-%d')} - {self.chief_complaint[:50]}"


def medical_image_upload_path(instance, filename):
    """Generate upload path for medical images"""
    return f'medical_records/{instance.medical_record.patient.user.username}/{instance.medical_record.visit_date.strftime("%Y-%m-%d")}/{filename}'


class MedicalImage(models.Model):
    """Medical images attached to records"""
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='images')
    
    # Image Information
    image = models.ImageField(upload_to=medical_image_upload_path)
    title = models.CharField(max_length=100, help_text="Brief description of the image")
    description = models.TextField(blank=True, help_text="Detailed description or notes about the image")
    
    # Image Metadata
    image_type_choices = [
        ('clinical', 'Clinical Photo'),
        ('dermoscopy', 'Dermoscopy'),
        ('before', 'Before Treatment'),
        ('after', 'After Treatment'),
        ('diagnostic', 'Diagnostic Image'),
        ('other', 'Other'),
    ]
    image_type = models.CharField(max_length=20, choices=image_type_choices, default='clinical')
    
    # System fields
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_images')
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.medical_record.patient.user.get_full_name()}"
