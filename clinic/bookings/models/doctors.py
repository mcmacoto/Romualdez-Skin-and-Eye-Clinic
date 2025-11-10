"""
Doctor model for managing medical staff
"""
from django.db import models
from django.contrib.auth.models import User


class Doctor(models.Model):
    """Medical staff/doctor profiles"""
    
    # Basic Information
    first_name = models.CharField(max_length=100, help_text="Doctor's first name")
    last_name = models.CharField(max_length=100, help_text="Doctor's last name")
    
    # Professional Information
    specialization = models.CharField(
        max_length=200, 
        help_text="Medical specialization (e.g., Dermatologist, Ophthalmologist)"
    )
    license_number = models.CharField(
        max_length=50, 
        unique=True, 
        help_text="Professional license number"
    )
    
    # Contact Information
    phone_number = models.CharField(max_length=15, help_text="Contact number")
    email = models.EmailField(help_text="Email address")
    
    # Availability
    is_available = models.BooleanField(
        default=True, 
        help_text="Currently accepting appointments"
    )
    
    # Work Schedule (stored as JSON or text)
    schedule_notes = models.TextField(
        blank=True,
        help_text="Working hours and availability notes"
    )
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_doctors'
    )
    
    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['is_available']),
        ]
    
    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name} - {self.specialization}"
    
    def get_full_name(self):
        """Return doctor's full name with title"""
        return f"Dr. {self.first_name} {self.last_name}"
    
    def get_short_name(self):
        """Return doctor's name with last name initial"""
        return f"Dr. {self.first_name} {self.last_name[0]}."
    
    @property
    def appointment_count(self):
        """Get total number of appointments"""
        return self.bookings.count()
    
    @property
    def active_appointments_count(self):
        """Get number of active (non-cancelled) appointments"""
        return self.bookings.exclude(status='Cancelled').count()
