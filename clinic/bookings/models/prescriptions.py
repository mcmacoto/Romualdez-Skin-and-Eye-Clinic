"""
Prescription models
Handles medicines prescribed to patients
"""
from django.db import models
from django.contrib.auth.models import User

from .patients import MedicalRecord
from .inventory import Inventory, StockTransaction


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
        help_text="Medicine from inventory",
        null=True,
        blank=True
    )
    # Custom medicine name for medicines not in inventory
    custom_medicine_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Medicine name if not in inventory"
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
        medicine_name = self.custom_medicine_name if self.custom_medicine_name else self.medicine.name
        return f"{medicine_name} x{self.quantity} - {self.medical_record.patient.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        """Calculate total price and update inventory with transaction safety"""
        from django.db import transaction
        from django.core.exceptions import ValidationError
        
        # Set unit price from current medicine price if not set and using inventory medicine
        if self.medicine and not self.unit_price:
            self.unit_price = self.medicine.price
        
        # If custom medicine and no price set, default to 0
        if not self.medicine and not self.unit_price:
            self.unit_price = 0
        
        # Calculate total
        self.total_price = self.unit_price * self.quantity
        
        # Check if this is a new prescription
        is_new = self.pk is None
        
        # Use atomic transaction to ensure prescription and inventory update happen together
        with transaction.atomic():
            # If new prescription with inventory medicine, check stock availability first
            if is_new and self.medicine:
                # Lock the inventory item to prevent race conditions
                medicine = Inventory.objects.select_for_update().get(pk=self.medicine.pk)
                
                # Validate sufficient stock before saving
                if medicine.quantity < self.quantity:
                    raise ValidationError(
                        f"Insufficient stock for {medicine.name}. "
                        f"Available: {medicine.quantity}, Required: {self.quantity}"
                    )
                
                # Save prescription first
                super().save(*args, **kwargs)
                
                # Deduct from inventory
                medicine.quantity -= self.quantity
                medicine.save()
                
                # Create stock transaction
                StockTransaction.objects.create(
                    inventory_item=medicine,
                    transaction_type='Stock Out',
                    quantity=self.quantity,
                    performed_by=self.prescribed_by,
                    notes=f"Prescribed to {self.medical_record.patient.user.get_full_name()}"
                )
            else:
                # No inventory update needed, just save
                super().save(*args, **kwargs)
