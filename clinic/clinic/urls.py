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
from django.urls import path
from django.contrib.auth.views import LoginView
from bookings import views

# Admin site customization
admin.site.site_header = "Romualdez Skin and Eye Clinic Staff Portal"
admin.site.site_title = "Clinic Portal"
admin.site.index_title = "Dashboard"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', LoginView.as_view(template_name='bookings/login.html'), name='login'),
    path('', views.home, name='home'),
    path('booking/', views.booking, name='booking'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
]