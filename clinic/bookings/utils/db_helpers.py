"""
Database helper utilities
Provides safe database operation wrappers
"""
from django.db import transaction


def atomic_save(instance):
    """
    Safely save a model instance within a database transaction
    
    Args:
        instance: Django model instance to save
        
    Returns:
        The saved instance
    """
    with transaction.atomic():
        instance.save()
    return instance
