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
import json

from ..models import Service, Doctor, Calendar, ClinicSettings
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
    
    # Base queryset with optimized query - include patient_profile
    users = User.objects.select_related('patient_profile').prefetch_related('groups').order_by('-date_joined')
    
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
        
        # Try to get patient profile if it exists
        try:
            patient_profile = user.patient_profile
        except:
            patient_profile = None
        
        return render(request, 'bookings_v2/htmx_partials/user_detail.html', {
            'user': user,
            'patient_profile': patient_profile
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
        users = User.objects.select_related('patient_profile').prefetch_related('groups').order_by('-date_joined')
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
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            try:
                # Get or create patient profile
                patient_profile = user.patient_profile
                
                # Delete old profile picture if it exists
                if patient_profile.profile_picture:
                    patient_profile.profile_picture.delete(save=False)
                
                # Save new profile picture
                patient_profile.profile_picture = request.FILES['profile_picture']
                patient_profile.save()
                
            except Exception as e:
                # If patient profile doesn't exist, log the error but continue
                print(f"Could not update profile picture: {str(e)}")
        
        # Return updated user list with optimized query
        users = User.objects.select_related('patient_profile').prefetch_related('groups').order_by('-date_joined')
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


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_user_password_form(request, user_id):
    """HTMX endpoint to show password reset form"""
    try:
        user = User.objects.get(id=user_id)
        
        # Only superusers can reset passwords for staff accounts
        if not request.user.is_superuser:
            if user.is_staff or user.is_superuser:
                return HttpResponse('<div class="alert alert-danger">Only superusers can reset staff passwords</div>', status=403)
        
        return render(request, 'bookings_v2/htmx_partials/user_password_form.html', {
            'user': user
        })
    except User.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">User not found</div>', status=404)


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_user_password_reset(request, user_id):
    """HTMX endpoint to reset user password"""
    try:
        user = User.objects.get(id=user_id)
        
        # Only superusers can reset passwords for staff accounts
        if not request.user.is_superuser:
            if user.is_staff or user.is_superuser:
                return HttpResponse('<div class="alert alert-danger">Only superusers can reset staff passwords</div>', status=403)
        
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate passwords
        if not new_password or not confirm_password:
            return HttpResponse('<div class="alert alert-danger">Both password fields are required</div>', status=400)
        
        if new_password != confirm_password:
            return HttpResponse('<div class="alert alert-danger">Passwords do not match</div>', status=400)
        
        if len(new_password) < 8:
            return HttpResponse('<div class="alert alert-danger">Password must be at least 8 characters long</div>', status=400)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Return success message
        return HttpResponse(
            f'<div class="alert alert-success">'
            f'<i class="fas fa-check-circle"></i> Password successfully reset for {user.username}'
            f'</div>'
        )
        
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
                f'<tr><td colspan="6" class="text-center text-warning">Cannot delete service with {bookings_count} associated bookings</td></tr>',
                status=400
            )
        
        service_name = service.name
        service.delete()
        
        # Return empty response - HTMX will swap and remove the row
        response = HttpResponse('', status=200)
        response['HX-Trigger'] = 'showToast'
        return response
        
    except Service.DoesNotExist:
        return HttpResponse('<tr><td colspan="6" class="text-center text-danger">Service not found</td></tr>', status=404)
    except Exception as e:
        return HttpResponse(f'<tr><td colspan="6" class="text-center text-danger">Error: {str(e)}</td></tr>', status=400)


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_service_toggle(request, service_id):
    """Toggle service active status"""
    try:
        service = Service.objects.get(id=service_id)
        service.is_active = not service.is_active
        service.save()
        
        # Return updated service row
        return render(request, 'bookings_v2/partials/service_row.html', {
            'service': service
        })
        
    except Service.DoesNotExist:
        return HttpResponse('<tr><td colspan="6" class="text-center text-danger">Service not found</td></tr>', status=404)
    except Exception as e:
        return HttpResponse(f'<tr><td colspan="6" class="text-center text-danger">Error: {str(e)}</td></tr>', status=400)


# ========================================
# DOCTOR MANAGEMENT
# ========================================

@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_doctors_list(request):
    """List all doctors with search and filter"""
    search_query = request.GET.get('search', '').strip()
    availability_filter = request.GET.get('availability', '')
    
    doctors = Doctor.objects.all()
    
    # Apply search filter
    if search_query:
        doctors = doctors.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(specialization__icontains=search_query) |
            Q(license_number__icontains=search_query)
        )
    
    # Apply availability filter
    if availability_filter:
        is_available = availability_filter.lower() == 'available'
        doctors = doctors.filter(is_available=is_available)
    
    # Annotate with booking counts
    from django.db.models import Count
    doctors = doctors.annotate(
        total_bookings=Count('bookings'),
        active_bookings=Count('bookings', filter=Q(bookings__status__in=['Pending', 'Confirmed']))
    )
    
    return render(request, 'bookings_v2/htmx_partials/doctors_list.html', {
        'doctors': doctors,
        'search_query': search_query,
        'availability_filter': availability_filter
    })


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_doctor_create_form(request):
    """Display doctor creation form"""
    return render(request, 'bookings_v2/htmx_partials/doctor_form.html', {
        'is_edit': False
    })


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_doctor_create(request):
    """Create a new doctor"""
    try:
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'specialization', 'license_number', 'phone_number', 'email']
        for field in required_fields:
            if not request.POST.get(field):
                return HttpResponse(f'<div class="alert alert-danger">Error: {field.replace("_", " ").title()} is required</div>', status=400)
        
        doctor = Doctor.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            specialization=request.POST.get('specialization'),
            license_number=request.POST.get('license_number'),
            phone_number=request.POST.get('phone_number'),
            email=request.POST.get('email'),
            is_available=request.POST.get('is_available') == 'on',
            schedule_notes=request.POST.get('schedule_notes', ''),
            created_by=request.user
        )
        
        # Return updated doctors list
        from django.db.models import Count
        doctors = Doctor.objects.all().annotate(
            total_bookings=Count('bookings'),
            active_bookings=Count('bookings', filter=Q(bookings__status__in=['Pending', 'Confirmed']))
        )
        
        return render(request, 'bookings_v2/htmx_partials/doctors_list.html', {
            'doctors': doctors,
            'search_query': '',
            'availability_filter': ''
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}<br><small>{error_details}</small></div>', status=400)


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_doctor_edit_form(request, doctor_id):
    """Display doctor edit form"""
    try:
        doctor = Doctor.objects.get(id=doctor_id)
        return render(request, 'bookings_v2/htmx_partials/doctor_form.html', {
            'doctor': doctor,
            'is_edit': True
        })
    except Doctor.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Doctor not found</div>', status=404)


@login_required
@staff_required
@require_http_methods(["PUT", "POST"])
def htmx_doctor_update(request, doctor_id):
    """Update doctor information"""
    try:
        doctor = Doctor.objects.get(id=doctor_id)
        
        doctor.first_name = request.POST.get('first_name')
        doctor.last_name = request.POST.get('last_name')
        doctor.specialization = request.POST.get('specialization')
        doctor.license_number = request.POST.get('license_number')
        doctor.phone_number = request.POST.get('phone_number')
        doctor.email = request.POST.get('email')
        doctor.is_available = request.POST.get('is_available') == 'on'
        doctor.schedule_notes = request.POST.get('schedule_notes', '')
        
        doctor.save()
        
        # Return updated doctors list
        from django.db.models import Count
        doctors = Doctor.objects.all().annotate(
            total_bookings=Count('bookings'),
            active_bookings=Count('bookings', filter=Q(bookings__status__in=['Pending', 'Confirmed']))
        )
        
        return render(request, 'bookings_v2/htmx_partials/doctors_list.html', {
            'doctors': doctors,
            'search_query': '',
            'availability_filter': ''
        })
        
    except Doctor.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Doctor not found</div>', status=404)
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


@login_required
@staff_required
@require_http_methods(["DELETE"])
def htmx_doctor_delete(request, doctor_id):
    """Delete a doctor"""
    try:
        doctor = Doctor.objects.get(id=doctor_id)
        
        # Check if doctor has any bookings
        bookings_count = doctor.bookings.count()
        if bookings_count > 0:
            return HttpResponse(
                f'<tr><td colspan="8" class="text-center text-warning">Cannot delete doctor with {bookings_count} associated bookings</td></tr>',
                status=400
            )
        
        doctor.delete()
        
        # Return empty response - HTMX will swap and remove the row
        response = HttpResponse('', status=200)
        response['HX-Trigger'] = 'showToast'
        return response
        
    except Doctor.DoesNotExist:
        return HttpResponse('<tr><td colspan="8" class="text-center text-danger">Doctor not found</td></tr>', status=404)
    except Exception as e:
        return HttpResponse(f'<tr><td colspan="8" class="text-center text-danger">Error: {str(e)}</td></tr>', status=400)


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_doctor_schedule(request, doctor_id):
    """View doctor's schedule/appointments"""
    try:
        doctor = Doctor.objects.get(id=doctor_id)
        
        # Get date filter
        date_str = request.GET.get('date')
        if date_str:
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            bookings = doctor.bookings.filter(date=filter_date).exclude(status='Cancelled')
        else:
            from datetime import date
            filter_date = date.today()
            bookings = doctor.bookings.filter(date__gte=filter_date).exclude(status='Cancelled')[:20]
        
        bookings = bookings.select_related('service').order_by('date', 'time')
        
        return render(request, 'bookings_v2/htmx_partials/doctor_schedule.html', {
            'doctor': doctor,
            'bookings': bookings,
            'filter_date': filter_date
        })
        
    except Doctor.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Doctor not found</div>', status=404)


# ========================================
# CALENDAR MANAGEMENT (Blocked Dates)
# ========================================

@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_calendar_view(request):
    """Display calendar with blocked dates"""
    from datetime import date, timedelta
    from calendar import monthrange, Calendar as PythonCalendar
    import json
    from ..models import Calendar as CalendarModel
    
    # Get current month/year or from request
    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))
    
    # Get first and last day of the month
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    
    # Get blocked dates for this month
    blocked_dates = CalendarModel.objects.filter(
        date__gte=first_day,
        date__lte=last_day,
        event_type='blocked'
    )
    
    # Create a dict of blocked dates for easy lookup
    blocked_dict = {bd.date.strftime('%Y-%m-%d'): bd.reason or 'Blocked' for bd in blocked_dates}
    
    # Generate calendar data
    cal = PythonCalendar(6)  # 6 = Sunday as first day
    month_days = cal.monthdayscalendar(year, month)
    
    # Build calendar with date objects
    calendar_weeks = []
    today = date.today()
    
    for week in month_days:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(None)  # Empty cell
            else:
                day_date = date(year, month, day)
                date_str = day_date.strftime('%Y-%m-%d')
                is_sunday = day_date.weekday() == 6  # 6 = Sunday (0=Monday, 6=Sunday)
                week_data.append({
                    'day': day,
                    'date': day_date,
                    'date_str': date_str,
                    'is_blocked': date_str in blocked_dict,
                    'is_sunday': is_sunday,  # Mark Sundays
                    'reason': blocked_dict.get(date_str, 'Sunday - Clinic Closed' if is_sunday else ''),
                    'is_past': day_date < today,
                    'is_today': day_date == today
                })
        calendar_weeks.append(week_data)
    
    # Calculate previous and next month
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year
    
    return render(request, 'bookings_v2/htmx_partials/calendar_view.html', {
        'year': year,
        'month': month,
        'month_name': first_day.strftime('%B'),
        'calendar_weeks': calendar_weeks,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
    })


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_toggle_blocked_date(request):
    """Toggle a date as blocked/unblocked"""
    try:
        date_str = request.POST.get('date')
        reason = request.POST.get('reason', '')
        
        # Parse the date
        from datetime import datetime
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Check if date is already blocked
        blocked_date = Calendar.objects.filter(date=date_obj, event_type='blocked').first()
        
        if blocked_date:
            # Unblock the date
            blocked_date.delete()
            return HttpResponse(json.dumps({
                'status': 'unblocked',
                'message': f'{date_obj.strftime("%B %d, %Y")} is now available for booking'
            }), content_type='application/json')
        else:
            # Block the date
            Calendar.objects.create(
                event_type='blocked',
                date=date_obj,
                reason=reason if reason else 'Blocked by admin',
                created_by=request.user
            )
            return HttpResponse(json.dumps({
                'status': 'blocked',
                'message': f'{date_obj.strftime("%B %d, %Y")} is now blocked'
            }), content_type='application/json')
            
    except Exception as e:
        return HttpResponse(
            json.dumps({'status': 'error', 'message': str(e)}),
            content_type='application/json',
            status=400
        )


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_blocked_dates_list(request):
    """List all blocked dates"""
    from datetime import date
    
    # Get future blocked dates
    blocked_dates = Calendar.objects.filter(
        date__gte=date.today(),
        event_type='blocked'
    ).order_by('date')
    
    return render(request, 'bookings_v2/htmx_partials/blocked_dates_list.html', {
        'blocked_dates': blocked_dates
    })


@login_required
@staff_required
@require_http_methods(["DELETE"])
def htmx_delete_blocked_date(request, blocked_date_id):
    """Delete a blocked date"""
    try:
        blocked_date = Calendar.objects.get(id=blocked_date_id, event_type='blocked')
        date_str = blocked_date.date.strftime('%B %d, %Y')
        blocked_date.delete()
        
        response = HttpResponse('', status=200)
        response['HX-Trigger'] = 'refreshCalendar'
        return response
        
    except Calendar.DoesNotExist:
        return HttpResponse(
            '<tr><td colspan="4" class="text-center text-danger">Blocked date not found</td></tr>',
            status=404
        )


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


# ========================================
# CLINIC SETTINGS MANAGEMENT
# ========================================

@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_clinic_settings_form(request):
    """Display clinic settings form"""
    settings = ClinicSettings.load()
    return render(request, 'bookings_v2/htmx_partials/clinic_settings_form.html', {
        'settings': settings
    })


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_clinic_settings_update(request):
    """Update clinic settings"""
    try:
        settings = ClinicSettings.load()
        
        # Update fields
        settings.opening_time = request.POST.get('opening_time')
        settings.closing_time = request.POST.get('closing_time')
        settings.appointment_slot_duration = int(request.POST.get('appointment_slot_duration', 60))
        settings.clinic_name = request.POST.get('clinic_name', '')
        settings.clinic_address = request.POST.get('clinic_address', '')
        settings.clinic_phone = request.POST.get('clinic_phone', '')
        settings.clinic_email = request.POST.get('clinic_email', '')
        
        settings.save()
        
        # Return updated form with success message
        return HttpResponse(
            '<div class="alert alert-success"><i class="fas fa-check-circle"></i> Clinic settings updated successfully!</div>' +
            render(request, 'bookings_v2/htmx_partials/clinic_settings_form.html', {'settings': settings}).content.decode()
        )
        
    except Exception as e:
        import traceback
        return HttpResponse(
            f'<div class="alert alert-danger">Error updating settings: {str(e)}<br><pre>{traceback.format_exc()}</pre></div>',
            status=400
        )

