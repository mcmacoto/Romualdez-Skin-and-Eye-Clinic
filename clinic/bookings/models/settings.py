"""
Clinic Settings Model
Stores global clinic configuration
"""
from django.db import models


class ClinicSettings(models.Model):
    """Singleton model for clinic-wide settings"""
    
    # Operating Hours
    opening_time = models.TimeField(
        default='09:00',
        help_text="Clinic opening time (e.g., 09:00)"
    )
    closing_time = models.TimeField(
        default='17:00',
        help_text="Clinic closing time (e.g., 17:00)"
    )
    
    # Appointment Settings
    appointment_slot_duration = models.IntegerField(
        default=60,
        help_text="Duration of each appointment slot in minutes"
    )
    
    # Contact Information
    clinic_name = models.CharField(
        max_length=200,
        default="Romualdez Skin and Eye Clinic",
        help_text="Official clinic name"
    )
    clinic_address = models.TextField(
        blank=True,
        help_text="Full clinic address"
    )
    clinic_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Main contact number"
    )
    clinic_email = models.EmailField(
        blank=True,
        help_text="Main email address"
    )
    
    # System Fields
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Clinic Settings"
        verbose_name_plural = "Clinic Settings"
    
    def __str__(self):
        return f"Clinic Settings (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)"""
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        """Load or create the singleton settings instance"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def get_time_slots(self):
        """Generate list of time slots based on operating hours"""
        from datetime import datetime, timedelta
        
        slots = []
        current = datetime.combine(datetime.today(), self.opening_time)
        end = datetime.combine(datetime.today(), self.closing_time)
        
        while current < end:
            slots.append({
                'time': current.strftime('%H:%M'),
                'display': current.strftime('%I:%M %p')
            })
            current += timedelta(minutes=self.appointment_slot_duration)
        
        return slots
