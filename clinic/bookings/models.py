from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# Create your models here.

class Appointment(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    date = models.DateField()
    time = models.TimeField()
    message =  models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    
    CONSULTATION_STATUS_CHOICES = [
        ('Not Yet', 'Not Yet'),
        ('Ongoing', 'Ongoing'),
        ('Done', 'Done'),
    ]
    consultation_status = models.CharField(
        max_length=10, 
        choices=CONSULTATION_STATUS_CHOICES, 
        default='Not Yet',
        help_text="Track consultation progress"
    )
    
    def __str__(self):
        return f"{self.name} - {self.date} {self.time}"

class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='services/')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Service price in Philippine Pesos (₱)")
    
    def __str__(self):
        return self.name

class Patient(models.Model):
    """Extended patient information linked to User account"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    
    # Personal Information
    date_of_birth = models.DateField()
    gender_choices = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=gender_choices)
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    
    # Medical Information
    blood_type_choices = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('UK', 'Unknown'),
    ]
    blood_type = models.CharField(max_length=3, choices=blood_type_choices, default='UK')
    allergies = models.TextField(blank=True, help_text="List any known allergies")
    current_medications = models.TextField(blank=True, help_text="Current medications and dosages")
    medical_history = models.TextField(blank=True, help_text="Previous medical conditions and surgeries")
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_patients')
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.user.email}"

class MedicalRecord(models.Model):
    """Individual medical record entries for patients"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    
    # Visit Information
    visit_date = models.DateTimeField()
    chief_complaint = models.TextField(help_text="Patient's main concern or reason for visit")
    
    # Clinical Findings
    symptoms = models.TextField(blank=True, help_text="Observed symptoms")
    diagnosis = models.TextField(blank=True, help_text="Clinical diagnosis")
    treatment_plan = models.TextField(blank=True, help_text="Prescribed treatment and recommendations")
    
    # Vital Signs (optional)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True, help_text="°C")
    blood_pressure_systolic = models.IntegerField(blank=True, null=True)
    blood_pressure_diastolic = models.IntegerField(blank=True, null=True)
    heart_rate = models.IntegerField(blank=True, null=True, help_text="BPM")
    weight = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, help_text="kg")
    height = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, help_text="cm")
    
    # Follow-up and Notes
    follow_up_date = models.DateField(blank=True, null=True)
    additional_notes = models.TextField(blank=True)
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_records')
    
    class Meta:
        ordering = ['-visit_date']
    
    def __str__(self):
        return f"{self.patient.user.get_full_name()} - {self.visit_date.strftime('%Y-%m-%d')} - {self.chief_complaint[:50]}"

def medical_image_upload_path(instance, filename):
    """Generate upload path for medical images"""
    return f'medical_records/{instance.medical_record.patient.user.username}/{instance.medical_record.visit_date.strftime("%Y-%m-%d")}/{filename}'

class MedicalImage(models.Model):
    """Medical images attached to records"""
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='images')
    
    # Image Information
    image = models.ImageField(upload_to=medical_image_upload_path)
    title = models.CharField(max_length=100, help_text="Brief description of the image")
    description = models.TextField(blank=True, help_text="Detailed description or notes about the image")
    
    # Image Metadata
    image_type_choices = [
        ('clinical', 'Clinical Photo'),
        ('dermoscopy', 'Dermoscopy'),
        ('before', 'Before Treatment'),
        ('after', 'After Treatment'),
        ('diagnostic', 'Diagnostic Image'),
        ('other', 'Other'),
    ]
    image_type = models.CharField(max_length=20, choices=image_type_choices, default='clinical')
    
    # System fields
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_images')
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.medical_record.patient.user.get_full_name()}"

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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='In Stock')
    quantity = models.IntegerField(default=0, help_text="Current quantity in stock")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    class Meta:
        ordering = ['-date_stock_in']
        verbose_name = 'Inventory Item'
        verbose_name_plural = 'Inventory Items'
    
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
    
    class Meta:
        ordering = ['-transaction_date']
        verbose_name = 'Stock Transaction'
        verbose_name_plural = 'Stock Transactions'
    
    def __str__(self):
        return f"{self.transaction_type} - {self.inventory_item.name} (Qty: {self.quantity}) - {self.transaction_date.strftime('%Y-%m-%d %H:%M')}"


class Prescription(models.Model):
    """Medicines prescribed to patients"""
    
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        help_text="Associated medical record"
    )
    medicine = models.ForeignKey(
        Inventory,
        on_delete=models.PROTECT,
        limit_choices_to={'category': 'Medicine'},
        help_text="Medicine from inventory"
    )
    quantity = models.IntegerField(default=1, help_text="Quantity prescribed")
    dosage = models.CharField(max_length=100, help_text="e.g., '1 tablet twice daily'")
    duration = models.CharField(max_length=100, blank=True, help_text="e.g., '7 days', '2 weeks'")
    instructions = models.TextField(blank=True, help_text="Additional instructions for the patient")
    
    # Pricing
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price per unit at time of prescription"
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        help_text="Total cost (auto-calculated)"
    )
    
    # System fields
    prescribed_date = models.DateTimeField(auto_now_add=True)
    prescribed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='prescribed_medications'
    )
    
    class Meta:
        ordering = ['-prescribed_date']
        verbose_name = 'Prescription'
        verbose_name_plural = 'Prescriptions'
    
    def __str__(self):
        return f"{self.medicine.name} x{self.quantity} - {self.medical_record.patient.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        """Calculate total price and update inventory"""
        # Set unit price from current medicine price if not set
        if not self.unit_price:
            self.unit_price = self.medicine.price
        
        # Calculate total
        self.total_price = self.unit_price * self.quantity
        
        # Save first
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # If new prescription, deduct from inventory
        if is_new:
            if self.medicine.quantity >= self.quantity:
                self.medicine.quantity -= self.quantity
                self.medicine.save()
                
                # Create stock transaction
                StockTransaction.objects.create(
                    inventory_item=self.medicine,
                    transaction_type='Stock Out',
                    quantity=self.quantity,
                    performed_by=self.prescribed_by,
                    notes=f"Prescribed to {self.medical_record.patient.user.get_full_name()}"
                )



# ===== CLINIC OPERATIONS: BOOKING, BILLING, PAYMENT =====

class Booking(models.Model):
    """Patient booking/appointment with automatic billing generation"""
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    CONSULTATION_STATUS_CHOICES = [
        ('Not Yet', 'Not Yet'),
        ('Ongoing', 'Ongoing'),
        ('Done', 'Done'),
    ]
    
    # Patient Information
    patient_name = models.CharField(max_length=100, help_text="Full name of the patient")
    patient_email = models.EmailField(help_text="Patient's email address")
    patient_phone = models.CharField(max_length=15, help_text="Contact number")
    
    # Booking Details
    date = models.DateField(help_text="Appointment date")
    time = models.TimeField(help_text="Appointment time")
    service = models.ForeignKey(
        Service, 
        on_delete=models.PROTECT, 
        help_text="Service to be provided",
        related_name='bookings'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    consultation_status = models.CharField(
        max_length=10, 
        choices=CONSULTATION_STATUS_CHOICES, 
        default='Not Yet',
        help_text="Track consultation progress"
    )
    notes = models.TextField(blank=True, help_text="Additional notes or special requests")
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_bookings'
    )
    
    class Meta:
        ordering = ['-date', '-time']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
    
    def __str__(self):
        return f"{self.patient_name} - {self.date} {self.time} ({self.status})"
    
    def get_status_badge_class(self):
        """Return CSS class for status badge"""
        status_classes = {
            'Pending': 'status-pending',
            'Confirmed': 'status-confirmed',
            'Completed': 'status-completed',
            'Cancelled': 'status-cancelled',
        }
        return status_classes.get(self.status, 'status-pending')


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
        help_text="Automatically updated when payments cover total"
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
    
    def get_status_text(self):
        """Return payment status text"""
        if self.is_paid:
            return 'Paid'
        elif self.amount_paid > 0:
            return 'Partially Paid'
        else:
            return 'Unpaid'


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


# ===== POINT OF SALE (POS) SYSTEM =====

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
        default='Pending'
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
