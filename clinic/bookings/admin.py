from django.contrib import admin
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.utils.html import format_html
from datetime import date
from .models import Appointment, Service, Patient, MedicalRecord, MedicalImage

# Custom Admin Site
class ClinicAdminSite(AdminSite):
    site_header = "Romualdez Skin Clinic Staff Portal"
    site_title = "Clinic Portal"
    index_title = "Dashboard"
    
    def index(self, request, extra_context=None):
        """
        Display the main admin index page with custom dashboard data.
        """
        extra_context = extra_context or {}
        
        # Get statistics
        total_appointments = Appointment.objects.count()
        pending_appointments = Appointment.objects.filter(status='Pending').count()
        confirmed_appointments = Appointment.objects.filter(status='Confirmed').count()
        today_appointments = Appointment.objects.filter(date=date.today()).count()
        
        # Get recent appointments (last 10)
        recent_appointments = Appointment.objects.all().order_by('-created_at')[:10]
        
        # Get patient count (customers only)
        total_patients = User.objects.filter(groups__name='Customer').count()
        
        # Medical records statistics
        total_medical_records = MedicalRecord.objects.count()
        total_patient_profiles = Patient.objects.count()
        recent_medical_records = MedicalRecord.objects.select_related('patient__user').order_by('-visit_date')[:5]
        
        extra_context.update({
            'total_appointments': total_appointments,
            'pending_appointments': pending_appointments,
            'confirmed_appointments': confirmed_appointments,
            'today_appointments': today_appointments,
            'recent_appointments': recent_appointments,
            'total_patients': total_patients,
            'total_medical_records': total_medical_records,
            'total_patient_profiles': total_patient_profiles,
            'recent_medical_records': recent_medical_records,
        })
        
        return super().index(request, extra_context)

# Create custom admin site instance
clinic_admin_site = ClinicAdminSite(name='clinic_admin')

class RestrictedUserAdmin(BaseUserAdmin):
    """Custom User Admin that restricts staff creation to superusers only"""
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            # Staff can only see customer users and themselves
            return qs.filter(groups__name='Customer').distinct() | qs.filter(id=request.user.id)
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        
        if not request.user.is_superuser:
            # Remove sensitive fields for non-superusers
            restricted_fieldsets = []
            for name, field_options in fieldsets:
                if name == 'Permissions':
                    # Staff cannot modify permissions
                    continue
                elif name is None:  # Personal info section
                    fields = list(field_options['fields'])
                    # Remove staff status and superuser status
                    if 'is_staff' in fields:
                        fields.remove('is_staff')
                    if 'is_superuser' in fields:
                        fields.remove('is_superuser')
                    restricted_fieldsets.append((name, {'fields': tuple(fields)}))
                else:
                    restricted_fieldsets.append((name, field_options))
            return restricted_fieldsets
        
        return fieldsets
    
    def save_model(self, request, obj, form, change):
        # Prevent non-superusers from creating staff accounts
        if not request.user.is_superuser:
            if obj.is_staff and not change:
                # New user being created as staff by non-superuser
                messages.error(request, "You don't have permission to create staff accounts.")
                return
            elif change and obj.is_staff:
                # Existing staff user being modified by non-superuser
                original = User.objects.get(pk=obj.pk)
                if not original.is_staff:
                    # Trying to promote regular user to staff
                    messages.error(request, "You don't have permission to grant staff status.")
                    return
        
        super().save_model(request, obj, form, change)
        
        # Automatically add new users to Customer group if not staff
        if not change and not obj.is_staff:
            customer_group, created = Group.objects.get_or_create(name='Customer')
            obj.groups.add(customer_group)
    
    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser and obj:
            # Staff cannot delete other staff members or superusers
            if obj.is_staff or obj.is_superuser:
                return False
        return super().has_delete_permission(request, obj)

# Register your models with the custom admin site
@admin.register(Appointment, site=clinic_admin_site)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'date', 'time', 'status', 'created_at')
    list_filter = ('status', 'date', 'created_at')
    search_fields = ('name', 'email', 'phone')
    ordering = ('-created_at',)
    date_hierarchy = 'date'
    list_editable = ('status',)
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Appointment Details', {
            'fields': ('date', 'time', 'status', 'message')
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related()

@admin.register(Service, site=clinic_admin_site)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    
    def has_module_permission(self, request):
        # Only superusers can manage services
        return request.user.is_superuser

class MedicalImageInline(admin.TabularInline):
    """Inline admin for medical images"""
    model = MedicalImage
    extra = 0
    readonly_fields = ('uploaded_at', 'uploaded_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set on creation
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Patient, site=clinic_admin_site)
class PatientAdmin(admin.ModelAdmin):
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

@admin.register(MedicalRecord, site=clinic_admin_site)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'visit_date', 'chief_complaint_short', 'diagnosis_short', 'created_by', 'created_at')
    list_filter = ('visit_date', 'created_at', 'created_by')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'chief_complaint', 'diagnosis')
    ordering = ('-visit_date',)
    date_hierarchy = 'visit_date'
    
    inlines = [MedicalImageInline]
    
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

@admin.register(MedicalImage, site=clinic_admin_site)
class MedicalImageAdmin(admin.ModelAdmin):
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
        if obj.image:
            return format_html('<img src="{}" style="max-width: 200px; max-height: 200px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set on creation
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

class GroupAdmin(admin.ModelAdmin):
    """Custom Group admin that only superusers can access"""
    
    def has_module_permission(self, request):
        return request.user.is_superuser

# Register the User model with our custom admin site using the restricted admin
clinic_admin_site.register(User, RestrictedUserAdmin)
clinic_admin_site.register(Group, GroupAdmin)

# Also register with default admin for compatibility
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Service)

