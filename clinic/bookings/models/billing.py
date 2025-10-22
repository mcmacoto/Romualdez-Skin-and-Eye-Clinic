"""
Billing and payment models
Handles billing records and payment transactions
"""
from django.db import models
from django.contrib.auth.models import User

from .appointments import Booking


class Billing(models.Model):
    """Billing record automatically created when booking is confirmed"""
    
    # Relationship
    booking = models.OneToOneField(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='billing',
        help_text="Associated booking"
    )
    
    # Fee Breakdown
    service_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=500.00,
        help_text="Fee for the service provided"
    )
    medicine_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Cost of medicines used"
    )
    additional_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Any additional charges"
    )
    discount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Discount amount"
    )
    
    # Computed Field
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        editable=False,
        help_text="Total amount (auto-calculated)"
    )
    
    # Payment Status
    is_paid = models.BooleanField(
        default=False,
        help_text="Automatically updated when payments cover total",
        db_index=True
    )
    amount_paid = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        editable=False,
        help_text="Total amount paid (auto-calculated)"
    )
    balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00,
        editable=False,
        help_text="Remaining balance (auto-calculated)"
    )
    
    # System Fields
    issued_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, help_text="Billing notes")
    
    class Meta:
        ordering = ['-issued_date']
        verbose_name = 'Billing'
        verbose_name_plural = 'Billings'
    
    def __str__(self):
        return f"Bill #{self.id} - {self.booking.patient_name} - ₱{self.total_amount}"
    
    def save(self, *args, **kwargs):
        """Calculate total amount before saving"""
        self.total_amount = (
            self.service_fee + 
            self.medicine_fee + 
            self.additional_fee - 
            self.discount
        )
        # Set initial balance to total_amount if this is a new billing
        if not self.pk:
            self.balance = self.total_amount
        super().save(*args, **kwargs)
    
    def update_payment_status(self):
        """Update payment status based on total payments - uses update() to avoid signal recursion"""
        total_payments = sum(
            payment.amount_paid 
            for payment in self.payments.all()
        )
        amount_paid = total_payments
        balance = self.total_amount - total_payments
        is_paid = balance <= 0
        
        # Use update() to avoid triggering post_save signal
        Billing.objects.filter(pk=self.pk).update(
            amount_paid=amount_paid,
            balance=balance,
            is_paid=is_paid
        )
        
        # Update instance attributes to reflect changes
        self.amount_paid = amount_paid
        self.balance = balance
        self.is_paid = is_paid
    
    def get_status_text(self):
        """Get human-readable payment status"""
        if self.is_paid:
            return "Fully Paid"
        elif self.amount_paid > 0:
            return "Partially Paid"
        else:
            return "Unpaid"
    
    def get_status_badge_class(self):
        """Return CSS class for payment status badge"""
        if self.is_paid:
            return 'billing-paid'
        elif self.amount_paid > 0:
            return 'billing-partial'
        else:
            return 'billing-unpaid'


class Payment(models.Model):
    """Payment records linked to billing"""
    
    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('GCash', 'GCash'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Card', 'Credit/Debit Card'),
        ('Other', 'Other'),
    ]
    
    # Relationship
    billing = models.ForeignKey(
        Billing, 
        on_delete=models.CASCADE, 
        related_name='payments',
        help_text="Associated billing record"
    )
    
    # Payment Details
    amount_paid = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Amount paid in this transaction"
    )
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHOD_CHOICES,
        help_text="Method of payment"
    )
    reference_number = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Transaction reference number (optional)"
    )
    notes = models.TextField(
        blank=True,
        help_text="Payment notes or remarks"
    )
    
    # System Fields
    payment_date = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='recorded_payments'
    )
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def __str__(self):
        return f"Payment #{self.id} - ₱{self.amount_paid} ({self.payment_method}) - {self.payment_date.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        """Update billing status after saving payment"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update billing payment status
        if is_new or 'amount_paid' in kwargs.get('update_fields', []):
            self.billing.update_payment_status()
