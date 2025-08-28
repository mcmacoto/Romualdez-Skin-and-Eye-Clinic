from django.contrib import admin
from .models import Appointment, Service

# Register your models here.
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'date', 'time', 'status', 'created_at')
    list_filter = ('status', 'date')
    search_fields = ('name', 'email', 'phone')
    ordering = ('-created_at',)
    date_hierarchy = 'date'

admin.site.register(Service)

