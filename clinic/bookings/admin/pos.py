"""
Admin classes for POS (Point of Sale) models
"""
from django.contrib import admin
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum

from .base import CustomModelAdmin
from ..models import POSSale, POSSaleItem, Inventory
from ..utils import format_currency, format_status_badge, get_status_color


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
        return format_currency(obj.total_amount)
    total_amount_display.short_description = 'Total Amount'
    total_amount_display.admin_order_field = 'total_amount'
    
    def status_badge(self, obj):
        """Display colored status badge"""
        colors = {
            'Pending': get_status_color('Pending', 'pos'),
            'Completed': get_status_color('Completed', 'pos'),
            'Cancelled': get_status_color('Cancelled', 'pos'),
            'Refunded': get_status_color('Refunded', 'pos'),
        }
        return format_status_badge(obj.status, colors)
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
