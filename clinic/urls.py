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
    path('admin/', admin.site.urls),  # Move admin to end
]