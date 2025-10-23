"""
URL patterns for Bootstrap/HTMX/Alpine version (v2)
Access via /v2/ prefix to test alongside original version
"""
from django.urls import path
from . import views_v2

app_name = 'bookings_v2'

urlpatterns = [
    # V2 routes - new Bootstrap/HTMX/Alpine implementation
    
    # Landing and authentication
    path('', views_v2.landing_v2, name='landing'),
    path('login/', views_v2.login_v2, name='login'),
    path('staff-login/', views_v2.staff_login_v2, name='staff_login'),
    path('logout/', views_v2.logout_v2, name='logout'),
    
    # Public pages
    path('home/', views_v2.home_v2, name='home'),
    path('booking/', views_v2.booking_v2, name='booking'),
    path('success/', views_v2.success_v2, name='success'),
    path('services/', views_v2.services_v2, name='services'),
    path('about/', views_v2.about_v2, name='about'),
    path('contact/', views_v2.contact_v2, name='contact'),
    
    # Admin dashboard (staff only)
    path('admin-dashboard/', views_v2.admin_dashboard_v2, name='admin_dashboard'),
    
    # Patient dashboard (patient only)
    path('patient-dashboard/', views_v2.patient_dashboard_v2, name='patient_dashboard'),
    
    # HTMX partial endpoints (return HTML fragments)
    path('htmx/unpaid-patients/', views_v2.htmx_unpaid_patients, name='htmx_unpaid_patients'),
    path('htmx/all-billings/', views_v2.htmx_all_billings, name='htmx_all_billings'),
    path('htmx/all-billings-list/', views_v2.htmx_all_billings, name='htmx_all_billings_list'),
    path('htmx/paid-billings/', views_v2.htmx_paid_billings, name='htmx_paid_billings'),
    path('htmx/unpaid-billings/', views_v2.htmx_unpaid_billings, name='htmx_unpaid_billings'),
    path('htmx/mark-paid/<int:billing_id>/', views_v2.htmx_mark_paid, name='htmx_mark_paid'),
    path('htmx/services-preview/', views_v2.htmx_services_preview, name='htmx_services_preview'),
    
    # Booking HTMX endpoints
    path('htmx/time-slots/', views_v2.htmx_time_slots, name='htmx_time_slots'),
    path('htmx/submit-booking/', views_v2.htmx_submit_booking, name='htmx_submit_booking'),
    
    # Contact HTMX endpoint
    path('htmx/submit-contact/', views_v2.htmx_submit_contact, name='htmx_submit_contact'),
    
    # Appointments HTMX endpoints
    path('htmx/appointments/', views_v2.htmx_appointments_list, name='htmx_appointments_list'),
    path('htmx/mark-consultation-done/<int:booking_id>/', views_v2.htmx_mark_consultation_done, name='htmx_mark_consultation_done'),
    path('htmx/update-consultation-status/<int:booking_id>/', views_v2.htmx_update_consultation_status, name='htmx_update_consultation_status'),
    path('htmx/delete-appointment/<int:booking_id>/', views_v2.htmx_delete_appointment, name='htmx_delete_appointment'),
    path('htmx/appointment/create-form/', views_v2.htmx_appointment_create_form, name='htmx_appointment_create_form'),
    path('htmx/appointment/create/', views_v2.htmx_appointment_create, name='htmx_appointment_create'),
    path('htmx/appointment/<int:appointment_id>/edit/', views_v2.htmx_appointment_edit_form, name='htmx_appointment_edit_form'),
    path('htmx/appointment/<int:appointment_id>/update/', views_v2.htmx_appointment_update, name='htmx_appointment_update'),
    
    # Patients HTMX endpoints
    path('htmx/patients/', views_v2.htmx_patients_list, name='htmx_patients_list'),
    path('htmx/patient-records/<int:patient_id>/', views_v2.htmx_patient_records, name='htmx_patient_records'),
    path('htmx/delete-patient/<int:patient_id>/', views_v2.htmx_delete_patient, name='htmx_delete_patient'),
    path('htmx/patient/create-form/', views_v2.htmx_patient_create_form, name='htmx_patient_create_form'),
    path('htmx/patient/create/', views_v2.htmx_patient_create, name='htmx_patient_create'),
    path('htmx/patient/<int:patient_id>/edit/', views_v2.htmx_patient_edit_form, name='htmx_patient_edit_form'),
    path('htmx/patient/<int:patient_id>/update/', views_v2.htmx_patient_update, name='htmx_patient_update'),
    
    # Medical Records HTMX endpoints
    path('htmx/medical-records/', views_v2.htmx_medical_records_list, name='htmx_medical_records_list'),
    path('htmx/medical-images/<int:record_id>/', views_v2.htmx_medical_images, name='htmx_medical_images'),
    
    # Billing & Payment HTMX endpoints
    path('htmx/payment/create-form/', views_v2.htmx_payment_create_form, name='htmx_payment_create_form'),
    path('htmx/payment/create/', views_v2.htmx_payment_create, name='htmx_payment_create'),
    
    # Inventory HTMX endpoints
    path('htmx/inventory/', views_v2.htmx_inventory_list, name='htmx_inventory_list'),
    path('htmx/inventory-adjust/<int:item_id>/', views_v2.htmx_inventory_adjust, name='htmx_inventory_adjust'),
    path('htmx/inventory-adjust-submit/<int:item_id>/', views_v2.htmx_inventory_adjust_submit, name='htmx_inventory_adjust_submit'),
    path('htmx/inventory/create-form/', views_v2.htmx_inventory_create_form, name='htmx_inventory_create_form'),
    path('htmx/inventory/create/', views_v2.htmx_inventory_create, name='htmx_inventory_create'),
    path('htmx/inventory/<int:item_id>/edit/', views_v2.htmx_inventory_edit_form, name='htmx_inventory_edit_form'),
    path('htmx/inventory/<int:item_id>/update/', views_v2.htmx_inventory_update, name='htmx_inventory_update'),
    
    # Services HTMX endpoints
    path('htmx/services/', views_v2.htmx_services_list, name='htmx_services_list'),
    path('htmx/service/create-form/', views_v2.htmx_service_create_form, name='htmx_service_create_form'),
    path('htmx/service/create/', views_v2.htmx_service_create, name='htmx_service_create'),
    path('htmx/service/<int:service_id>/edit/', views_v2.htmx_service_edit_form, name='htmx_service_edit_form'),
    path('htmx/service/<int:service_id>/update/', views_v2.htmx_service_update, name='htmx_service_update'),
    path('htmx/service/<int:service_id>/delete/', views_v2.htmx_service_delete, name='htmx_service_delete'),
    
    # Pending Bookings HTMX endpoints
    path('htmx/pending-bookings/', views_v2.htmx_pending_bookings, name='htmx_pending_bookings'),
    path('htmx/accept-booking/<int:booking_id>/', views_v2.htmx_accept_booking, name='htmx_accept_booking'),
    path('htmx/decline-booking/<int:booking_id>/', views_v2.htmx_decline_booking, name='htmx_decline_booking'),
    
    # User Management HTMX endpoints
    path('htmx/users/', views_v2.htmx_users_list, name='htmx_users_list'),
    path('htmx/user/<int:user_id>/', views_v2.htmx_user_detail, name='htmx_user_detail'),
    path('htmx/user/<int:user_id>/edit/', views_v2.htmx_user_edit, name='htmx_user_edit'),
    path('htmx/user/create-form/', views_v2.htmx_user_create_form, name='htmx_user_create_form'),
    path('htmx/user/create/', views_v2.htmx_user_create, name='htmx_user_create'),
    path('htmx/user/<int:user_id>/update/', views_v2.htmx_user_update, name='htmx_user_update'),
    path('htmx/user/<int:user_id>/delete/', views_v2.htmx_user_delete, name='htmx_user_delete'),
]

