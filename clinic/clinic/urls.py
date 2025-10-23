"""
URL configuration for clinic project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from django.conf import settings
from django.conf.urls.static import static
from bookings import views
from bookings.admin import clinic_admin_site

# Admin site customization
admin.site.site_header = "Romualdez Skin Clinic Staff Portal"
admin.site.site_title = "Clinic Portal"
admin.site.index_title = "Dashboard"

urlpatterns = [
    path('admin/', clinic_admin_site.urls),
    
    # === V2 Routes (Bootstrap/HTMX/Alpine) - TEST VERSION ===
    path('v2/', include('bookings.urls_v2')),  # Access via http://localhost:8000/v2/
    
    # === Original Routes (Current Production) ===
    path('login/', LoginView.as_view(template_name='bookings/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='landing'), name='logout'),
    path('landing/', views.landing, name='landing'),
    path('', views.home, name='home'),
    path('booking/', views.booking, name='booking'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('contact/', views.contact, name='contact'),
    
    # API endpoints for pending bookings management
    path('api/pending-bookings/', views.api_get_pending_bookings, name='api_pending_bookings'),
    path('api/bookings/<int:booking_id>/accept/', views.api_accept_booking, name='api_accept_booking'),
    path('api/bookings/<int:booking_id>/decline/', views.api_decline_booking, name='api_decline_booking'),
    
    # API endpoints for patients, medical records, inventory, and POS sales
    path('api/patients/', views.api_get_patients, name='api_patients'),
    path('api/medical-records/', views.api_get_medical_records, name='api_medical_records'),
    path('api/inventory/', views.api_get_inventory, name='api_inventory'),
    path('api/pos-sales/', views.api_pos_sales, name='api_pos_sales'),
    path('api/patient-profile/', views.api_get_patient_profile, name='api_patient_profile'),
    
    # API endpoints for billing management
    path('api/unpaid-patients/', views.api_get_unpaid_patients, name='api_unpaid_patients'),
    path('api/all-billings/', views.api_get_all_billings, name='api_all_billings'),
    path('api/billing/<int:billing_id>/mark-paid/', views.api_mark_billing_paid, name='api_mark_billing_paid'),
    path('api/billing/<int:billing_id>/update-fees/', views.api_update_billing_fees, name='api_update_billing_fees'),
    
    # API endpoints for appointments modal
    path('api/all-appointments/', views.api_get_all_appointments, name='api_all_appointments'),
    path('api/booking/<int:booking_id>/mark-done/', views.api_mark_consultation_done, name='api_mark_consultation_done'),
    path('api/booking/<int:booking_id>/update-status/', views.api_update_consultation_status, name='api_update_consultation_status'),
    path('api/booking/<int:booking_id>/delete/', views.api_delete_appointment, name='api_delete_appointment'),
    
    # API endpoints for patient management
    path('api/patient/<int:patient_id>/medical-records/', views.api_get_patient_medical_records, name='api_patient_medical_records'),
    path('api/patient/<int:patient_id>/delete/', views.api_delete_patient, name='api_delete_patient'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)