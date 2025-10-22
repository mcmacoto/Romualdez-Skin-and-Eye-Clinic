"""
Admin classes for billing-related models
"""
from django.contrib import admin
from django.utils.html import format_html

from .base import CustomModelAdmin
from ..models import Billing, Payment
from ..utils import format_status_badge, get_status_color


class PaymentInline(admin.TabularInline):
    """Inline payment editor for billing"""
    model = Payment
    extra = 1
    fields = ('amount_paid', 'payment_method', 'reference_number', 'notes', 'payment_date')
    readonly_fields = ('payment_date',)


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
            status = 'Paid'
        elif obj.amount_paid > 0:
            status = 'Partial'
        else:
            status = 'Unpaid'
        
        colors = {
            'Paid': get_status_color('Paid', 'payment'),
            'Partial': get_status_color('Partial', 'payment'),
            'Unpaid': get_status_color('Unpaid', 'payment'),
        }
        return format_status_badge(status, colors)
    payment_status_badge.short_description = 'Payment Status'
    
    class Media:
        js = ('admin/js/billing_inline_edit.js',)
        css = {
            'all': ('admin/css/billing_inline_edit.css',)
        }


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
