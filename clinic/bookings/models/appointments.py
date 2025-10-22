"""
Appointment and booking models
Handles appointment scheduling and booking management
"""
from django.db import models
from django.contrib.auth.models import User

from .base import Service


class Appointment(models.Model):
    """Legacy appointment model (consider migrating to Booking)"""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    date = models.DateField(db_index=True)
    time = models.TimeField()
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='Pending', 
        db_index=True
    )
    
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
    date = models.DateField(help_text="Appointment date", db_index=True)
    time = models.TimeField(help_text="Appointment time")
    service = models.ForeignKey(
        Service, 
        on_delete=models.PROTECT, 
        help_text="Service to be provided",
        related_name='bookings'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='Pending', 
        db_index=True
    )
    consultation_status = models.CharField(
        max_length=10, 
        choices=CONSULTATION_STATUS_CHOICES, 
        default='Not Yet',
        help_text="Track consultation progress",
        db_index=True
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
