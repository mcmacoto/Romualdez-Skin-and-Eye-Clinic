"""
Blocked Dates model for calendar control
Allows admin to block specific dates from booking
"""
from django.db import models
from django.contrib.auth.models import User


class BlockedDate(models.Model):
    """
    Represents a date that is blocked from bookings.
    Used for holidays, clinic closures, or other unavailable dates.
    """
    date = models.DateField(
        unique=True,
        help_text="Date to block from bookings",
        db_index=True
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Reason for blocking (e.g., Holiday, Clinic Closed)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='blocked_dates'
    )
    
    class Meta:
        ordering = ['date']
        verbose_name = 'Blocked Date'
        verbose_name_plural = 'Blocked Dates'
    
    def __str__(self):
        if self.reason:
            return f"{self.date.strftime('%B %d, %Y')} - {self.reason}"
        return f"{self.date.strftime('%B %d, %Y')}"
    
    @classmethod
    def is_date_blocked(cls, date):
        """Check if a specific date is blocked"""
        return cls.objects.filter(date=date).exists()
    
    @classmethod
    def get_blocked_dates_range(cls, start_date, end_date):
        """Get all blocked dates in a date range"""
        return cls.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).values_list('date', flat=True)
