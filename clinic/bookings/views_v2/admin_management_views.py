"""
Admin and Service Management Views for v2
Handles user management and service CRUD operations
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..decorators import staff_required
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q
from datetime import datetime

from ..models import Service
from ..utils.reports import (
    generate_appointments_pdf,
    export_patients_csv,
    export_billing_csv,
    generate_services_pdf
)


# ========================================
# USER MANAGEMENT
# ========================================

@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_users_list(request):
    """HTMX endpoint to list all users"""
    # Get filter parameters
    role = request.GET.get('role', 'all')
    search = request.GET.get('search', '')
    
    # Base queryset with optimized query
    users = User.objects.prefetch_related('groups').order_by('-date_joined')
    
    # Apply role filter
    if role == 'staff':
        users = users.filter(is_staff=True)
    elif role == 'customer':
        users = users.filter(is_staff=False)
    elif role == 'superuser':
        users = users.filter(is_superuser=True)
    
    # Apply search filter
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # If not superuser, only show non-staff users and self
    if not request.user.is_superuser:
        users = users.filter(Q(is_staff=False) | Q(id=request.user.id))
    
    return render(request, 'bookings_v2/htmx_partials/users_list.html', {
        'users': users
    })


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_user_detail(request, user_id):
    """HTMX endpoint to show user details"""
    try:
        user = User.objects.get(id=user_id)
        
        # Non-superusers can only view non-staff users and themselves
        if not request.user.is_superuser:
            if user.is_staff and user.id != request.user.id:
                return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
        
        return render(request, 'bookings_v2/htmx_partials/user_detail.html', {
            'user': user
        })
    except User.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">User not found</div>', status=404)


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_user_edit(request, user_id):
    """HTMX endpoint to show user edit form"""
    try:
        edit_user = User.objects.get(id=user_id)
        
        # Only superusers can edit staff/superuser accounts
        if not request.user.is_superuser:
            if edit_user.is_staff or edit_user.is_superuser:
                return HttpResponse('<div class="alert alert-danger">Only superusers can edit staff accounts</div>', status=403)
        
        # Get user's group names
        user_groups = edit_user.groups.values_list('name', flat=True)
        
        # Try to get patient profile if it exists
        try:
            patient_profile = edit_user.patient_profile
        except:
            patient_profile = None
        
        return render(request, 'bookings_v2/htmx_partials/user_form.html', {
            'edit_user': edit_user,
            'user_groups': list(user_groups),
            'patient_profile': patient_profile
        })
    except User.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">User not found</div>', status=404)


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_user_create_form(request):
    """HTMX endpoint to show user creation form"""
    # Pass empty context to ensure no edit_user variable exists
    return render(request, 'bookings_v2/htmx_partials/user_form.html', {'edit_user': None})


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_user_create(request):
    """HTMX endpoint to create a new user"""
    try:
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        is_active = request.POST.get('is_active') == 'on'
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        groups_list = request.POST.getlist('groups')
        
        # Validation
        if not username or not email or not password1:
            return HttpResponse('<div class="alert alert-danger">Required fields missing</div>', status=400)
        
        if password1 != password2:
            return HttpResponse('<div class="alert alert-danger">Passwords do not match</div>', status=400)
        
        if User.objects.filter(username=username).exists():
            return HttpResponse(f'<div class="alert alert-danger">Username "{username}" already exists</div>', status=400)
        
        if User.objects.filter(email=email).exists():
            return HttpResponse(f'<div class="alert alert-danger">Email "{email}" is already registered</div>', status=400)
        
        # Only superusers can create staff/superuser accounts
        if not request.user.is_superuser and (is_staff or is_superuser):
            return HttpResponse('<div class="alert alert-danger">Only superusers can create staff accounts</div>', status=403)
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
            is_staff=is_staff,
            is_superuser=is_superuser
        )
        
        # Add to groups
        for group_name in groups_list:
            group, created = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
        
        # Auto-add to Customer group if not staff
        if not is_staff:
            customer_group, created = Group.objects.get_or_create(name='Customer')
            user.groups.add(customer_group)
        
        # Return updated user list with optimized query
        users = User.objects.prefetch_related('groups').order_by('-date_joined')
        if not request.user.is_superuser:
            users = users.filter(Q(is_staff=False) | Q(id=request.user.id))
        
        response = render(request, 'bookings_v2/htmx_partials/users_list.html', {'users': users})
        response['HX-Trigger'] = 'userCreated, showToast'
        return response
        
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_user_update(request, user_id):
    """HTMX endpoint to update user"""
    try:
        user = User.objects.get(id=user_id)
        
        # Only superusers can edit staff/superuser accounts
        if not request.user.is_superuser:
            if user.is_staff or user.is_superuser:
                return HttpResponse('<div class="alert alert-danger">Only superusers can edit staff accounts</div>', status=403)
        
        # Update fields
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.is_active = request.POST.get('is_active') == 'on'
        
        # Only superusers can change staff status
        if request.user.is_superuser:
            user.is_staff = request.POST.get('is_staff') == 'on'
            user.is_superuser = request.POST.get('is_superuser') == 'on'
        
        user.save()
        
        # Update groups
        groups_list = request.POST.getlist('groups')
        user.groups.clear()
        for group_name in groups_list:
            group, created = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
        
        # Return updated user list with optimized query
        users = User.objects.prefetch_related('groups').order_by('-date_joined')
        if not request.user.is_superuser:
            users = users.filter(Q(is_staff=False) | Q(id=request.user.id))
        
        response = render(request, 'bookings_v2/htmx_partials/users_list.html', {'users': users})
        response['HX-Trigger'] = 'userUpdated, showToast'
        return response
        
    except User.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">User not found</div>', status=404)
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


@login_required
@staff_required
@require_http_methods(["DELETE"])
def htmx_user_delete(request, user_id):
    """HTMX endpoint to deactivate user"""
    try:
        user = User.objects.get(id=user_id)
        
        # Cannot deactivate self
        if user.id == request.user.id:
            return HttpResponse('<div class="alert alert-danger">You cannot deactivate your own account</div>', status=403)
        
        # Only superusers can deactivate staff/superuser accounts
        if not request.user.is_superuser:
            if user.is_staff or user.is_superuser:
                return HttpResponse('<div class="alert alert-danger">Only superusers can deactivate staff accounts</div>', status=403)
        
        # Deactivate instead of delete
        user.is_active = False
        user.save()
        
        return HttpResponse('')  # Return empty for swap delete
        
    except User.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">User not found</div>', status=404)
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


# ========================================
# SERVICE MANAGEMENT
# ========================================

@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_services_list(request):
    """Return HTML fragment of all services"""
    services = Service.objects.all().order_by('name')
    
    return render(request, 'bookings_v2/partials/services_list.html', {
        'services': services
    })


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_service_create_form(request):
    """Return HTML form for creating a new service"""
    return render(request, 'bookings_v2/htmx_partials/service_form.html')


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_service_create(request):
    """Create a new service"""
    try:
        service = Service.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            price=request.POST.get('price'),
            image=request.FILES.get('image')
        )
        
        # Return updated services list
        services = Service.objects.all().order_by('name')
        response = render(request, 'bookings_v2/partials/services_list.html', {
            'services': services
        })
        response['HX-Trigger'] = 'showToast'
        return response
        
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_service_edit_form(request, service_id):
    """Return HTML form for editing a service"""
    try:
        service = Service.objects.get(id=service_id)
        return render(request, 'bookings_v2/htmx_partials/service_form.html', {
            'service': service
        })
    except Service.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Service not found</div>', status=404)


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_service_update(request, service_id):
    """Update an existing service"""
    try:
        service = Service.objects.get(id=service_id)
        service.name = request.POST.get('name')
        service.description = request.POST.get('description')
        service.price = request.POST.get('price')
        
        # Update image only if a new one is uploaded
        if request.FILES.get('image'):
            service.image = request.FILES.get('image')
        
        service.save()
        
        # Return updated services list
        services = Service.objects.all().order_by('name')
        response = render(request, 'bookings_v2/partials/services_list.html', {
            'services': services
        })
        response['HX-Trigger'] = 'showToast'
        return response
        
    except Service.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Service not found</div>', status=404)
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


@login_required
@staff_required
@require_http_methods(["DELETE"])
def htmx_service_delete(request, service_id):
    """Delete a service"""
    try:
        service = Service.objects.get(id=service_id)
        
        # Check if service is being used in any bookings
        bookings_count = service.bookings.count()
        if bookings_count > 0:
            return HttpResponse(
                f'<tr><td colspan="5" class="text-center text-warning">Cannot delete service with {bookings_count} associated bookings</td></tr>',
                status=400
            )
        
        service_name = service.name
        service.delete()
        
        # Return empty response - HTMX will swap and remove the row
        response = HttpResponse('', status=200)
        response['HX-Trigger'] = 'showToast'
        return response
        
    except Service.DoesNotExist:
        return HttpResponse('<tr><td colspan="5" class="text-center text-danger">Service not found</td></tr>', status=404)
    except Exception as e:
        return HttpResponse(f'<tr><td colspan="5" class="text-center text-danger">Error: {str(e)}</td></tr>', status=400)


# ========================================
# REPORTS
# ========================================

@login_required
@staff_required
@require_http_methods(["GET"])
def download_appointments_pdf(request):
    """Download appointments report as PDF"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')
    
    # Parse dates if provided
    start = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
    end = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
    
    return generate_appointments_pdf(start, end, status)


@login_required
@staff_required
@require_http_methods(["GET"])
def download_patients_csv(request):
    """Download patients export as CSV"""
    return export_patients_csv()


@login_required
@staff_required
@require_http_methods(["GET"])
def download_billing_csv(request):
    """Download billing records as CSV"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Parse dates if provided
    start = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
    end = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
    
    return export_billing_csv(start, end)


@login_required
@staff_required
@require_http_methods(["GET"])
def download_services_pdf(request):
    """Download services report as PDF"""
    return generate_services_pdf()
