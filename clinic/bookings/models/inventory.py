"""
Inventory and stock transaction models
Handles inventory management for medicines, equipment, and misc items
"""
from django.db import models
from django.contrib.auth.models import User


class Inventory(models.Model):
    """Inventory Management System for Medicine, Equipment, and Miscellaneous items"""
    
    STATUS_CHOICES = [
        ('In Stock', 'In Stock'),
        ('Low Stock', 'Low Stock'),
        ('Out of Stock', 'Out of Stock'),
    ]
    
    CATEGORY_CHOICES = [
        ('Medicine', 'Medicine'),
        ('Equipment', 'Equipment'),
        ('Miscellaneous', 'Miscellaneous'),
    ]
    
    item_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Unit price in PHP")
    expiry_date = models.DateField(blank=True, null=True, help_text="Optional expiry date for medicines")
    date_stock_in = models.DateField(auto_now_add=True)
    stock = models.IntegerField(default=0, help_text="Minimum stock level threshold")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='In Stock', db_index=True)
    quantity = models.IntegerField(default=0, help_text="Current quantity in stock")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    
    class Meta:
        ordering = ['-date_stock_in']
        verbose_name = 'Inventory Item'
        verbose_name_plural = 'Inventory Items'
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['status', 'quantity']),
            models.Index(fields=['expiry_date']),  # For expiry alerts
        ]
    
    def __str__(self):
        return f"{self.name} ({self.category}) - Qty: {self.quantity} - ₱{self.price}"
    
    def save(self, *args, **kwargs):
        """Auto-update status based on quantity"""
        if self.quantity <= 0:
            self.status = 'Out of Stock'
        elif self.quantity <= self.stock:
            self.status = 'Low Stock'
        else:
            self.status = 'In Stock'
        super().save(*args, **kwargs)


class StockTransaction(models.Model):
    """Track all stock in/out transactions for inventory items"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('Stock In', 'Stock In'),
        ('Stock Out', 'Stock Out'),
    ]
    
    inventory_item = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    quantity = models.IntegerField()
    transaction_date = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stock_transactions')
    notes = models.TextField(blank=True, help_text="Optional notes about this transaction")
    
    # Approval workflow for stock adjustments
    requires_approval = models.BooleanField(
        default=False,
        help_text="Whether this transaction needs supervisor approval",
        db_index=True
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="Whether this transaction has been approved",
        db_index=True
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_stock_transactions',
        help_text="Supervisor who approved this transaction"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this transaction was approved"
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason if transaction was rejected"
    )
    
    class Meta:
        ordering = ['-transaction_date']
        verbose_name = 'Stock Transaction'
        verbose_name_plural = 'Stock Transactions'
    
    def __str__(self):
        return f"{self.transaction_type} - {self.inventory_item.name} (Qty: {self.quantity}) - {self.transaction_date.strftime('%Y-%m-%d %H:%M')}"
