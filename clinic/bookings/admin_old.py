from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.utils.html import format_html
from datetime import date
from django import forms
from django.db import transaction
from .models import (
    Appointment, Service, Patient, MedicalRecord, MedicalImage, 
    Inventory, StockTransaction, Booking, Billing, Payment, Prescription,
    POSSale, POSSaleItem
)

# Custom Admin Site
class ClinicAdminSite(AdminSite):
    site_header = "Romualdez Skin & Eye Clinic Staff Portal"
    site_title = "Clinic Portal"
    index_title = "Dashboard"
    
    def index(self, request, extra_context=None):
        """
        Display the main admin index page with custom dashboard data.
        """
        extra_context = extra_context or {}
        
        # Get statistics - Total Appointments shows bookings with consultation_status "Not Yet" or "Ongoing"
        total_appointments = Booking.objects.filter(
            status='Confirmed',
            consultation_status__in=['Not Yet', 'Ongoing']
        ).count()
        pending_appointments = Appointment.objects.filter(status='Pending').count()
        confirmed_appointments = Appointment.objects.filter(status='Confirmed').count()
        today_appointments = Appointment.objects.filter(date=date.today()).count()
        
        # IMPORTANT: Add Booking statistics (the new system)
        total_bookings = Booking.objects.count()
        pending_bookings = Booking.objects.filter(status='Pending').count()
        confirmed_bookings = Booking.objects.filter(status='Confirmed').count()
        completed_bookings = Booking.objects.filter(status='Completed').count()
        today_bookings = Booking.objects.filter(date=date.today()).count()
        
        # Combine pending counts from both systems
        total_pending = pending_appointments + pending_bookings
        
        # Get recent appointments (last 10)
        recent_appointments = Appointment.objects.all().order_by('-created_at')[:10]
        
        # Get patient count (customers only)
        total_patients = User.objects.filter(groups__name='Customer').count()
        
        # Medical records statistics
        total_medical_records = MedicalRecord.objects.count()
        total_patient_profiles = Patient.objects.count()
        recent_medical_records = MedicalRecord.objects.select_related('patient__user').order_by('-visit_date')[:5]
        
        # Inventory statistics
        total_inventory_items = Inventory.objects.count()
        low_stock_items = Inventory.objects.filter(status='Low Stock').count()
        out_of_stock_items = Inventory.objects.filter(status='Out of Stock').count()
        
        # Billing statistics
        from django.db.models import Sum
        total_billings = Billing.objects.count()
        paid_bills = Billing.objects.filter(is_paid=True).count()
        unpaid_bills = Billing.objects.filter(is_paid=False).count()
        partially_paid_bills = Billing.objects.filter(is_paid=False, amount_paid__gt=0).count()
        
        total_revenue = Billing.objects.filter(is_paid=True).aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        total_amount_billed = Billing.objects.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        total_amount_paid = Billing.objects.aggregate(
            total=Sum('amount_paid')
        )['total'] or 0
        
        total_balance_outstanding = Billing.objects.filter(is_paid=False).aggregate(
            total=Sum('balance')
        )['total'] or 0
        
        # POS statistics
        total_pos_sales = POSSale.objects.count()
        completed_pos_sales = POSSale.objects.filter(status='Completed').count()
        pending_pos_sales = POSSale.objects.filter(status='Pending').count()
        pos_revenue_today = POSSale.objects.filter(
            status='Completed',
            sale_date__date=date.today()
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        pos_total_revenue = POSSale.objects.filter(
            status='Completed'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Recent POS sales
        recent_pos_sales = POSSale.objects.select_related('patient', 'created_by').order_by('-sale_date')[:5]
        
        extra_context.update({
            'total_appointments': total_appointments,
            'pending_appointments': total_pending,  # Combined pending count
            'pending_bookings': pending_bookings,  # New bookings pending count
            'confirmed_appointments': confirmed_appointments,
            'today_appointments': today_appointments,
            'recent_appointments': recent_appointments,
            'total_patients': total_patients,
            'total_medical_records': total_medical_records,
            'total_patient_profiles': total_patient_profiles,
            'recent_medical_records': recent_medical_records,
            'total_inventory_items': total_inventory_items,
            'low_stock_items': low_stock_items,
            'out_of_stock_items': out_of_stock_items,
            'total_bookings': total_bookings,
            'confirmed_bookings': confirmed_bookings,
            'completed_bookings': completed_bookings,
            'today_bookings': today_bookings,
            'paid_bills': paid_bills,
            'unpaid_bills': unpaid_bills,
            'partially_paid_bills': partially_paid_bills,
            'total_revenue': total_revenue,
            'total_amount_billed': total_amount_billed,
            'total_amount_paid': total_amount_paid,
            'total_balance_outstanding': total_balance_outstanding,
            'total_billings': total_billings,
            'total_pos_sales': total_pos_sales,
            'completed_pos_sales': completed_pos_sales,
            'pending_pos_sales': pending_pos_sales,
            'pos_revenue_today': pos_revenue_today,
            'pos_total_revenue': pos_total_revenue,
            'recent_pos_sales': recent_pos_sales,
        })
        
        return super().index(request, extra_context)

# Create custom admin site instance
clinic_admin_site = ClinicAdminSite(name='clinic_admin')

# Base ModelAdmin class to hide app label from breadcrumbs
class CustomModelAdmin(admin.ModelAdmin):
    """Base admin class that removes the app name from breadcrumbs"""
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Override to modify breadcrumb context"""
        extra_context = extra_context or {}
        extra_context['hide_app_breadcrumb'] = True
        return super().changeform_view(request, object_id, form_url, extra_context)
    
    def changelist_view(self, request, extra_context=None):
        """Override to modify breadcrumb context"""
        extra_context = extra_context or {}
        extra_context['hide_app_breadcrumb'] = True
        return super().changelist_view(request, extra_context)
    
    def add_view(self, request, form_url='', extra_context=None):
        """Override to modify breadcrumb context"""
        extra_context = extra_context or {}
        extra_context['hide_app_breadcrumb'] = True
        return super().add_view(request, form_url, extra_context)

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
class AppointmentAdmin(CustomModelAdmin):
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
class ServiceAdmin(CustomModelAdmin):
    list_display = ('name', 'price_display', 'description')
    search_fields = ('name', 'description')
    list_filter = ('price',)
    
    fieldsets = (
        ('Service Information', {
            'fields': ('name', 'description', 'image', 'price')
        }),
    )
    
    def price_display(self, obj):
        """Display price with currency symbol"""
        return f"₱{obj.price:,.2f}"
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'price'
    
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


@admin.register(Patient, site=clinic_admin_site)
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

@admin.register(MedicalRecord, site=clinic_admin_site)
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

@admin.register(MedicalImage, site=clinic_admin_site)
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
        if obj.image:
            return format_html('<img src="{}" style="max-width: 200px; max-height: 200px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set on creation
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

class GroupAdmin(CustomModelAdmin):
    """Custom Group admin that only superusers can access"""
    
    def has_module_permission(self, request):
        return request.user.is_superuser

# Inventory Management System
class InventoryAdminForm(forms.ModelForm):
    """Custom form for Inventory with Stock In/Out functionality"""
    
    stock_in = forms.IntegerField(
        required=False,
        initial=0,
        min_value=0,
        label="Stock In",
        help_text="Add quantity to current stock"
    )
    stock_out = forms.IntegerField(
        required=False,
        initial=0,
        min_value=0,
        label="Stock Out",
        help_text="Subtract quantity from current stock"
    )
    
    class Meta:
        model = Inventory
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make stock_in and stock_out fields more prominent
        if self.instance and self.instance.pk:
            self.fields['stock_in'].help_text = f"Current quantity: {self.instance.quantity}. Add to stock."
            self.fields['stock_out'].help_text = f"Current quantity: {self.instance.quantity}. Remove from stock."

@admin.register(Inventory, site=clinic_admin_site)
class InventoryAdmin(CustomModelAdmin):
    form = InventoryAdminForm
    
    list_display = ('item_id', 'name', 'category', 'quantity', 'stock', 'status', 'expiry_date', 'date_stock_in')
    list_filter = ('category', 'status', 'date_stock_in')
    search_fields = ('name', 'description', 'item_id')
    ordering = ('-date_stock_in',)
    date_hierarchy = 'date_stock_in'
    list_per_page = 25
    
    fieldsets = (
        ('Item Information', {
            'fields': ('name', 'description', 'category')
        }),
        ('Stock Management', {
            'fields': ('quantity', 'stock', 'status', 'stock_in', 'stock_out'),
            'description': 'Use Stock In/Out fields to adjust inventory. Status updates automatically.'
        }),
        ('Additional Details', {
            'fields': ('expiry_date', 'date_stock_in'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_stock_in', 'status')
    
    def save_model(self, request, obj, form, change):
        """Handle stock in/out adjustments"""
        stock_in = form.cleaned_data.get('stock_in', 0) or 0
        stock_out = form.cleaned_data.get('stock_out', 0) or 0
        
        # Adjust quantity based on stock in/out
        if stock_in > 0:
            obj.quantity += stock_in
            messages.success(request, f"Added {stock_in} units to {obj.name}. New quantity: {obj.quantity}")
        
        if stock_out > 0:
            if obj.quantity >= stock_out:
                obj.quantity -= stock_out
                messages.success(request, f"Removed {stock_out} units from {obj.name}. New quantity: {obj.quantity}")
            else:
                messages.error(request, f"Cannot remove {stock_out} units. Only {obj.quantity} units available.")
                return
        
        # Status is auto-updated in model's save method
        super().save_model(request, obj, form, change)
    
    def get_list_display_links(self, request, list_display):
        """Make item_id and name clickable"""
        return ('item_id', 'name')
    
    # Custom display methods
    def colored_status(self, obj):
        colors = {
            'In Stock': 'green',
            'Low Stock': 'orange',
            'Out of Stock': 'red'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.status
        )
    colored_status.short_description = 'Status'


# ===== PRESCRIPTION ADMIN =====
@admin.register(Prescription, site=clinic_admin_site)
class PrescriptionAdmin(CustomModelAdmin):
    list_display = ('id', 'patient_name', 'medicine', 'quantity', 'dosage', 'total_price', 'prescribed_date')
    list_filter = ('prescribed_date', 'medicine__category')
    search_fields = ('medical_record__patient__user__first_name', 'medical_record__patient__user__last_name', 'medicine__name')
    readonly_fields = ('total_price', 'prescribed_date', 'prescribed_by')
    date_hierarchy = 'prescribed_date'
    
    fieldsets = (
        ('Prescription Details', {
            'fields': ('medical_record', 'medicine', 'quantity', 'dosage', 'duration')
        }),
        ('Pricing', {
            'fields': ('unit_price', 'total_price')
        }),
        ('Instructions', {
            'fields': ('instructions',),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('prescribed_date', 'prescribed_by'),
            'classes': ('collapse',)
        }),
    )
    
    def patient_name(self, obj):
        return obj.medical_record.patient.user.get_full_name()
    patient_name.short_description = 'Patient'
    
    def save_model(self, request, obj, form, change):
        if not obj.prescribed_by:
            obj.prescribed_by = request.user
        super().save_model(request, obj, form, change)


# ===== BOOKING ADMIN =====
@admin.register(Booking, site=clinic_admin_site)
class BookingAdmin(CustomModelAdmin):
    list_display = ('id', 'patient_name', 'patient_email', 'patient_phone', 'date', 'time', 'service', 'status_badge', 'consultation_status_badge', 'created_at')
    list_filter = ('status', 'consultation_status', 'date', 'service', 'created_at')
    search_fields = ('patient_name', 'patient_email', 'patient_phone', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    date_hierarchy = 'date'
    list_per_page = 25
    actions = ['accept_bookings', 'reject_bookings', 'mark_completed', 'mark_consultation_done']
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient_name', 'patient_email', 'patient_phone')
        }),
        ('Booking Details', {
            'fields': ('service', 'date', 'time', 'status', 'consultation_status', 'notes')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'Pending': '#ffc107',
            'Confirmed': '#28a745',
            'Completed': '#17a2b8',
            'Cancelled': '#dc3545',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.status
        )
    status_badge.short_description = 'Status'
    
    def consultation_status_badge(self, obj):
        colors = {
            'Not Yet': '#6c757d',
            'Ongoing': '#ffc107',
            'Done': '#28a745',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.consultation_status, '#6c757d'),
            obj.consultation_status
        )
    consultation_status_badge.short_description = 'Consultation'
    
    @admin.action(description='✅ Accept selected bookings')
    def accept_bookings(self, request, queryset):
        """Accept bookings and trigger automation (Patient/Billing/Record creation)"""
        try:
            with transaction.atomic():
                # Filter only pending bookings
                pending_bookings = queryset.filter(status='Pending')
                
                if not pending_bookings.exists():
                    self.message_user(
                        request,
                        "No pending bookings selected. Only pending bookings can be accepted.",
                        level=messages.WARNING
                    )
                    return
                
                count = 0
                for booking in pending_bookings:
                    booking.status = 'Confirmed'
                    booking.save()  # This triggers the signals
                    count += 1
                
                self.message_user(
                    request,
                    f'✅ Successfully accepted {count} booking(s). Patient profiles, medical records, and billing have been created automatically.',
                    level=messages.SUCCESS
                )
                
        except Exception as e:
            self.message_user(
                request,
                f'❌ Error accepting bookings: {str(e)}',
                level=messages.ERROR
            )
    
    @admin.action(description='❌ Reject selected bookings')
    def reject_bookings(self, request, queryset):
        """Reject/Cancel bookings"""
        try:
            with transaction.atomic():
                # Filter only pending or confirmed bookings
                active_bookings = queryset.exclude(status__in=['Cancelled', 'Completed'])
                
                if not active_bookings.exists():
                    self.message_user(
                        request,
                        "No active bookings selected. Only pending/confirmed bookings can be rejected.",
                        level=messages.WARNING
                    )
                    return
                
                count = active_bookings.update(status='Cancelled')
                
                self.message_user(
                    request,
                    f'❌ Successfully rejected {count} booking(s).',
                    level=messages.SUCCESS
                )
                
        except Exception as e:
            self.message_user(
                request,
                f'❌ Error rejecting bookings: {str(e)}',
                level=messages.ERROR
            )
    
    @admin.action(description='✔️ Mark as completed')
    def mark_completed(self, request, queryset):
        """Mark bookings as completed"""
        try:
            with transaction.atomic():
                # Only confirmed bookings can be marked as completed
                confirmed_bookings = queryset.filter(status='Confirmed')
                
                if not confirmed_bookings.exists():
                    self.message_user(
                        request,
                        "No confirmed bookings selected. Only confirmed bookings can be marked as completed.",
                        level=messages.WARNING
                    )
                    return
                
                count = confirmed_bookings.update(status='Completed')
                
                self.message_user(
                    request,
                    f'✔️ Successfully marked {count} booking(s) as completed.',
                    level=messages.SUCCESS
                )
                
        except Exception as e:
            self.message_user(
                request,
                f'❌ Error marking bookings as completed: {str(e)}',
                level=messages.ERROR
            )
    
    @admin.action(description='🏥 Mark consultation as DONE (Creates Patient/Billing)')
    def mark_consultation_done(self, request, queryset):
        """Mark consultation status as Done - triggers automatic patient/billing creation"""
        try:
            with transaction.atomic():
                # Filter confirmed bookings that are not yet done
                eligible_bookings = queryset.filter(status='Confirmed').exclude(consultation_status='Done')
                
                if not eligible_bookings.exists():
                    self.message_user(
                        request,
                        "No eligible bookings selected. Only confirmed bookings with consultation status 'Not Yet' or 'Ongoing' can be marked as done.",
                        level=messages.WARNING
                    )
                    return
                
                count = 0
                for booking in eligible_bookings:
                    booking.consultation_status = 'Done'
                    booking.save()  # This triggers the signal to create Patient/MedicalRecord/Billing
                    count += 1
                
                self.message_user(
                    request,
                    f'🏥 Successfully marked {count} consultation(s) as DONE. Patient profiles, medical records, and billing have been created automatically.',
                    level=messages.SUCCESS
                )
                
        except Exception as e:
            self.message_user(
                request,
                f'❌ Error marking consultations as done: {str(e)}',
                level=messages.ERROR
            )
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        
        # Check if status changed to Confirmed
        if change:
            old_obj = Booking.objects.get(pk=obj.pk)
            if old_obj.status != 'Confirmed' and obj.status == 'Confirmed':
                messages.info(request, f"Booking confirmed! Patient profile, medical record, and billing will be created automatically.")
        
        super().save_model(request, obj, form, change)


# ===== BILLING ADMIN =====
class PaymentInline(admin.TabularInline):
    """Inline payment editor for billing"""
    model = Payment
    extra = 1
    fields = ('amount_paid', 'payment_method', 'reference_number', 'notes', 'payment_date')
    readonly_fields = ('payment_date',)


@admin.register(Billing, site=clinic_admin_site)
class BillingAdmin(CustomModelAdmin):
    list_display = ('id', 'booking_patient', 'editable_service_fee', 'editable_medicine_fee', 'total_amount', 'amount_paid', 'balance', 'payment_status_badge', 'issued_date')
    list_filter = ('is_paid', 'issued_date')
    search_fields = ('booking__patient_name', 'booking__patient_email', 'notes')
    readonly_fields = ('total_amount', 'amount_paid', 'balance', 'is_paid', 'issued_date', 'updated_at')
    date_hierarchy = 'issued_date'
    inlines = [PaymentInline]
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking',)
        }),
        ('Fee Breakdown', {
            'fields': ('service_fee', 'medicine_fee', 'additional_fee', 'discount')
        }),
        ('Total & Payment', {
            'fields': ('total_amount', 'amount_paid', 'balance', 'is_paid')
        }),
        ('Additional Info', {
            'fields': ('notes', 'issued_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def booking_patient(self, obj):
        return obj.booking.patient_name
    booking_patient.short_description = 'Patient'
    
    def editable_service_fee(self, obj):
        return format_html(
            '<input type="number" '
            'class="billing-fee-input" '
            'data-billing-id="{}" '
            'data-fee-type="service" '
            'value="{}" '
            'step="0.01" '
            'min="0" '
            'style="width: 100px; padding: 4px; border: 1px solid #ddd; border-radius: 4px;" />',
            obj.id,
            obj.service_fee
        )
    editable_service_fee.short_description = 'Service Fee'
    
    def editable_medicine_fee(self, obj):
        return format_html(
            '<input type="number" '
            'class="billing-fee-input" '
            'data-billing-id="{}" '
            'data-fee-type="medicine" '
            'value="{}" '
            'step="0.01" '
            'min="0" '
            'style="width: 100px; padding: 4px; border: 1px solid #ddd; border-radius: 4px;" />',
            obj.id,
            obj.medicine_fee
        )
    editable_medicine_fee.short_description = 'Medicine Fee'
    
    def payment_status_badge(self, obj):
        if obj.is_paid:
            color = '#28a745'
            text = 'Paid'
        elif obj.amount_paid > 0:
            color = '#ffc107'
            text = 'Partially Paid'
        else:
            color = '#dc3545'
            text = 'Unpaid'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            text
        )
    payment_status_badge.short_description = 'Payment Status'
    
    class Media:
        js = ('admin/js/billing_inline_edit.js',)
        css = {
            'all': ('admin/css/billing_inline_edit.css',)
        }


# ===== PAYMENT ADMIN =====
@admin.register(Payment, site=clinic_admin_site)
class PaymentAdmin(CustomModelAdmin):
    list_display = ('id', 'billing_patient', 'amount_paid', 'payment_method', 'reference_number', 'payment_date', 'recorded_by')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('billing__booking__patient_name', 'reference_number', 'notes')
    readonly_fields = ('payment_date', 'recorded_by')
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('billing', 'amount_paid', 'payment_method', 'reference_number')
        }),
        ('Additional Details', {
            'fields': ('notes', 'payment_date', 'recorded_by'),
            'classes': ('collapse',)
        }),
    )
    
    def billing_patient(self, obj):
        return obj.billing.booking.patient_name
    billing_patient.short_description = 'Patient'
    
    def save_model(self, request, obj, form, change):
        if not obj.recorded_by:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)


# ===== STOCK TRANSACTION ADMIN =====
@admin.register(StockTransaction, site=clinic_admin_site)
class StockTransactionAdmin(CustomModelAdmin):
    list_display = ('id', 'inventory_item', 'transaction_type', 'quantity', 'transaction_date', 'performed_by')
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('inventory_item__name', 'notes')
    readonly_fields = ('transaction_date', 'performed_by')
    date_hierarchy = 'transaction_date'
    
    def save_model(self, request, obj, form, change):
        if not obj.performed_by:
            obj.performed_by = request.user
        super().save_model(request, obj, form, change)


# ===== POS (POINT OF SALE) SYSTEM =====

class POSSaleItemInline(admin.TabularInline):
    """Inline sale items for POS"""
    model = POSSaleItem
    extra = 1
    fields = ('inventory_item', 'quantity', 'unit_price', 'line_total', 'notes')
    readonly_fields = ('line_total',)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "inventory_item":
            # Show only items that are in stock or low stock
            kwargs["queryset"] = Inventory.objects.filter(
                status__in=['In Stock', 'Low Stock']
            ).order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(POSSale, site=clinic_admin_site)
class POSSaleAdmin(CustomModelAdmin):
    list_display = (
        'receipt_number', 
        'customer_name', 
        'sale_type', 
        'total_amount_display', 
        'payment_method', 
        'status_badge', 
        'sale_date',
        'created_by'
    )
    list_filter = ('status', 'sale_type', 'payment_method', 'sale_date')
    search_fields = ('receipt_number', 'customer_name', 'reference_number', 'notes')
    readonly_fields = (
        'receipt_number', 
        'subtotal', 
        'discount_amount', 
        'tax_amount', 
        'total_amount', 
        'change_amount',
        'sale_date',
        'updated_at'
    )
    date_hierarchy = 'sale_date'
    list_per_page = 25
    inlines = [POSSaleItemInline]
    actions = ['complete_sales', 'cancel_sales', 'print_receipts']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('sale_type', 'patient', 'customer_name'),
            'description': 'For registered patients, select patient. For walk-ins, enter customer name.'
        }),
        ('Pricing & Discounts', {
            'fields': (
                'subtotal',
                ('discount_percent', 'discount_amount'),
                ('tax_percent', 'tax_amount'),
                'total_amount'
            ),
            'classes': ('wide',),
            'description': 'Add sale items below in the "Sale Items" section'
        }),
        ('Payment Information', {
            'fields': (
                'payment_method',
                'amount_received',
                'change_amount',
                'reference_number'
            ),
            'classes': ('wide',)
        }),
        ('Transaction Status', {
            'fields': ('status', 'notes'),
        }),
        ('System Information', {
            'fields': ('receipt_number', 'sale_date', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make created_by readonly after creation"""
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly.append('created_by')
        return readonly
    
    def total_amount_display(self, obj):
        """Display total amount with currency"""
        return f"₱{obj.total_amount:,.2f}"
    total_amount_display.short_description = 'Total Amount'
    total_amount_display.admin_order_field = 'total_amount'
    
    def status_badge(self, obj):
        """Display colored status badge"""
        colors = {
            'Pending': '#ffc107',
            'Completed': '#28a745',
            'Cancelled': '#dc3545',
            'Refunded': '#6c757d',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.status
        )
    status_badge.short_description = 'Status'
    
    @admin.action(description='✅ Complete selected sales')
    def complete_sales(self, request, queryset):
        """Complete pending sales and deduct from inventory"""
        try:
            with transaction.atomic():
                pending_sales = queryset.filter(status='Pending')
                
                if not pending_sales.exists():
                    self.message_user(
                        request,
                        "No pending sales selected. Only pending sales can be completed.",
                        level=messages.WARNING
                    )
                    return
                
                count = 0
                for sale in pending_sales:
                    # Check if there are items
                    if not sale.items.exists():
                        continue
                    
                    # Check inventory availability
                    insufficient_stock = []
                    for item in sale.items.all():
                        if item.inventory_item.quantity < item.quantity:
                            insufficient_stock.append(
                                f"{item.inventory_item.name} (Need: {item.quantity}, Available: {item.inventory_item.quantity})"
                            )
                    
                    if insufficient_stock:
                        self.message_user(
                            request,
                            f"Receipt #{sale.receipt_number} - Insufficient stock: {', '.join(insufficient_stock)}",
                            level=messages.ERROR
                        )
                        continue
                    
                    # Complete the sale
                    sale.status = 'Completed'
                    sale.save()
                    
                    # Deduct items from inventory (handled in POSSaleItem.save)
                    for item in sale.items.all():
                        item.save()  # Triggers inventory deduction
                    
                    count += 1
                
                if count > 0:
                    self.message_user(
                        request,
                        f'✅ Successfully completed {count} sale(s). Inventory has been updated.',
                        level=messages.SUCCESS
                    )
                
        except Exception as e:
            self.message_user(
                request,
                f'❌ Error completing sales: {str(e)}',
                level=messages.ERROR
            )
    
    @admin.action(description='❌ Cancel selected sales')
    def cancel_sales(self, request, queryset):
        """Cancel pending sales"""
        try:
            with transaction.atomic():
                active_sales = queryset.filter(status='Pending')
                
                if not active_sales.exists():
                    self.message_user(
                        request,
                        "No pending sales selected. Only pending sales can be cancelled.",
                        level=messages.WARNING
                    )
                    return
                
                count = active_sales.update(status='Cancelled')
                
                self.message_user(
                    request,
                    f'❌ Successfully cancelled {count} sale(s).',
                    level=messages.SUCCESS
                )
                
        except Exception as e:
            self.message_user(
                request,
                f'❌ Error cancelling sales: {str(e)}',
                level=messages.ERROR
            )
    
    @admin.action(description='🖨️ Print receipts')
    def print_receipts(self, request, queryset):
        """Mark selected sales for receipt printing"""
        completed_sales = queryset.filter(status='Completed')
        count = completed_sales.count()
        
        if count > 0:
            receipt_numbers = ', '.join([sale.receipt_number for sale in completed_sales[:5]])
            if count > 5:
                receipt_numbers += f' and {count - 5} more'
            
            self.message_user(
                request,
                f'🖨️ Ready to print {count} receipt(s): {receipt_numbers}',
                level=messages.INFO
            )
        else:
            self.message_user(
                request,
                "No completed sales selected. Only completed sales can be printed.",
                level=messages.WARNING
            )
    
    def save_model(self, request, obj, form, change):
        """Auto-set created_by and handle status changes"""
        if not obj.created_by:
            obj.created_by = request.user
        
        # Check if status changed to Completed
        if change:
            try:
                old_obj = POSSale.objects.get(pk=obj.pk)
                if old_obj.status != 'Completed' and obj.status == 'Completed':
                    # Verify inventory before completing
                    insufficient_stock = []
                    for item in obj.items.all():
                        if item.inventory_item.quantity < item.quantity:
                            insufficient_stock.append(
                                f"{item.inventory_item.name} (Need: {item.quantity}, Available: {item.inventory_item.quantity})"
                            )
                    
                    if insufficient_stock:
                        messages.error(
                            request,
                            f"Cannot complete sale - Insufficient stock: {', '.join(insufficient_stock)}"
                        )
                        return  # Don't save
                    
                    messages.success(
                        request,
                        f"Sale completed! Receipt #{obj.receipt_number}. Inventory has been updated."
                    )
                elif old_obj.status == 'Completed' and obj.status in ['Cancelled', 'Refunded']:
                    messages.info(
                        request,
                        f"Sale {obj.status.lower()}. Items will be returned to inventory."
                    )
                    # Return items to inventory
                    for item in obj.items.all():
                        item.return_to_inventory(item.quantity)
            except POSSale.DoesNotExist:
                pass
        
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        """Save the formset and update sale totals"""
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, POSSaleItem):
                if not instance.unit_price:
                    instance.unit_price = instance.inventory_item.price
                instance.save()
        
        # Save deleted items
        for obj in formset.deleted_objects:
            obj.delete()
        
        formset.save_m2m()
        
        # Recalculate sale totals
        if hasattr(form.instance, 'calculate_subtotal'):
            form.instance.calculate_subtotal()


@admin.register(POSSaleItem, site=clinic_admin_site)
class POSSaleItemAdmin(CustomModelAdmin):
    list_display = ('id', 'sale_receipt', 'inventory_item', 'quantity', 'unit_price_display', 'line_total_display')
    list_filter = ('sale__sale_date', 'inventory_item__category')
    search_fields = ('sale__receipt_number', 'inventory_item__name', 'notes')
    readonly_fields = ('line_total',)
    
    fieldsets = (
        ('Sale Information', {
            'fields': ('sale',)
        }),
        ('Item Details', {
            'fields': ('inventory_item', 'quantity', 'unit_price', 'line_total', 'notes')
        }),
    )
    
    def sale_receipt(self, obj):
        return obj.sale.receipt_number
    sale_receipt.short_description = 'Receipt #'
    
    def unit_price_display(self, obj):
        return f"₱{obj.unit_price:,.2f}"
    unit_price_display.short_description = 'Unit Price'
    unit_price_display.admin_order_field = 'unit_price'
    
    def line_total_display(self, obj):
        return f"₱{obj.line_total:,.2f}"
    line_total_display.short_description = 'Line Total'
    line_total_display.admin_order_field = 'line_total'


# Register the User model with our custom admin site using the restricted admin
clinic_admin_site.register(User, RestrictedUserAdmin)
clinic_admin_site.register(Group, GroupAdmin)

# Also register with default admin for compatibility
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Service)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Billing, BillingAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Prescription, PrescriptionAdmin)
admin.site.register(POSSale, POSSaleAdmin)
admin.site.register(POSSaleItem, POSSaleItemAdmin)

