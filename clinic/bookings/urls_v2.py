"""
URL patterns for Bootstrap/HTMX/Alpine version (v2)
Access via /v2/ prefix to test alongside original version
"""
from django.urls import path
from .views_v2 import (
    # Import all views from the views_v2 package
    # Auth views
    landing_v2, login_v2, staff_login_v2, logout_v2,
    patient_dashboard_v2, admin_dashboard_v2,
    # Public views  
    home_v2, booking_v2, services_v2, about_v2, contact_v2, success_v2,
    htmx_services_preview, htmx_time_slots, htmx_submit_booking, htmx_submit_contact,
    # Dashboard views
    htmx_dashboard_stats, htmx_financial_overview,
    # Billing views
    htmx_unpaid_patients, htmx_all_billings, htmx_mark_paid,
    htmx_paid_billings, htmx_unpaid_billings,
    htmx_payment_create_form, htmx_payment_create,
    # Appointment views
    htmx_appointments_list, htmx_mark_consultation_done,
    htmx_update_consultation_status, htmx_update_appointment_doctor, htmx_delete_appointment,
    htmx_pending_bookings, htmx_accept_booking, htmx_decline_booking,
    htmx_appointment_create_form, htmx_appointment_create,
    htmx_appointment_edit_form, htmx_appointment_update,
    # Patient views
    htmx_patients_list, htmx_patient_records, htmx_patient_detail,
    htmx_delete_patient, htmx_medical_records_list,
    htmx_medical_record_edit_form, htmx_medical_record_update,
    htmx_medical_record_create_form, htmx_medical_record_create,
    htmx_medical_record_detail, htmx_delete_medical_record,
    htmx_medical_images, htmx_prescriptions,
    htmx_prescription_create_form, htmx_prescription_create,
    htmx_prescription_delete,
    htmx_medical_image_upload_form, htmx_medical_image_upload,
    htmx_medical_image_delete,
    htmx_patient_create_form, htmx_patient_create,
    htmx_patient_edit_form, htmx_patient_update,
    upload_profile_picture,
    # Inventory views
    htmx_inventory_list, htmx_inventory_adjust, htmx_inventory_adjust_submit,
    htmx_stock_transactions_list,
    htmx_pos_interface, htmx_pos_product_search,
    htmx_pos_add_to_cart, htmx_pos_remove_from_cart,
    htmx_pos_update_quantity, htmx_pos_update_discount,
    htmx_pos_complete_sale, htmx_pos_cancel_sale,
    htmx_pos_sales_list, htmx_pos_sale_detail,
    htmx_inventory_create_form, htmx_inventory_create,
    htmx_inventory_edit_form, htmx_inventory_update, htmx_inventory_delete,
    # Admin management views
    htmx_users_list, htmx_user_detail, htmx_user_edit,
    htmx_user_create_form, htmx_user_create,
    htmx_user_update, htmx_user_delete,
    htmx_user_password_form, htmx_user_password_reset,
    htmx_services_list, htmx_service_create_form, htmx_service_create,
    htmx_service_edit_form, htmx_service_update, htmx_service_delete, htmx_service_toggle,
    # Doctor management views
    htmx_doctors_list, htmx_doctor_create_form, htmx_doctor_create,
    htmx_doctor_edit_form, htmx_doctor_update, htmx_doctor_delete,
    htmx_doctor_schedule,
    # Calendar management views
    htmx_calendar_view, htmx_toggle_blocked_date,
    htmx_blocked_dates_list, htmx_delete_blocked_date,
    # Clinic settings views
    htmx_clinic_settings_form, htmx_clinic_settings_update,
    # Report views
    download_appointments_pdf, download_patients_csv,
    download_billing_csv, download_services_pdf,
)

app_name = 'bookings_v2'

urlpatterns = [
    # V2 routes - new Bootstrap/HTMX/Alpine implementation
    
    # Landing and authentication
    path('', landing_v2, name='landing'),
    path('login/', login_v2, name='login'),
    path('staff-login/', staff_login_v2, name='staff_login'),
    path('logout/', logout_v2, name='logout'),
    
    # Public pages
    path('home/', home_v2, name='home'),
    path('booking/', booking_v2, name='booking'),
    path('success/', success_v2, name='success'),
    path('services/', services_v2, name='services'),
    path('about/', about_v2, name='about'),
    path('contact/', contact_v2, name='contact'),
    
    # Admin dashboard (staff only)
    path('admin-dashboard/', admin_dashboard_v2, name='admin_dashboard'),
    
    # Patient dashboard (patient only)
    path('patient-dashboard/', patient_dashboard_v2, name='patient_dashboard'),
    
    # HTMX partial endpoints (return HTML fragments)
    # Dashboard stats refresh endpoint
    path('htmx/dashboard-stats/', htmx_dashboard_stats, name='htmx_dashboard_stats'),
    path('htmx/financial-overview/', htmx_financial_overview, name='htmx_financial_overview'),
    
    path('htmx/unpaid-patients/', htmx_unpaid_patients, name='htmx_unpaid_patients'),
    path('htmx/all-billings/', htmx_all_billings, name='htmx_all_billings'),
    path('htmx/all-billings-list/', htmx_all_billings, name='htmx_all_billings_list'),
    path('htmx/paid-billings/', htmx_paid_billings, name='htmx_paid_billings'),
    path('htmx/unpaid-billings/', htmx_unpaid_billings, name='htmx_unpaid_billings'),
    path('htmx/mark-paid/<int:billing_id>/', htmx_mark_paid, name='htmx_mark_paid'),
    path('htmx/services-preview/', htmx_services_preview, name='htmx_services_preview'),
    
    # Booking HTMX endpoints
    path('htmx/time-slots/', htmx_time_slots, name='htmx_time_slots'),
    path('htmx/submit-booking/', htmx_submit_booking, name='htmx_submit_booking'),
    
    # Contact HTMX endpoint
    path('htmx/submit-contact/', htmx_submit_contact, name='htmx_submit_contact'),
    
    # Appointments HTMX endpoints
    path('htmx/appointments/', htmx_appointments_list, name='htmx_appointments_list'),
    path('htmx/mark-consultation-done/<int:booking_id>/', htmx_mark_consultation_done, name='htmx_mark_consultation_done'),
    path('htmx/update-consultation-status/<int:booking_id>/', htmx_update_consultation_status, name='htmx_update_consultation_status'),
    path('htmx/update-appointment-doctor/<int:booking_id>/', htmx_update_appointment_doctor, name='htmx_update_appointment_doctor'),
    path('htmx/delete-appointment/<int:booking_id>/', htmx_delete_appointment, name='htmx_delete_appointment'),
    path('htmx/appointment/create-form/', htmx_appointment_create_form, name='htmx_appointment_create_form'),
    path('htmx/appointment/create/', htmx_appointment_create, name='htmx_appointment_create'),
    path('htmx/appointment/<int:appointment_id>/edit/', htmx_appointment_edit_form, name='htmx_appointment_edit_form'),
    path('htmx/appointment/<int:appointment_id>/update/', htmx_appointment_update, name='htmx_appointment_update'),
    
    # Patients HTMX endpoints
    path('htmx/patients/', htmx_patients_list, name='htmx_patients_list'),
    path('htmx/patient-detail/<int:patient_id>/', htmx_patient_detail, name='htmx_patient_detail'),
    path('htmx/patient-records/<int:patient_id>/', htmx_patient_records, name='htmx_patient_records'),
    path('htmx/delete-patient/<int:patient_id>/', htmx_delete_patient, name='htmx_delete_patient'),
    path('htmx/patient/create-form/', htmx_patient_create_form, name='htmx_patient_create_form'),
    path('htmx/patient/create/', htmx_patient_create, name='htmx_patient_create'),
    path('htmx/patient/<int:patient_id>/edit/', htmx_patient_edit_form, name='htmx_patient_edit_form'),
    path('htmx/patient/<int:patient_id>/update/', htmx_patient_update, name='htmx_patient_update'),
    path('htmx/upload-profile-picture/', upload_profile_picture, name='upload_profile_picture'),
    
    # Medical Records HTMX endpoints
    path('htmx/medical-records/', htmx_medical_records_list, name='htmx_medical_records_list'),
    path('htmx/medical-record/create-form/', htmx_medical_record_create_form, name='htmx_medical_record_create_form'),
    path('htmx/medical-record/create/', htmx_medical_record_create, name='htmx_medical_record_create'),
    path('htmx/medical-record/<int:record_id>/', htmx_medical_record_detail, name='htmx_medical_record_detail'),
    path('htmx/medical-record/<int:record_id>/edit/', htmx_medical_record_edit_form, name='htmx_medical_record_edit_form'),
    path('htmx/medical-record/<int:record_id>/update/', htmx_medical_record_update, name='htmx_medical_record_update'),
    path('htmx/medical-record/<int:record_id>/delete/', htmx_delete_medical_record, name='htmx_delete_medical_record'),
    path('htmx/medical-images/<int:record_id>/', htmx_medical_images, name='htmx_medical_images'),
    path('htmx/medical-image/upload-form/<int:record_id>/', htmx_medical_image_upload_form, name='htmx_medical_image_upload_form'),
    path('htmx/medical-image/upload/<int:record_id>/', htmx_medical_image_upload, name='htmx_medical_image_upload'),
    path('htmx/medical-image/<int:image_id>/delete/', htmx_medical_image_delete, name='htmx_medical_image_delete'),
    path('htmx/prescriptions/<int:record_id>/', htmx_prescriptions, name='htmx_prescriptions'),
    path('htmx/prescription/create-form/<int:record_id>/', htmx_prescription_create_form, name='htmx_prescription_create_form'),
    path('htmx/prescription/create/<int:record_id>/', htmx_prescription_create, name='htmx_prescription_create'),
    path('htmx/prescription/<int:prescription_id>/delete/', htmx_prescription_delete, name='htmx_prescription_delete'),
    
    # Billing & Payment HTMX endpoints
    path('htmx/payment/create-form/', htmx_payment_create_form, name='htmx_payment_create_form'),
    path('htmx/payment/create/', htmx_payment_create, name='htmx_payment_create'),
    
    # Inventory HTMX endpoints
    path('htmx/inventory/', htmx_inventory_list, name='htmx_inventory_list'),
    path('htmx/inventory-adjust/<int:item_id>/', htmx_inventory_adjust, name='htmx_inventory_adjust'),
    path('htmx/inventory-adjust-submit/<int:item_id>/', htmx_inventory_adjust_submit, name='htmx_inventory_adjust_submit'),
    path('htmx/inventory/create-form/', htmx_inventory_create_form, name='htmx_inventory_create_form'),
    path('htmx/inventory/create/', htmx_inventory_create, name='htmx_inventory_create'),
    path('htmx/inventory/<int:item_id>/edit/', htmx_inventory_edit_form, name='htmx_inventory_edit_form'),
    path('htmx/inventory/<int:item_id>/update/', htmx_inventory_update, name='htmx_inventory_update'),
    path('htmx/inventory/<int:item_id>/delete/', htmx_inventory_delete, name='htmx_inventory_delete'),
    
    # Stock Transactions HTMX endpoints
    path('htmx/stock-transactions/', htmx_stock_transactions_list, name='htmx_stock_transactions_list'),
    
    # POS System HTMX endpoints
    path('htmx/pos/', htmx_pos_interface, name='htmx_pos_interface'),
    path('htmx/pos/products/', htmx_pos_product_search, name='htmx_pos_product_search'),
    path('htmx/pos/add/<int:item_id>/', htmx_pos_add_to_cart, name='htmx_pos_add_to_cart'),
    path('htmx/pos/remove/<int:item_id>/', htmx_pos_remove_from_cart, name='htmx_pos_remove_from_cart'),
    path('htmx/pos/quantity/<int:item_id>/', htmx_pos_update_quantity, name='htmx_pos_update_quantity'),
    path('htmx/pos/discount/<int:sale_id>/', htmx_pos_update_discount, name='htmx_pos_update_discount'),
    path('htmx/pos/complete/<int:sale_id>/', htmx_pos_complete_sale, name='htmx_pos_complete_sale'),
    path('htmx/pos/cancel/<int:sale_id>/', htmx_pos_cancel_sale, name='htmx_pos_cancel_sale'),
    path('htmx/pos-sales/', htmx_pos_sales_list, name='htmx_pos_sales_list'),
    path('htmx/pos-sale/<int:sale_id>/', htmx_pos_sale_detail, name='htmx_pos_sale_detail'),
    
    # Services HTMX endpoints
    path('htmx/services/', htmx_services_list, name='htmx_services_list'),
    path('htmx/service/create-form/', htmx_service_create_form, name='htmx_service_create_form'),
    path('htmx/service/create/', htmx_service_create, name='htmx_service_create'),
    path('htmx/service/<int:service_id>/edit/', htmx_service_edit_form, name='htmx_service_edit_form'),
    path('htmx/service/<int:service_id>/update/', htmx_service_update, name='htmx_service_update'),
    path('htmx/service/<int:service_id>/delete/', htmx_service_delete, name='htmx_service_delete'),
    path('htmx/service/<int:service_id>/toggle/', htmx_service_toggle, name='htmx_service_toggle'),
    
    # Pending Bookings HTMX endpoints
    path('htmx/pending-bookings/', htmx_pending_bookings, name='htmx_pending_bookings'),
    path('htmx/accept-booking/<int:booking_id>/', htmx_accept_booking, name='htmx_accept_booking'),
    path('htmx/decline-booking/<int:booking_id>/', htmx_decline_booking, name='htmx_decline_booking'),
    
    # User Management HTMX endpoints
    path('htmx/users/', htmx_users_list, name='htmx_users_list'),
    path('htmx/user/<int:user_id>/', htmx_user_detail, name='htmx_user_detail'),
    path('htmx/user/<int:user_id>/edit/', htmx_user_edit, name='htmx_user_edit'),
    path('htmx/user/create-form/', htmx_user_create_form, name='htmx_user_create_form'),
    path('htmx/user/create/', htmx_user_create, name='htmx_user_create'),
    path('htmx/user/<int:user_id>/update/', htmx_user_update, name='htmx_user_update'),
    path('htmx/user/<int:user_id>/delete/', htmx_user_delete, name='htmx_user_delete'),
    path('htmx/user/<int:user_id>/password-form/', htmx_user_password_form, name='htmx_user_password_form'),
    path('htmx/user/<int:user_id>/password-reset/', htmx_user_password_reset, name='htmx_user_password_reset'),
    
    # Doctor Management HTMX endpoints
    path('htmx/doctors/', htmx_doctors_list, name='htmx_doctors_list'),
    path('htmx/doctor/create-form/', htmx_doctor_create_form, name='htmx_doctor_create_form'),
    path('htmx/doctor/create/', htmx_doctor_create, name='htmx_doctor_create'),
    path('htmx/doctor/<int:doctor_id>/edit/', htmx_doctor_edit_form, name='htmx_doctor_edit_form'),
    path('htmx/doctor/<int:doctor_id>/update/', htmx_doctor_update, name='htmx_doctor_update'),
    path('htmx/doctor/<int:doctor_id>/delete/', htmx_doctor_delete, name='htmx_doctor_delete'),
    path('htmx/doctor/<int:doctor_id>/schedule/', htmx_doctor_schedule, name='htmx_doctor_schedule'),
    
    # Calendar Management HTMX endpoints
    path('htmx/calendar/', htmx_calendar_view, name='htmx_calendar_view'),
    path('htmx/calendar/toggle-date/', htmx_toggle_blocked_date, name='htmx_toggle_blocked_date'),
    path('htmx/calendar/blocked-dates/', htmx_blocked_dates_list, name='htmx_blocked_dates_list'),
    path('htmx/calendar/blocked-date/<int:blocked_date_id>/delete/', htmx_delete_blocked_date, name='htmx_delete_blocked_date'),
    
    # Clinic Settings HTMX endpoints
    path('htmx/clinic-settings/', htmx_clinic_settings_form, name='htmx_clinic_settings_form'),
    path('htmx/clinic-settings/update/', htmx_clinic_settings_update, name='htmx_clinic_settings_update'),
    
    # Reports - Download endpoints
    path('reports/appointments-pdf/', download_appointments_pdf, name='download_appointments_pdf'),
    path('reports/patients-csv/', download_patients_csv, name='download_patients_csv'),
    path('reports/billing-csv/', download_billing_csv, name='download_billing_csv'),
    path('reports/services-pdf/', download_services_pdf, name='download_services_pdf'),
]