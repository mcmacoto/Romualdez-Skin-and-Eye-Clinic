"""
Calendar model for managing all date-related clinic operations
Consolidates blocked dates, holidays, and time-based scheduling
"""
from django.db import models
from django.contrib.auth.models import User


class Calendar(models.Model):
    """
    Unified calendar model for managing clinic dates and scheduling.
    Replaces BlockedDate and handles all date-related operations.
    """
    EVENT_TYPE_CHOICES = [
        ('blocked', 'Blocked Date'),
        ('holiday', 'Holiday'),
        ('special_hours', 'Special Operating Hours'),
    ]
    
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        default='blocked',
        help_text="Type of calendar event",
        db_index=True
    )
    date = models.DateField(
        help_text="Date of the calendar event",
        db_index=True
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Reason for the calendar event (e.g., Holiday, Clinic Closed)"
    )
    
    # Time-related fields (optional, for future special hours functionality)
    start_time = models.TimeField(
        blank=True,
        null=True,
        help_text="Start time (for special operating hours)"
    )
    end_time = models.TimeField(
        blank=True,
        null=True,
        help_text="End time (for special operating hours)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='calendar_events'
    )
    
    class Meta:
        ordering = ['date']
        verbose_name = 'Calendar Event'
        verbose_name_plural = 'Calendar Events'
        indexes = [
            models.Index(fields=['date', 'event_type']),
        ]
        # Prevent duplicate events on the same date with same type
        unique_together = [['date', 'event_type']]
    
    def __str__(self):
        if self.reason:
            return f"{self.date.strftime('%B %d, %Y')} - {self.get_event_type_display()}: {self.reason}"
        return f"{self.date.strftime('%B %d, %Y')} - {self.get_event_type_display()}"
    
    @classmethod
    def is_date_blocked(cls, date):
        """Check if a specific date is blocked"""
        return cls.objects.filter(
            date=date,
            event_type='blocked'
        ).exists()
    
    @classmethod
    def get_blocked_dates_range(cls, start_date, end_date):
        """Get all blocked dates in a date range"""
        return cls.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            event_type='blocked'
        ).values_list('date', flat=True)
    
    @classmethod
    def get_special_hours(cls, date):
        """Get special operating hours for a specific date"""
        try:
            event = cls.objects.get(date=date, event_type='special_hours')
            return {
                'start_time': event.start_time,
                'end_time': event.end_time,
                'reason': event.reason
            }
        except cls.DoesNotExist:
            return None
