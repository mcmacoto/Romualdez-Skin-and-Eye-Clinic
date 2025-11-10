"""
Admin interface for Calendar model
Manages blocked dates, holidays, and special operating hours
"""
from django.contrib import admin
from ..models import Calendar


@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    """Admin interface for Calendar events"""
    
    list_display = [
        'date',
        'event_type',
        'reason',
        'start_time',
        'end_time',
        'created_by',
        'created_at'
    ]
    
    list_filter = [
        'event_type',
        'date',
        'created_at'
    ]
    
    search_fields = [
        'reason',
        'date'
    ]
    
    date_hierarchy = 'date'
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'date', 'reason')
        }),
        ('Time Information (Optional)', {
            'fields': ('start_time', 'end_time'),
            'classes': ('collapse',),
            'description': 'Used for special operating hours'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-set created_by on save"""
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    class Meta:
        verbose_name = 'Calendar Event'
        verbose_name_plural = 'Calendar Events'
