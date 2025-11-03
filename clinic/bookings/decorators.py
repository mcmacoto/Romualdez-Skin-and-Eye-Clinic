"""
Custom decorators for view permissions and common patterns
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)


def staff_required(view_func):
    """
    Decorator for staff-only views with HTMX-friendly error responses
    
    Usage:
        @login_required
        @staff_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('HX-Request'):
                return HttpResponse(
                    '<div class="alert alert-danger">Please log in to continue.</div>',
                    status=401
                )
            return redirect('bookings_v2:staff_login')
        
        if not request.user.is_staff:
            logger.warning(f"Non-staff user {request.user.username} attempted to access staff-only view: {view_func.__name__}")
            if request.headers.get('HX-Request'):
                return HttpResponse(
                    '<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> Permission denied. Staff access required.</div>',
                    status=403
                )
            return redirect('bookings_v2:landing')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def superuser_required(view_func):
    """
    Decorator for superuser-only views
    
    Usage:
        @login_required
        @superuser_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('bookings_v2:staff_login')
        
        if not request.user.is_superuser:
            logger.warning(f"Non-superuser {request.user.username} attempted to access superuser-only view: {view_func.__name__}")
            if request.headers.get('HX-Request'):
                return HttpResponse(
                    '<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> Superuser access required.</div>',
                    status=403
                )
            return redirect('bookings_v2:admin_dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def patient_required(view_func):
    """
    Decorator for patient-only views (non-staff users)
    
    Usage:
        @login_required
        @patient_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('bookings_v2:login')
        
        if request.user.is_staff:
            logger.info(f"Staff user {request.user.username} redirected from patient view to admin dashboard")
            return redirect('bookings_v2:admin_dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
