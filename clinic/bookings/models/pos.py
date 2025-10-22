"""
Point of Sale (POS) models
Handles POS sales transactions and sale items
"""
from django.db import models
from django.contrib.auth.models import User

from .patients import Patient
from .inventory import Inventory, StockTransaction


class POSSale(models.Model):
    """Main POS Sales transaction"""
    
    SALE_TYPE_CHOICES = [
        ('Walk-in', 'Walk-in Customer'),
        ('Patient', 'Registered Patient'),
    ]
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('GCash', 'GCash'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Card', 'Credit/Debit Card'),
        ('Other', 'Other'),
    ]
    
    # Transaction Info
    receipt_number = models.CharField(
        max_length=50, 
        unique=True, 
        editable=False,
        help_text="Auto-generated receipt number"
    )
    sale_date = models.DateTimeField(auto_now_add=True)
    
    # Customer Info
    sale_type = models.CharField(
        max_length=20, 
        choices=SALE_TYPE_CHOICES, 
        default='Walk-in',
        help_text="Type of customer"
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pos_sales',
        help_text="Optional: Link to registered patient"
    )
    customer_name = models.CharField(
        max_length=100,
        help_text="Customer name (required for walk-ins)"
    )
    
    # Pricing
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        editable=False,
        help_text="Subtotal before discount"
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Discount percentage (0-100)"
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        editable=False,
        help_text="Discount amount (auto-calculated)"
    )
    tax_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Tax percentage (0-100)"
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        editable=False,
        help_text="Tax amount (auto-calculated)"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        editable=False,
        help_text="Final total amount"
    )
    
    # Payment
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='Cash'
    )
    amount_received = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Amount received from customer"
    )
    change_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        editable=False,
        help_text="Change given to customer"
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Payment reference number (for electronic payments)"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending',
        db_index=True
    )
    
    # Notes
    notes = models.TextField(blank=True, help_text="Additional notes")
    
    # System Fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pos_sales'
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-sale_date']
        verbose_name = 'POS Sale'
        verbose_name_plural = 'POS Sales'
    
    def __str__(self):
        return f"Receipt #{self.receipt_number} - {self.customer_name} - ₱{self.total_amount}"
    
    def save(self, *args, **kwargs):
        """Generate receipt number and calculate totals"""
        # Generate receipt number if new
        if not self.receipt_number:
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.receipt_number = f"REC-{timestamp}"
        
        # Calculate discount
        self.discount_amount = (self.subtotal * self.discount_percent) / 100
        
        # Calculate subtotal after discount
        amount_after_discount = self.subtotal - self.discount_amount
        
        # Calculate tax
        self.tax_amount = (amount_after_discount * self.tax_percent) / 100
        
        # Calculate total
        self.total_amount = amount_after_discount + self.tax_amount
        
        # Calculate change
        self.change_amount = max(0, self.amount_received - self.total_amount)
        
        super().save(*args, **kwargs)
    
    def calculate_subtotal(self):
        """Calculate subtotal from all sale items"""
        subtotal = sum(item.line_total for item in self.items.all())
        self.subtotal = subtotal
        self.save()
        return subtotal
    
    def get_status_badge_class(self):
        """Return CSS class for status badge"""
        status_classes = {
            'Pending': 'status-pending',
            'Completed': 'status-completed',
            'Cancelled': 'status-cancelled',
            'Refunded': 'status-refunded',
        }
        return status_classes.get(self.status, 'status-pending')


class POSSaleItem(models.Model):
    """Individual items in a POS sale"""
    
    sale = models.ForeignKey(
        POSSale,
        on_delete=models.CASCADE,
        related_name='items'
    )
    inventory_item = models.ForeignKey(
        Inventory,
        on_delete=models.PROTECT,
        help_text="Item from inventory"
    )
    quantity = models.IntegerField(
        default=1,
        help_text="Quantity sold"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price per unit at time of sale"
    )
    line_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        help_text="Line total (quantity × unit price)"
    )
    notes = models.CharField(
        max_length=255,
        blank=True,
        help_text="Item-specific notes"
    )
    
    class Meta:
        ordering = ['id']
        verbose_name = 'Sale Item'
        verbose_name_plural = 'Sale Items'
    
    def __str__(self):
        return f"{self.inventory_item.name} x{self.quantity} - ₱{self.line_total}"
    
    def save(self, *args, **kwargs):
        """Calculate line total and update inventory"""
        # Set unit price from current inventory price if not set
        if not self.unit_price:
            self.unit_price = self.inventory_item.price
        
        # Calculate line total
        self.line_total = self.unit_price * self.quantity
        
        # Check if this is a new item
        is_new = self.pk is None
        old_quantity = 0
        
        if not is_new:
            # Get the old quantity before update
            old_item = POSSaleItem.objects.get(pk=self.pk)
            old_quantity = old_item.quantity
        
        super().save(*args, **kwargs)
        
        # Update sale subtotal
        self.sale.calculate_subtotal()
        
        # Update inventory only if sale is completed
        if self.sale.status == 'Completed':
            if is_new:
                # Deduct from inventory for new item
                self.deduct_from_inventory(self.quantity)
            elif old_quantity != self.quantity:
                # Adjust inventory for quantity change
                quantity_diff = self.quantity - old_quantity
                if quantity_diff > 0:
                    self.deduct_from_inventory(quantity_diff)
                else:
                    self.return_to_inventory(abs(quantity_diff))
    
    def deduct_from_inventory(self, qty):
        """Deduct quantity from inventory"""
        if self.inventory_item.quantity >= qty:
            self.inventory_item.quantity -= qty
            self.inventory_item.save()
            
            # Create stock transaction
            StockTransaction.objects.create(
                inventory_item=self.inventory_item,
                transaction_type='Stock Out',
                quantity=qty,
                performed_by=self.sale.created_by,
                notes=f"POS Sale - Receipt #{self.sale.receipt_number}"
            )
    
    def return_to_inventory(self, qty):
        """Return quantity to inventory (for refunds/cancellations)"""
        self.inventory_item.quantity += qty
        self.inventory_item.save()
        
        # Create stock transaction
        StockTransaction.objects.create(
            inventory_item=self.inventory_item,
            transaction_type='Stock In',
            quantity=qty,
            performed_by=self.sale.created_by,
            notes=f"POS Return - Receipt #{self.sale.receipt_number}"
        )
    
    def delete(self, *args, **kwargs):
        """Return items to inventory when deleted"""
        if self.sale.status == 'Completed':
            self.return_to_inventory(self.quantity)
        super().delete(*args, **kwargs)
        # Update sale subtotal
        self.sale.calculate_subtotal()
