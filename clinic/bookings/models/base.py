"""
Base models for the clinic system
Contains shared/foundational models used across the application
"""
from django.db import models


class Service(models.Model):
    """Services offered by the clinic"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='services/')
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        help_text="Service price in Philippine Pesos (₱)"
    )
    
    def __str__(self):
        return self.name
