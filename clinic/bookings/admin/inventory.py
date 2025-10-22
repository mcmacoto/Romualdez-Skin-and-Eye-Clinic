"""
Admin classes for inventory-related models
"""
from django.contrib import admin
from django.contrib import messages
from django import forms

from .base import CustomModelAdmin
from ..models import Inventory, StockTransaction, Prescription
from ..utils import format_colored_text, format_currency


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
        return format_colored_text(obj.status, colors)
    colored_status.short_description = 'Status'


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
