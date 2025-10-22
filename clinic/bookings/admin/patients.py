"""
Admin classes for patient-related models
"""
from django.contrib import admin

from .base import CustomModelAdmin
from ..models import Patient, MedicalRecord, MedicalImage, Prescription, Inventory
from ..utils import format_image_preview


class MedicalImageInline(admin.TabularInline):
    """Inline admin for medical images"""
    model = MedicalImage
    extra = 0
    readonly_fields = ('uploaded_at', 'uploaded_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set on creation
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


class PrescriptionInline(admin.TabularInline):
    """Inline prescription editor for medical records"""
    model = Prescription
    extra = 1
    fields = ('medicine', 'quantity', 'dosage', 'duration', 'unit_price', 'total_price')
    readonly_fields = ('total_price',)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "medicine":
            kwargs["queryset"] = Inventory.objects.filter(
                category='Medicine',
                status__in=['In Stock', 'Low Stock']
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class PatientAdmin(CustomModelAdmin):
    list_display = ('get_full_name', 'user_email', 'phone', 'date_of_birth', 'gender', 'blood_type', 'created_at')
    list_filter = ('gender', 'blood_type', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'phone')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('user', 'date_of_birth', 'gender', 'phone')
        }),
        ('Contact Information', {
            'fields': ('address', 'emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Medical Information', {
            'fields': ('blood_type', 'allergies', 'current_medications', 'medical_history')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Patient Name'
    get_full_name.admin_order_field = 'user__last_name'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class MedicalRecordAdmin(CustomModelAdmin):
    list_display = ('patient_name', 'visit_date', 'chief_complaint_short', 'diagnosis_short', 'created_by', 'created_at')
    list_filter = ('visit_date', 'created_at', 'created_by')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'chief_complaint', 'diagnosis')
    ordering = ('-visit_date',)
    date_hierarchy = 'visit_date'
    
    inlines = [MedicalImageInline, PrescriptionInline]
    
    fieldsets = (
        ('Patient & Visit Information', {
            'fields': ('patient', 'visit_date', 'chief_complaint')
        }),
        ('Clinical Findings', {
            'fields': ('symptoms', 'diagnosis', 'treatment_plan')
        }),
        ('Vital Signs', {
            'fields': (
                ('temperature', 'heart_rate'),
                ('blood_pressure_systolic', 'blood_pressure_diastolic'),
                ('weight', 'height')
            ),
            'classes': ('collapse',)
        }),
        ('Follow-up & Notes', {
            'fields': ('follow_up_date', 'additional_notes')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    
    def patient_name(self, obj):
        return obj.patient.user.get_full_name() or obj.patient.user.username
    patient_name.short_description = 'Patient'
    patient_name.admin_order_field = 'patient__user__last_name'
    
    def chief_complaint_short(self, obj):
        return obj.chief_complaint[:50] + '...' if len(obj.chief_complaint) > 50 else obj.chief_complaint
    chief_complaint_short.short_description = 'Chief Complaint'
    
    def diagnosis_short(self, obj):
        return obj.diagnosis[:50] + '...' if obj.diagnosis and len(obj.diagnosis) > 50 else obj.diagnosis or '-'
    diagnosis_short.short_description = 'Diagnosis'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class MedicalImageAdmin(CustomModelAdmin):
    list_display = ('title', 'patient_name', 'image_type', 'visit_date', 'uploaded_by', 'uploaded_at')
    list_filter = ('image_type', 'uploaded_at', 'uploaded_by')
    search_fields = ('title', 'description', 'medical_record__patient__user__first_name', 'medical_record__patient__user__last_name')
    ordering = ('-uploaded_at',)
    
    fieldsets = (
        ('Image Information', {
            'fields': ('medical_record', 'image', 'image_preview')
        }),
        ('Details', {
            'fields': ('title', 'description', 'image_type')
        }),
        ('System Information', {
            'fields': ('uploaded_at', 'uploaded_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('uploaded_at', 'uploaded_by', 'image_preview')
    
    def patient_name(self, obj):
        return obj.medical_record.patient.user.get_full_name() or obj.medical_record.patient.user.username
    patient_name.short_description = 'Patient'
    
    def visit_date(self, obj):
        return obj.medical_record.visit_date.strftime('%Y-%m-%d')
    visit_date.short_description = 'Visit Date'
    
    def image_preview(self, obj):
        """Display image preview"""
        if obj.image:
            return format_image_preview(obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set on creation
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
