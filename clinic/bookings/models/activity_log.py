"""
Activity Log Model
Tracks all user actions for audit trail
"""
from django.db import models
from django.contrib.auth.models import User


class ActivityLog(models.Model):
    """Track user activities for audit purposes"""
    
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PAYMENT', 'Payment'),
        ('ACCEPT', 'Accept'),
        ('DECLINE', 'Decline'),
        ('CANCEL', 'Cancel'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50, help_text="Name of the model (e.g., Booking, Patient)")
    object_id = models.IntegerField(null=True, blank=True, help_text="ID of the affected object")
    description = models.TextField(help_text="Description of the action")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['model_name', '-timestamp']),
        ]
    
    def __str__(self):
        username = self.user.username if self.user else 'Unknown'
        return f"{username} - {self.get_action_display()} {self.model_name} at {self.timestamp}"
