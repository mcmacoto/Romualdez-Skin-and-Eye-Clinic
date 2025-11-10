"""
Models package for bookings app
Organized by domain for better maintainability
"""
# Base models
from .base import Service

# Clinic Settings
from .settings import ClinicSettings

# Doctor models
from .doctors import Doctor

# Blocked dates for calendar control (deprecated - use Calendar)
from .blocked_dates import BlockedDate

# Calendar model for date management
from .calendar import Calendar

# Appointment and booking models
from .appointments import Appointment, Booking

# Patient and medical record models
from .patients import Patient, MedicalRecord, MedicalImage, medical_image_upload_path

# Billing and payment models
from .billing import Billing, Payment

# Inventory models
from .inventory import Inventory, StockTransaction

# Activity logging
from .activity_log import ActivityLog

# Prescription models
from .prescriptions import Prescription

# Point of Sale models
from .pos import POSSale, POSSaleItem

__all__ = [
    # Base
    'Service',
    
    # Settings
    'ClinicSettings',
    
    # Doctors
    'Doctor',
    
    # Blocked Dates (deprecated)
    'BlockedDate',
    
    # Calendar
    'Calendar',
    
    # Appointments
    'Appointment',
    'Booking',
    
    # Patients
    'Patient',
    'MedicalRecord',
    'MedicalImage',
    'medical_image_upload_path',
    
    # Billing
    'Billing',
    'Payment',
    
    # Inventory
    'Inventory',
    'StockTransaction',
    
    # Prescriptions
    'Prescription',
    
    # POS
    'POSSale',
    'POSSaleItem',
]
