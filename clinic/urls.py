from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from bookings import views

urlpatterns = [
    path('', views.landing, name='landing'), 
    path('home/', views.home, name='home'),
    path('booking/', views.booking, name='booking'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)