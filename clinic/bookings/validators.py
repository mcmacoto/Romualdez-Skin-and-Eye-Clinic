"""
Custom validators for forms and models.
"""
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time
import re


def validate_future_date(value):
    """Ensure date is not in the past"""
    if value < timezone.now().date():
        raise ValidationError('Date cannot be in the past.')


def validate_clinic_hours(value):
    """Ensure time is within clinic operating hours (8 AM - 5 PM)"""
    clinic_open = time(8, 0)  # 8:00 AM
    clinic_close = time(17, 0)  # 5:00 PM
    
    if not (clinic_open <= value <= clinic_close):
        raise ValidationError('Time must be between 8:00 AM and 5:00 PM (clinic hours).')


def validate_phone_format(value):
    """Validate Philippine phone number format"""
    # Accepts formats: 09171234567, +639171234567, (02) 1234-5678, 02-1234-5678
    patterns = [
        r'^09\d{9}$',  # Mobile: 09171234567
        r'^\+639\d{9}$',  # Mobile with country code: +639171234567
        r'^\(0\d{1,2}\)\s?\d{3,4}-\d{4}$',  # Landline: (02) 1234-5678
        r'^0\d{1,2}-\d{3,4}-\d{4}$',  # Landline: 02-1234-5678
    ]
    
    if not any(re.match(pattern, value) for pattern in patterns):
        raise ValidationError(
            'Invalid phone format. Use: 09171234567, +639171234567, (02) 1234-5678, or 02-1234-5678'
        )


def validate_email_domain(value):
    """Ensure email has valid domain format"""
    if '@' not in value:
        raise ValidationError('Invalid email address.')
    
    domain = value.split('@')[1]
    if '.' not in domain:
        raise ValidationError('Email domain must contain a dot (e.g., gmail.com).')


def validate_positive_decimal(value):
    """Ensure decimal value is positive"""
    if value < 0:
        raise ValidationError('Value must be positive.')


def validate_age_range(value):
    """Ensure age is within reasonable range (0-150)"""
    today = timezone.now().date()
    age = (today - value).days // 365
    
    if age < 0:
        raise ValidationError('Date of birth cannot be in the future.')
    if age > 150:
        raise ValidationError('Age cannot exceed 150 years.')


def validate_stock_quantity(value):
    """Ensure stock quantity is non-negative"""
    if value < 0:
        raise ValidationError('Stock quantity cannot be negative.')


def validate_discount_percentage(value):
    """Ensure discount is between 0% and 100%"""
    if not (0 <= value <= 100):
        raise ValidationError('Discount must be between 0% and 100%.')


def validate_time_slot_interval(value):
    """Ensure time is on 30-minute intervals"""
    if value.minute not in [0, 30]:
        raise ValidationError('Time must be on 30-minute intervals (e.g., 9:00, 9:30).')
