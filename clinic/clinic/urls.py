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
from bookings import views_v2
from bookings.admin import clinic_admin_site

# Admin site customization
admin.site.site_header = "Romualdez Skin Clinic Staff Portal"
admin.site.site_title = "Clinic Portal"
admin.site.index_title = "Dashboard"

urlpatterns = [
    # === V2 Routes (PRIMARY ADMIN INTERFACE) ===
    path('admin/', include('bookings.urls_v2')),  # V2 is now the primary admin interface
    
    # === Legacy Django Admin (DEPRECATED) ===
    path('old-admin/', clinic_admin_site.urls),  # Old Django admin - Use new V2 interface instead
    
    # === Public Routes ===
    path('login/', LoginView.as_view(template_name='bookings/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='landing'), name='logout'),
    path('landing/', views_v2.landing_v2, name='landing'),
    path('', views_v2.home_v2, name='home'),
    path('booking/', views_v2.booking_v2, name='booking'),
    path('about/', views_v2.about_v2, name='about'),
    path('services/', views_v2.services_v2, name='services'),
    path('contact/', views_v2.contact_v2, name='contact'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)