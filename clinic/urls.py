from django.contrib import admin
from django.urls import path
from bookings import views

urlpatterns = [
    path('', views.landing, name='root'),  # Root URL goes to landing
    path('landing/', views.landing, name='landing'),
    path('home/', views.home, name='home'),
    path('booking/', views.booking, name='booking'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    
    # API endpoints for pending bookings management
    path('api/pending-bookings/', views.api_get_pending_bookings, name='api_pending_bookings'),
    path('api/bookings/<int:booking_id>/accept/', views.api_accept_booking, name='api_accept_booking'),
    path('api/bookings/<int:booking_id>/decline/', views.api_decline_booking, name='api_decline_booking'),
    
    # API endpoints for patients, medical records, and inventory
    path('api/patients/', views.api_get_patients, name='api_patients'),
    path('api/medical-records/', views.api_get_medical_records, name='api_medical_records'),
    path('api/inventory/', views.api_get_inventory, name='api_inventory'),
    
    path('admin/', admin.site.urls),  # Move admin to end
]