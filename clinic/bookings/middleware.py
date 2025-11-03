from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.conf import settings

class StaffPermissionMiddleware:
    """
    Middleware to enforce staff permission restrictions using configurable paths
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Load restricted paths from settings or use defaults
        self.restricted_paths = getattr(settings, 'STAFF_RESTRICTED_PATHS', [
            '/admin/auth/group/',  # Group management
            '/admin/auth/user/add/',  # User creation (superuser only)
        ])

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Check if we're in admin and user is staff but not superuser
        if (request.path.startswith('/admin/') and 
            request.user.is_authenticated and 
            request.user.is_staff and 
            not request.user.is_superuser):
            
            # Check against restricted paths
            for path in self.restricted_paths:
                if request.path.startswith(path):
                    # Allow GET for viewing, block POST/PUT/PATCH/DELETE
                    if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                        messages.error(request, "You don't have permission to modify this section.")
                        return redirect('/admin/')
                    # Block add/change pages even with GET
                    if 'add' in request.path or 'change' in request.path:
                        messages.error(request, "You don't have permission to modify this section.")
                        return redirect('/admin/')
            
            # Special handling for services - can view but not edit
            if request.path.startswith('/admin/bookings/service/'):
                if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] or 'add' in request.path or 'change' in request.path:
                    messages.error(request, "You don't have permission to edit services.")
                    return redirect('/admin/')
        
        return None
