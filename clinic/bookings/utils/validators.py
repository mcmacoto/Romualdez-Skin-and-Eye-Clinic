"""
Validators for common field patterns
Provides reusable validators for phone numbers, emails, etc.
"""
from django.core.validators import RegexValidator


# Phone number validator
phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)
