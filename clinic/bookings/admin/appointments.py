"""
Admin classes for appointment-related models
"""
from django.contrib import admin
from django.contrib import messages
from django.db import transaction

from .base import CustomModelAdmin
from ..models import Appointment, Service, Booking
from ..utils import format_currency, format_status_badge, get_status_color


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
        return format_currency(obj.price)
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'price'
    
    def has_module_permission(self, request):
        # Only superusers can manage services
        return request.user.is_superuser


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
            'Pending': get_status_color('Pending', 'booking'),
            'Confirmed': get_status_color('Confirmed', 'booking'),
            'Completed': get_status_color('Completed', 'booking'),
            'Cancelled': get_status_color('Cancelled', 'booking'),
        }
        return format_status_badge(obj.status, colors)
    status_badge.short_description = 'Status'
    
    def consultation_status_badge(self, obj):
        colors = {
            'Not Yet': get_status_color('Not Yet', 'consultation'),
            'Ongoing': get_status_color('Ongoing', 'consultation'),
            'Done': get_status_color('Done', 'consultation'),
        }
        return format_status_badge(obj.consultation_status, colors)
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
