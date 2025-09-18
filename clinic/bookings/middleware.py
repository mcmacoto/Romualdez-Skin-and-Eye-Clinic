from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

class StaffPermissionMiddleware:
    """
    Middleware to enforce staff permission restrictions
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Check if we're in admin and user is staff but not superuser
        if (request.path.startswith('/admin/') and 
            request.user.is_authenticated and 
            request.user.is_staff and 
            not request.user.is_superuser):
            
            # Restrict access to certain admin URLs
            restricted_paths = [
                '/admin/auth/group/',  # Group management
                '/admin/bookings/service/',  # Service management (unless viewing)
            ]
            
            for path in restricted_paths:
                if request.path.startswith(path):
                    if 'service' in path and request.method == 'GET' and 'add' not in request.path and 'change' not in request.path:
                        # Allow viewing services but not editing
                        continue
                    messages.error(request, "You don't have permission to access this section.")
                    return redirect('/admin/')
        
        return None