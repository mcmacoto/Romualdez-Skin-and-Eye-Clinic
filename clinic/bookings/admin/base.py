"""
Base admin components and custom admin site
"""
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils import timezone
from django.db.models import Count, Sum
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.utils.html import format_html
from datetime import date

from ..models import (
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


class GroupAdmin(CustomModelAdmin):
    """Custom Group admin that only superusers can access"""
    
    def has_module_permission(self, request):
        return request.user.is_superuser
