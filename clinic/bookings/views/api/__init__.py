"""
API views package
Contains all API endpoints organized by domain
"""
from .bookings import (
    api_get_pending_bookings,
    api_accept_booking,
    api_decline_booking,
)
from .patients import (
    api_get_patients,
    api_get_patient_profile,
    api_get_patient_medical_records,
    api_delete_patient,
)
from .medical import (
    api_get_medical_records,
)
from .billing import (
    api_get_unpaid_patients,
    api_get_all_billings,
    api_mark_billing_paid,
    api_update_billing_fees,
)
from .inventory import (
    api_get_inventory,
    api_pos_sales,
)
from .appointments import (
    api_get_all_appointments,
    api_mark_consultation_done,
    api_update_consultation_status,
    api_delete_appointment,
)

__all__ = [
    # Booking APIs
    'api_get_pending_bookings',
    'api_accept_booking',
    'api_decline_booking',
    
    # Patient APIs
    'api_get_patients',
    'api_get_patient_profile',
    'api_get_patient_medical_records',
    'api_delete_patient',
    
    # Medical APIs
    'api_get_medical_records',
    
    # Billing APIs
    'api_get_unpaid_patients',
    'api_get_all_billings',
    'api_mark_billing_paid',
    'api_update_billing_fees',
    
    # Inventory APIs
    'api_get_inventory',
    'api_pos_sales',
    
    # Appointment APIs
    'api_get_all_appointments',
    'api_mark_consultation_done',
    'api_update_consultation_status',
    'api_delete_appointment',
]
