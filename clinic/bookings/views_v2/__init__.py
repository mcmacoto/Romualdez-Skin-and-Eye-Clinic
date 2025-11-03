"""
Views V2 Package
This package modularizes the V2 views into logical components.

Modules:
- auth_views: Authentication and dashboard views  
- public_views: Public-facing pages and HTMX endpoints

For remaining views, we import from views_v2_legacy.py (the renamed monolithic file).
"""

# Import from modularized views
from .auth_views import (
    landing_v2,
    login_v2,
    staff_login_v2,
    logout_v2,
    patient_dashboard_v2,
    admin_dashboard_v2,
)

from .dashboard_views import (
    htmx_dashboard_stats,
)

from .public_views import (
    home_v2,
    booking_v2,
    services_v2,
    about_v2,
    contact_v2,
    success_v2,
    htmx_services_preview,
    htmx_time_slots,
    htmx_submit_booking,
    htmx_submit_contact,
)

# Import from billing_views
from .billing_views import (
    htmx_unpaid_patients,
    htmx_all_billings,
    htmx_mark_paid,
    htmx_paid_billings,
    htmx_unpaid_billings,
    htmx_payment_create_form,
    htmx_payment_create,
)

# Import from appointment_views
from .appointment_views import (
    htmx_appointments_list,
    htmx_mark_consultation_done,
    htmx_update_consultation_status,
    htmx_delete_appointment,
    htmx_pending_bookings,
    htmx_accept_booking,
    htmx_decline_booking,
    htmx_appointment_create_form,
    htmx_appointment_create,
    htmx_appointment_edit_form,
    htmx_appointment_update,
)

# Import from patient_views
from .patient_views import (
    htmx_patients_list,
    htmx_patient_records,
    htmx_patient_detail,
    htmx_delete_patient,
    htmx_medical_records_list,
    htmx_medical_record_edit_form,
    htmx_medical_record_update,
    htmx_medical_record_create_form,
    htmx_medical_record_create,
    htmx_medical_record_detail,
    htmx_delete_medical_record,
    htmx_medical_images,
    htmx_prescriptions,
    htmx_prescription_create_form,
    htmx_prescription_create,
    htmx_prescription_delete,
    htmx_medical_image_upload_form,
    htmx_medical_image_upload,
    htmx_medical_image_delete,
    htmx_patient_create_form,
    htmx_patient_create,
    htmx_patient_edit_form,
    htmx_patient_update,
)

# Import from inventory_views
from .inventory_views import (
    htmx_inventory_list,
    htmx_inventory_adjust,
    htmx_inventory_adjust_submit,
    htmx_stock_transactions_list,
    htmx_pos_interface,
    htmx_pos_product_search,
    htmx_pos_add_to_cart,
    htmx_pos_remove_from_cart,
    htmx_pos_update_quantity,
    htmx_pos_update_discount,
    htmx_pos_complete_sale,
    htmx_pos_cancel_sale,
    htmx_pos_sales_list,
    htmx_pos_sale_detail,
    htmx_inventory_create_form,
    htmx_inventory_create,
    htmx_inventory_edit_form,
    htmx_inventory_update,
    htmx_inventory_delete,
)

# Import from admin_management_views
from .admin_management_views import (
    htmx_users_list,
    htmx_user_detail,
    htmx_user_edit,
    htmx_user_create_form,
    htmx_user_create,
    htmx_user_update,
    htmx_user_delete,
    htmx_services_list,
    htmx_service_create_form,
    htmx_service_create,
    htmx_service_edit_form,
    htmx_service_update,
    htmx_service_delete,
    # Report views
    download_appointments_pdf,
    download_patients_csv,
    download_billing_csv,
    download_services_pdf,
)

# All views have been modularized! No more legacy imports needed.

# Export all views
__all__ = [
    # Auth views (modularized)
    'landing_v2',
    'login_v2',
    'staff_login_v2',
    'logout_v2',
    'patient_dashboard_v2',
    'admin_dashboard_v2',
    
    # Public views (modularized)
    'home_v2',
    'booking_v2',
    'services_v2',
    'about_v2',
    'contact_v2',
    'success_v2',
    'htmx_services_preview',
    'htmx_time_slots',
    'htmx_submit_booking',
    'htmx_submit_contact',
    
    # Billing views (from legacy)
    'htmx_unpaid_patients',
    'htmx_all_billings',
    'htmx_mark_paid',
    'htmx_paid_billings',
    'htmx_unpaid_billings',
    'htmx_payment_create_form',
    'htmx_payment_create',
    
    # Appointment views (from legacy)
    'htmx_appointments_list',
    'htmx_mark_consultation_done',
    'htmx_update_consultation_status',
    'htmx_delete_appointment',
    'htmx_pending_bookings',
    'htmx_accept_booking',
    'htmx_decline_booking',
    'htmx_appointment_create_form',
    'htmx_appointment_create',
    'htmx_appointment_edit_form',
    'htmx_appointment_update',
    
    # Patient views (from legacy)
    'htmx_patients_list',
    'htmx_patient_records',
    'htmx_patient_detail',
    'htmx_delete_patient',
    'htmx_medical_records_list',
    'htmx_medical_record_edit_form',
    'htmx_medical_record_update',
    'htmx_medical_record_create_form',
    'htmx_medical_record_create',
    'htmx_medical_record_detail',
    'htmx_delete_medical_record',
    'htmx_medical_images',
    'htmx_prescriptions',
    'htmx_prescription_create_form',
    'htmx_prescription_create',
    'htmx_prescription_delete',
    'htmx_medical_image_upload_form',
    'htmx_medical_image_upload',
    'htmx_medical_image_delete',
    'htmx_patient_create_form',
    'htmx_patient_create',
    'htmx_patient_edit_form',
    'htmx_patient_update',
    
    # Inventory views (from legacy)
    'htmx_inventory_list',
    'htmx_inventory_adjust',
    'htmx_inventory_adjust_submit',
    'htmx_stock_transactions_list',
    'htmx_pos_interface',
    'htmx_pos_product_search',
    'htmx_pos_add_to_cart',
    'htmx_pos_remove_from_cart',
    'htmx_pos_update_quantity',
    'htmx_pos_update_discount',
    'htmx_pos_complete_sale',
    'htmx_pos_cancel_sale',
    'htmx_pos_sales_list',
    'htmx_pos_sale_detail',
    'htmx_inventory_create_form',
    'htmx_inventory_create',
    'htmx_inventory_edit_form',
    'htmx_inventory_update',
    'htmx_inventory_delete',
    
    # Admin management views (from legacy)
    'htmx_users_list',
    'htmx_user_detail',
    'htmx_user_edit',
    'htmx_user_create_form',
    'htmx_user_create',
    'htmx_user_update',
    'htmx_user_delete',
    'htmx_services_list',
    'htmx_service_create_form',
    'htmx_service_create',
    'htmx_service_edit_form',
    'htmx_service_update',
    'htmx_service_delete',
    
    # Report views
    'download_appointments_pdf',
    'download_patients_csv',
    'download_billing_csv',
    'download_services_pdf',
]
