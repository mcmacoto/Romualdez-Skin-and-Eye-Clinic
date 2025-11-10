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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from bookings import views_v2

urlpatterns = [
    # === Root redirect to landing page ===
    path('', RedirectView.as_view(url='/admin/', permanent=False), name='root'),
    
    # === V2 Routes (PRIMARY ADMIN INTERFACE) ===
    path('admin/', include('bookings.urls_v2')),  # V2 HTMX-based admin interface
    
    # === Public Routes ===
    path('login/', views_v2.login_v2, name='login'),
    path('logout/', views_v2.logout_v2, name='logout'),
    path('landing/', views_v2.landing_v2, name='landing'),
    path('home/', views_v2.home_v2, name='home_page'),  # Moved from root to /home/
    path('booking/', views_v2.booking_v2, name='booking'),
    path('about/', views_v2.about_v2, name='about'),
    path('services/', views_v2.services_v2, name='services'),
    path('contact/', views_v2.contact_v2, name='contact'),
    
    # === Password Reset Routes ===
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)