"""
Views for Bootstrap/HTMX/Alpine version (v2)
These views return HTML fragments for HTMX requests
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from datetime import datetime, time, date, timedelta
from django.db.models import Q, Sum

from .models import Billing, Booking, Service, Patient, MedicalRecord, Inventory, Appointment, Payment, StockTransaction, POSSale, POSSaleItem


def landing_v2(request):
    """Landing page - Portal selection"""
    # If user is already logged in, redirect appropriately
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('bookings_v2:admin_dashboard')
        else:
            return redirect('bookings_v2:home')
    return render(request, 'bookings_v2/landing_v2.html')


def login_v2(request):
    """Patient login"""
    if request.user.is_authenticated:
        # Redirect staff to dashboard, patients to home
        if request.user.is_staff:
            return redirect('bookings_v2:admin_dashboard')
        return redirect('bookings_v2:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Don't allow staff to login through patient portal
            if user.is_staff:
                messages.error(request, 'Staff members must use the Staff Portal.')
                return redirect('bookings_v2:staff_login')
            
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('bookings_v2:home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'bookings_v2/login_v2.html')


def staff_login_v2(request):
    """Staff login - redirects to admin dashboard"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('bookings_v2:admin_dashboard')
        else:
            messages.warning(request, 'You do not have staff access.')
            return redirect('bookings_v2:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Only allow staff members
            if not user.is_staff:
                messages.error(request, 'Access denied. Staff credentials required.')
                return render(request, 'bookings_v2/staff_login_v2.html')
            
            login(request, user)
            messages.success(request, f'Welcome, {user.get_full_name() or user.username}!')
            return redirect('bookings_v2:admin_dashboard')
        else:
            messages.error(request, 'Invalid staff credentials.')
    
    return render(request, 'bookings_v2/staff_login_v2.html')


def logout_v2(request):
    """Logout and redirect to landing"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('bookings_v2:landing')


@login_required(login_url='bookings_v2:login')
def patient_dashboard_v2(request):
    """Patient Dashboard - Shows patient's own appointments, records, and billing"""
    # Prevent staff from accessing patient portal
    if request.user.is_staff:
        messages.warning(request, 'Staff should use the Admin Dashboard.')
        return redirect('bookings_v2:admin_dashboard')
    
    # Check if user has a patient profile
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        # User logged in but no patient record - show message
        messages.warning(request, 'No patient profile found. Please contact the clinic.')
        return render(request, 'bookings_v2/patient_dashboard_v2.html', {
            'has_profile': False
        })
    
    # Get patient's bookings
    bookings = Booking.objects.filter(
        patient_email=request.user.email
    ).select_related('service').order_by('-date', '-time')
    
    upcoming_bookings = bookings.filter(
        date__gte=date.today(),
        status__in=['Pending', 'Confirmed']
    )
    
    past_bookings = bookings.filter(
        Q(date__lt=date.today()) | Q(status='Completed')
    ).exclude(status='Cancelled')
    
    # Get medical records
    medical_records = MedicalRecord.objects.filter(
        patient=patient
    ).order_by('-visit_date')
    
    # Get billing information
    billings = Billing.objects.filter(
        booking__patient_email=request.user.email
    ).select_related('booking__service').order_by('-issued_date')
    
    unpaid_bills = billings.filter(is_paid=False)
    total_outstanding = unpaid_bills.aggregate(total=Sum('balance'))['total'] or 0
    
    context = {
        'has_profile': True,
        'patient': patient,
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'total_bookings': bookings.count(),
        'medical_records': medical_records,
        'total_records': medical_records.count(),
        'billings': billings,
        'unpaid_bills': unpaid_bills,
        'total_outstanding': total_outstanding,
    }
    
    return render(request, 'bookings_v2/patient_dashboard_v2.html', context)


def home_v2(request):
    """Homepage - V2 with Bootstrap/HTMX/Alpine"""
    return render(request, 'bookings_v2/home_v2.html')


@login_required(login_url='bookings_v2:staff_login')
def admin_dashboard_v2(request):
    """Admin Dashboard - V2 with Bootstrap/HTMX/Alpine - Staff Only"""
    # Require staff access
    if not request.user.is_staff:
        messages.error(request, 'Access denied. You do not have staff permissions.')
        return redirect('bookings_v2:home')
    
    # Get statistics - Total Appointments shows bookings with consultation_status "Not Yet" or "Ongoing"
    total_appointments = Booking.objects.filter(
        status='Confirmed',
        consultation_status__in=['Not Yet', 'Ongoing']
    ).count()
    
    # Booking statistics
    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status='Pending').count()
    confirmed_bookings = Booking.objects.filter(status='Confirmed').count()
    completed_bookings = Booking.objects.filter(status='Completed').count()
    today_bookings = Booking.objects.filter(date=date.today()).count()
    
    # Patient and medical records statistics
    total_medical_records = MedicalRecord.objects.count()
    total_patient_profiles = Patient.objects.count()
    
    # Inventory statistics
    total_inventory_items = Inventory.objects.count()
    low_stock_items = Inventory.objects.filter(status='Low Stock').count()
    out_of_stock_items = Inventory.objects.filter(status='Out of Stock').count()
    
    # Billing statistics
    total_billings = Billing.objects.count()
    paid_bills = Billing.objects.filter(is_paid=True).count()
    unpaid_bills = Billing.objects.filter(is_paid=False).count()
    partially_paid_bills = Billing.objects.filter(is_paid=False, amount_paid__gt=0).count()
    
    total_revenue = Billing.objects.filter(is_paid=True).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    total_amount_billed = Billing.objects.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    total_amount_paid = Billing.objects.aggregate(
        total=Sum('amount_paid')
    )['total'] or 0
    
    total_balance_outstanding = Billing.objects.filter(is_paid=False).aggregate(
        total=Sum('balance')
    )['total'] or 0
    
    context = {
        'total_appointments': total_appointments,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'confirmed_bookings': confirmed_bookings,
        'completed_bookings': completed_bookings,
        'today_bookings': today_bookings,
        'total_medical_records': total_medical_records,
        'total_patient_profiles': total_patient_profiles,
        'total_inventory_items': total_inventory_items,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
        'total_billings': total_billings,
        'paid_bills': paid_bills,
        'unpaid_bills': unpaid_bills,
        'partially_paid_bills': partially_paid_bills,
        'total_revenue': total_revenue,
        'total_amount_billed': total_amount_billed,
        'total_amount_paid': total_amount_paid,
        'total_balance_outstanding': total_balance_outstanding,
    }
    
    return render(request, 'bookings_v2/admin_dashboard_v2.html', context)


def booking_v2(request):
    """Booking page - V2 with Bootstrap/HTMX/Alpine"""
    services = Service.objects.all()
    return render(request, 'bookings_v2/booking_v2.html', {
        'services': services
    })


def services_v2(request):
    """Services page - V2 with Bootstrap/HTMX/Alpine"""
    services = Service.objects.all()
    return render(request, 'bookings_v2/services_v2.html', {
        'services': services
    })


def about_v2(request):
    """About page - V2 with Bootstrap/HTMX/Alpine"""
    return render(request, 'bookings_v2/about_v2.html')


def contact_v2(request):
    """Contact page - V2 with Bootstrap/HTMX/Alpine"""
    return render(request, 'bookings_v2/contact_v2.html')


def success_v2(request):
    """Booking success page - V2"""
    booking_id = request.GET.get('booking_id')
    booking = None
    
    if booking_id:
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            pass
    
    return render(request, 'bookings_v2/success_v2.html', {
        'booking': booking
    })


# === HTMX Partial Views (Return HTML Fragments) ===

@login_required
@require_http_methods(["GET"])
def htmx_unpaid_patients(request):
    """Return HTML fragment of unpaid patients for HTMX"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    unpaid_billings = Billing.objects.filter(
        is_paid=False
    ).select_related('booking__service').order_by('-issued_date')
    
    return render(request, 'bookings_v2/partials/unpaid_patients.html', {
        'unpaid_billings': unpaid_billings
    })


@login_required
@require_http_methods(["GET"])
def htmx_all_billings(request):
    """Return HTML fragment of all billings for HTMX with optional search"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    billings = Billing.objects.select_related('booking__service')
    
    # Handle search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        from django.db.models import Q
        billings = billings.filter(
            Q(booking__patient_name__icontains=search_query) |
            Q(booking__patient_email__icontains=search_query) |
            Q(booking__service__name__icontains=search_query)
        )
    
    billings = billings.order_by('-issued_date')
    
    # Calculate summary statistics
    from decimal import Decimal
    total_count = billings.count()
    paid_count = billings.filter(is_paid=True).count()
    unpaid_count = billings.filter(is_paid=False, amount_paid=0).count()
    partial_count = billings.filter(is_paid=False, amount_paid__gt=0).count()
    
    total_revenue = sum(b.total_amount for b in billings)
    amount_collected = sum(b.amount_paid for b in billings)
    outstanding_balance = sum(b.balance for b in billings)
    
    return render(request, 'bookings_v2/partials/all_billings_list.html', {
        'billings': billings,
        'total_count': total_count,
        'paid_count': paid_count,
        'unpaid_count': unpaid_count,
        'partial_count': partial_count,
        'total_revenue': total_revenue,
        'amount_collected': amount_collected,
        'outstanding_balance': outstanding_balance,
    })


@login_required
@require_http_methods(["POST"])
def htmx_mark_paid(request, billing_id):
    """Mark billing as paid - returns updated HTML fragment"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        billing = Billing.objects.get(id=billing_id)
        billing.is_paid = True
        billing.amount_paid = billing.total_amount
        billing.balance = 0
        billing.save()
        
        # Return success message to replace the row
        return HttpResponse(
            '<div class="alert alert-success alert-dismissible fade show" role="alert">'
            f'✓ Billing for {billing.booking.patient_name} marked as paid!'
            '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>'
            '</div>'
        )
    except Billing.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Billing not found</div>',
            status=404
        )


@login_required
@require_http_methods(["GET"])
def htmx_paid_billings(request):
    """Return HTML fragment of paid billings"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    billings = Billing.objects.select_related(
        'booking__service'
    ).filter(is_paid=True).order_by('-issued_date')
    
    return render(request, 'bookings_v2/partials/all_billings_list.html', {
        'billings': billings
    })


@login_required
@require_http_methods(["GET"])
def htmx_unpaid_billings(request):
    """Return HTML fragment of unpaid billings"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    billings = Billing.objects.select_related(
        'booking__service'
    ).filter(is_paid=False).order_by('-issued_date')
    
    return render(request, 'bookings_v2/partials/all_billings_list.html', {
        'billings': billings
    })


@require_http_methods(["GET"])
def htmx_services_preview(request):
    """Return HTML fragment of services for homepage preview"""
    services = Service.objects.all()[:3]  # Get first 3 services
    
    return render(request, 'bookings_v2/partials/services_preview.html', {
        'services': services
    })


@require_http_methods(["GET"])
def htmx_time_slots(request):
    """Return HTML fragment of available time slots based on service and date"""
    service_id = request.GET.get('service')
    booking_date = request.GET.get('date')
    
    # If no service or date selected, return empty select with instruction
    if not service_id or not booking_date:
        return HttpResponse(
            '<select class="form-select" name="time" required disabled>'
            '<option value="">Select service and date first...</option>'
            '</select>'
        )
    
    try:
        # Parse the date
        selected_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
        
        # Check if date is in the past
        if selected_date < date.today():
            return render(request, 'bookings_v2/partials/time_slots.html', {
                'available_slots': []
            })
        
        # Define clinic hours (9 AM to 5 PM, with 1-hour slots)
        clinic_hours = [
            {'time': '09:00', 'display': '9:00 AM'},
            {'time': '10:00', 'display': '10:00 AM'},
            {'time': '11:00', 'display': '11:00 AM'},
            {'time': '13:00', 'display': '1:00 PM'},
            {'time': '14:00', 'display': '2:00 PM'},
            {'time': '15:00', 'display': '3:00 PM'},
            {'time': '16:00', 'display': '4:00 PM'},
        ]
        
        # Get already booked time slots for this date
        booked_times = Booking.objects.filter(
            date=selected_date,
            status__in=['Pending', 'Confirmed']
        ).values_list('time', flat=True)
        
        # Convert booked times to strings for comparison
        booked_time_strings = [t.strftime('%H:%M') for t in booked_times]
        
        # Filter out booked slots
        available_slots = [
            slot for slot in clinic_hours 
            if slot['time'] not in booked_time_strings
        ]
        
        return render(request, 'bookings_v2/partials/time_slots.html', {
            'available_slots': available_slots
        })
        
    except ValueError:
        # Invalid date format - return empty select
        return HttpResponse(
            '<select class="form-select" name="time" required disabled>'
            '<option value="">Invalid date format</option>'
            '</select>'
        )


@require_http_methods(["POST"])
def htmx_submit_booking(request):
    """Handle HTMX booking form submission"""
    try:
        # Extract form data
        service_id = request.POST.get('service')
        patient_name = request.POST.get('patient_name')
        patient_email = request.POST.get('patient_email')
        patient_phone = request.POST.get('patient_phone')
        booking_date = request.POST.get('date')
        booking_time = request.POST.get('time')
        notes = request.POST.get('notes', '')
        
        # Validate required fields
        if not all([service_id, patient_name, patient_email, patient_phone, booking_date, booking_time]):
            return HttpResponse(
                '<div class="alert alert-danger">'
                '<i class="fas fa-exclamation-circle"></i> Please fill in all required fields.'
                '</div>',
                status=400
            )
        
        # Get service
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            return HttpResponse(
                '<div class="alert alert-danger">'
                '<i class="fas fa-exclamation-circle"></i> Invalid service selected.'
                '</div>',
                status=400
            )
        
        # Parse date and time
        try:
            parsed_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
            parsed_time = datetime.strptime(booking_time, '%H:%M').time()
        except ValueError:
            return HttpResponse(
                '<div class="alert alert-danger">'
                '<i class="fas fa-exclamation-circle"></i> Invalid date or time format.'
                '</div>',
                status=400
            )
        
        # Check if slot is still available
        existing_booking = Booking.objects.filter(
            date=parsed_date,
            time=parsed_time,
            status__in=['Pending', 'Confirmed']
        ).exists()
        
        if existing_booking:
            return HttpResponse(
                '<div class="alert alert-warning">'
                '<i class="fas fa-exclamation-triangle"></i> This time slot is no longer available. '
                'Please select a different time.'
                '</div>',
                status=400
            )
        
        # Create the booking
        booking = Booking.objects.create(
            patient_name=patient_name,
            patient_email=patient_email,
            patient_phone=patient_phone,
            date=parsed_date,
            time=parsed_time,
            service=service,
            notes=notes,
            status='Pending',
            created_by=request.user if request.user.is_authenticated else None
        )
        
        # Redirect to success page using HX-Redirect
        response = HttpResponse()
        response['HX-Redirect'] = f'/v2/success/?booking_id={booking.id}'
        return response
        
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Booking error: {str(e)}")
        return HttpResponse(
            '<div class="alert alert-danger">'
            f'<i class="fas fa-exclamation-circle"></i> An error occurred: {str(e)}'
            '</div>',
            status=500
        )


@require_http_methods(["POST"])
def htmx_submit_contact(request):
    """
    Handle contact form submission via HTMX
    Returns HTML fragment with success/error message
    """
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Basic validation
        errors = []
        if len(name) < 2:
            errors.append("Name must be at least 2 characters")
        if len(email) < 5 or '@' not in email:
            errors.append("Please enter a valid email address")
        if len(subject) < 3:
            errors.append("Please select a subject")
        if len(message) < 10:
            errors.append("Message must be at least 10 characters")
        
        if errors:
            error_html = '<div class="alert alert-danger">'
            error_html += '<i class="fas fa-exclamation-circle me-2"></i><strong>Please correct the following errors:</strong><ul class="mb-0 mt-2">'
            for error in errors:
                error_html += f'<li>{error}</li>'
            error_html += '</ul></div>'
            return HttpResponse(error_html, status=400)
        
        # In a real application, you would:
        # 1. Save to database (ContactMessage model)
        # 2. Send email notification to clinic staff
        # 3. Send confirmation email to user
        
        # For now, we'll just log it and return success
        print(f"Contact form submission from {name} ({email})")
        print(f"Subject: {subject}")
        print(f"Phone: {phone}")
        print(f"Message: {message}")
        
        # Return success message
        success_html = f'''
        <div class="alert alert-success">
            <i class="fas fa-check-circle me-2"></i>
            <strong>Thank you for contacting us, {name}!</strong>
            <p class="mb-0 mt-2">
                We've received your message about <strong>"{subject}"</strong> and will respond to 
                <strong>{email}</strong> within 24 hours during business days.
            </p>
        </div>
        <script>
            // Reset the form
            document.querySelector('form').reset();
            // Reset Alpine.js data
            if (window.Alpine) {{
                Alpine.store('contactForm', {{
                    name: '',
                    email: '',
                    phone: '',
                    subject: '',
                    message: '',
                    errors: {{}}
                }});
            }}
        </script>
        '''
        
        return HttpResponse(success_html)
        
    except Exception as e:
        print(f"Contact form error: {str(e)}")
        return HttpResponse(
            '<div class="alert alert-danger">'
            '<i class="fas fa-exclamation-circle"></i> '
            'An error occurred while sending your message. Please try again or contact us directly.'
            '</div>',
            status=500
        )


# === Additional HTMX Endpoints for Admin Dashboard ===

@login_required
@require_http_methods(["GET"])
def htmx_appointments_list(request):
    """Return HTML fragment of all appointments with optional search and filter"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    # Get filter parameter
    filter_status = request.GET.get('status', 'all')
    
    appointments = Booking.objects.select_related('service')
    
    # Handle search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        from django.db.models import Q
        appointments = appointments.filter(
            Q(patient_name__icontains=search_query) |
            Q(patient_email__icontains=search_query) |
            Q(patient_phone__icontains=search_query)
        )
    
    # Apply filters
    if filter_status == 'confirmed':
        appointments = appointments.filter(status='Confirmed')
    elif filter_status == 'pending':
        appointments = appointments.filter(status='Pending')
    elif filter_status == 'completed':
        appointments = appointments.filter(status='Completed')
    elif filter_status == 'today':
        appointments = appointments.filter(date=date.today())
    
    appointments = appointments.order_by('-date', '-time')
    
    return render(request, 'bookings_v2/partials/appointments_list.html', {
        'appointments': appointments
    })


@login_required
@require_http_methods(["POST"])
def htmx_mark_consultation_done(request, booking_id):
    """Mark consultation as done - returns updated HTML fragment"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        booking = Booking.objects.select_related('service').get(id=booking_id)
        booking.consultation_status = 'Done'
        booking.status = 'Completed'
        booking.save()
        
        # Return the updated row
        return render(request, 'bookings_v2/partials/appointments_list.html', {
            'appointments': [booking]
        })
    except Booking.DoesNotExist:
        return HttpResponse(
            '<tr><td colspan="7" class="text-center text-danger">Booking not found</td></tr>',
            status=404
        )


@login_required
@require_http_methods(["POST"])
def htmx_update_consultation_status(request, booking_id):
    """Update consultation status via dropdown - returns updated row"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        booking = Booking.objects.select_related('service').get(id=booking_id)
        new_status = request.POST.get('consultation_status')
        
        # Validate status
        valid_statuses = ['Not Yet', 'Ongoing', 'Done']
        if new_status not in valid_statuses:
            return HttpResponse(
                '<tr><td colspan="7" class="text-center text-danger">Invalid status</td></tr>',
                status=400
            )
        
        booking.consultation_status = new_status
        
        # If marking as done, also mark booking as completed
        if new_status == 'Done':
            booking.status = 'Completed'
        
        booking.save()
        
        # Return the updated row
        return render(request, 'bookings_v2/partials/appointments_list.html', {
            'appointments': [booking]
        })
    except Booking.DoesNotExist:
        return HttpResponse(
            '<tr><td colspan="7" class="text-center text-danger">Booking not found</td></tr>',
            status=404
        )


@login_required
@require_http_methods(["DELETE"])
def htmx_delete_appointment(request, booking_id):
    """Delete appointment - returns empty response to remove row"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        booking = Booking.objects.get(id=booking_id)
        
        # Check if there are medical records associated (soft delete consideration)
        has_records = hasattr(booking, 'patient') and booking.patient and booking.patient.medicalrecord_set.exists()
        
        if has_records:
            # Soft delete: just mark as cancelled instead of hard delete
            booking.status = 'Cancelled'
            booking.save()
            message = 'Appointment cancelled (has medical records)'
        else:
            # Hard delete: completely remove the appointment
            booking.delete()
            message = 'Appointment deleted successfully'
        
        # Return empty response - HTMX will swap and remove the row
        return HttpResponse('', status=200)
        
    except Booking.DoesNotExist:
        return HttpResponse(
            '<tr><td colspan="7" class="text-center text-danger">Appointment not found</td></tr>',
            status=404
        )


@login_required
@require_http_methods(["GET"])
def htmx_patients_list(request):
    """Return HTML fragment of all patients with optional search"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    patients = Patient.objects.select_related('user').prefetch_related('medical_records')
    
    # Handle search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        from django.db.models import Q
        patients = patients.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    patients = patients.order_by('-created_at')
    
    return render(request, 'bookings_v2/partials/patients_list.html', {
        'patients': patients
    })


@login_required
@require_http_methods(["GET"])
def htmx_patient_records(request, patient_id):
    """Return HTML fragment of medical records for a specific patient"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        patient = Patient.objects.get(id=patient_id)
        records = MedicalRecord.objects.filter(
            patient=patient
        ).select_related('created_by').prefetch_related(
            'prescriptions', 'images'
        ).order_by('-visit_date')
        
        return render(request, 'bookings_v2/partials/patient_medical_records.html', {
            'records': records,
            'patient': patient
        })
    except Patient.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Patient not found</div>',
            status=404
        )


@login_required
def htmx_patient_detail(request, patient_id):
    """Return HTML fragment with detailed patient profile"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        patient = Patient.objects.select_related('user').get(id=patient_id)
        
        # Get statistics
        total_appointments = Booking.objects.filter(
            patient_name=patient.user.get_full_name()
        ).count()
        
        total_records = MedicalRecord.objects.filter(patient=patient).count()
        
        # Calculate outstanding balance
        unpaid_billings = Billing.objects.filter(
            patient=patient,
            is_paid=False
        )
        total_outstanding = sum(billing.total_amount for billing in unpaid_billings) if unpaid_billings.exists() else 0
        
        # Get recent appointments (last 5)
        recent_appointments = Booking.objects.filter(
            patient_name=patient.user.get_full_name()
        ).select_related('service').order_by('-date', '-time')[:5]
        
        # Get recent medical records (last 3)
        recent_records = MedicalRecord.objects.filter(
            patient=patient
        ).select_related('created_by').prefetch_related('prescriptions').order_by('-visit_date')[:3]
        
        # Get recent billings (last 5)
        recent_billings = Billing.objects.filter(
            patient=patient
        ).order_by('-date_issued')[:5]
        
        context = {
            'patient': patient,
            'stats': {
                'total_appointments': total_appointments,
                'total_records': total_records,
                'total_outstanding': total_outstanding,
            },
            'recent_appointments': recent_appointments,
            'recent_records': recent_records,
            'recent_billings': recent_billings,
        }
        
        return render(request, 'bookings_v2/partials/patient_detail.html', context)
    except Patient.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Patient not found</div>',
            status=404
        )
    except Exception as e:
        import traceback
        return HttpResponse(
            f'<div class="alert alert-danger">Error loading patient: {str(e)}<br><pre>{traceback.format_exc()}</pre></div>',
            status=500
        )


@login_required
@require_http_methods(["DELETE"])
def htmx_delete_patient(request, patient_id):
    """Delete patient - handles cascade and returns empty response"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        patient = Patient.objects.select_related('user').get(id=patient_id)
        
        # Check for unpaid bills
        unpaid_bills = Billing.objects.filter(
            patient=patient,
            payment_status__in=['Pending', 'Partial']
        ).exists()
        
        if unpaid_bills:
            # Return error message - don't delete patients with unpaid bills
            return HttpResponse(
                '<tr><td colspan="7" class="text-center text-warning">Cannot delete patient with unpaid bills</td></tr>',
                status=400
            )
        
        # Get the associated user before deleting patient
        user = patient.user
        
        # Delete patient (will cascade to bookings, medical records, billing due to Django's on_delete)
        patient.delete()
        
        # Also delete the associated user account
        if user:
            user.delete()
        
        # Return empty response - HTMX will swap and remove the row
        return HttpResponse('', status=200)
        
    except Patient.DoesNotExist:
        return HttpResponse(
            '<tr><td colspan="7" class="text-center text-danger">Patient not found</td></tr>',
            status=404
        )


@login_required
@require_http_methods(["GET"])
def htmx_medical_records_list(request):
    """Return HTML fragment of all medical records with optional search"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    records = MedicalRecord.objects.select_related(
        'patient__user', 'created_by'
    ).prefetch_related(
        'prescriptions', 'images'
    )
    
    # Handle search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        from django.db.models import Q
        records = records.filter(
            Q(patient__user__first_name__icontains=search_query) |
            Q(patient__user__last_name__icontains=search_query) |
            Q(diagnosis__icontains=search_query) |
            Q(chief_complaint__icontains=search_query) |
            Q(treatment_plan__icontains=search_query)
        )
    
    records = records.order_by('-visit_date')
    
    return render(request, 'bookings_v2/partials/medical_records_list.html', {
        'records': records
    })


@login_required
@require_http_methods(["GET"])
def htmx_medical_record_edit_form(request, record_id):
    """Return HTML fragment with medical record edit form"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        record = MedicalRecord.objects.select_related(
            'patient__user'
        ).prefetch_related(
            'prescriptions', 'images'
        ).get(id=record_id)
        
        # Check if opened from patient records view
        patient_id = request.GET.get('patient_id')
        
        return render(request, 'bookings_v2/htmx_partials/medical_record_form.html', {
            'record': record,
            'patient_id': patient_id  # Pass to template for context-aware navigation
        })
    except MedicalRecord.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Medical record not found</div>',
            status=404
        )


@login_required
@require_http_methods(["PUT", "POST"])
def htmx_medical_record_update(request, record_id):
    """Update medical record and return updated list"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        record = MedicalRecord.objects.get(id=record_id)
        
        # Parse visit date and time
        visit_date_str = request.POST.get('visit_date')
        visit_time_str = request.POST.get('visit_time', '00:00')
        
        if visit_date_str:
            # Combine date and time
            visit_datetime_str = f"{visit_date_str} {visit_time_str}"
            record.visit_date = datetime.strptime(visit_datetime_str, '%Y-%m-%d %H:%M')
        
        # Update fields
        record.chief_complaint = request.POST.get('chief_complaint')
        record.symptoms = request.POST.get('symptoms', '')
        record.diagnosis = request.POST.get('diagnosis', '')
        record.treatment_plan = request.POST.get('treatment_plan', '')
        
        # Vital signs
        record.blood_pressure = request.POST.get('blood_pressure', '')
        record.temperature = request.POST.get('temperature', '')
        record.heart_rate = request.POST.get('heart_rate', '')
        record.weight = request.POST.get('weight', '')
        record.height = request.POST.get('height', '')
        
        # Notes and follow-up
        record.notes = request.POST.get('notes', '')
        
        follow_up_date = request.POST.get('follow_up_date')
        if follow_up_date:
            record.follow_up_date = follow_up_date
        else:
            record.follow_up_date = None
        
        record.save()
        
        # Check if we should return to patient records or general list
        patient_id = request.GET.get('patient_id')
        
        if patient_id:
            # Return to patient-specific records view
            try:
                patient = Patient.objects.get(id=patient_id)
                records = MedicalRecord.objects.filter(
                    patient=patient
                ).select_related('created_by').prefetch_related(
                    'prescriptions', 'images'
                ).order_by('-visit_date')
                
                return render(request, 'bookings_v2/partials/patient_medical_records.html', {
                    'records': records,
                    'patient': patient
                })
            except Patient.DoesNotExist:
                pass
        
        # Default: Return to general medical records list
        records = MedicalRecord.objects.select_related(
            'patient__user', 'created_by'
        ).prefetch_related(
            'prescriptions', 'images'
        ).order_by('-visit_date')
        
        return render(request, 'bookings_v2/partials/medical_records_list.html', {
            'records': records
        })
        
    except MedicalRecord.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Medical record not found</div>',
            status=404
        )
    except Exception as e:
        return HttpResponse(
            f'<div class="alert alert-danger">Error updating record: {str(e)}</div>',
            status=500
        )


@login_required
@require_http_methods(["GET"])
def htmx_medical_record_create_form(request):
    """Return HTML fragment with medical record creation form"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    # Get all patients for the dropdown
    patients = Patient.objects.select_related('user').order_by('user__last_name', 'user__first_name')
    
    return render(request, 'bookings_v2/htmx_partials/medical_record_create_form.html', {
        'patients': patients
    })


@login_required
@require_http_methods(["POST"])
def htmx_medical_record_create(request):
    """Create new medical record and return updated list"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        from datetime import datetime
        
        # Get patient
        patient_id = request.POST.get('patient_id')
        patient = Patient.objects.get(id=patient_id)
        
        # Parse visit date
        visit_date_str = request.POST.get('visit_date')
        visit_time_str = request.POST.get('visit_time', '00:00')
        visit_datetime = datetime.strptime(f"{visit_date_str} {visit_time_str}", "%Y-%m-%d %H:%M")
        
        # Create record
        record = MedicalRecord.objects.create(
            patient=patient,
            visit_date=visit_datetime,
            chief_complaint=request.POST.get('chief_complaint'),
            symptoms=request.POST.get('symptoms', ''),
            diagnosis=request.POST.get('diagnosis', ''),
            treatment_plan=request.POST.get('treatment_plan', ''),
            temperature=request.POST.get('temperature') or None,
            blood_pressure_systolic=request.POST.get('blood_pressure_systolic') or None,
            blood_pressure_diastolic=request.POST.get('blood_pressure_diastolic') or None,
            heart_rate=request.POST.get('heart_rate') or None,
            weight=request.POST.get('weight') or None,
            height=request.POST.get('height') or None,
            follow_up_date=request.POST.get('follow_up_date') or None,
            additional_notes=request.POST.get('additional_notes', ''),
            created_by=request.user
        )
        
        # Reload record with related data
        record = MedicalRecord.objects.select_related(
            'patient__user'
        ).prefetch_related(
            'prescriptions', 'images'
        ).get(id=record.id)
        
        # Return the edit form so user can add prescriptions and images
        return render(request, 'bookings_v2/htmx_partials/medical_record_form.html', {
            'record': record,
            'just_created': True  # Flag to show success message
        })
        
    except Patient.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Patient not found</div>',
            status=404
        )
    except Exception as e:
        import traceback
        error_msg = f'<div class="alert alert-danger">Error creating record: {str(e)}<br><pre>{traceback.format_exc()}</pre></div>'
        print(f"Error in htmx_medical_record_create: {traceback.format_exc()}")
        return HttpResponse(error_msg, status=500)


@login_required
@require_http_methods(["GET"])
def htmx_medical_images(request, record_id):
    """Return HTML fragment showing medical images for a specific record"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        record = MedicalRecord.objects.select_related('patient__user').prefetch_related('images').get(id=record_id)
        images = record.images.all()
        
        html = f'''
        <div class="mb-3 d-flex justify-content-between align-items-center">
            <div>
                <h6><strong>Patient:</strong> {record.patient.user.get_full_name()}</h6>
                <p class="text-muted mb-0">
                    <strong>Visit Date:</strong> {record.visit_date.strftime('%B %d, %Y')}
                </p>
            </div>
            <button 
                class="btn btn-sm btn-info"
                hx-get="/admin/htmx/medical-image/upload-form/{record_id}/"
                hx-target="#medicalImagesModalBody"
                hx-swap="innerHTML"
            >
                <i class="fas fa-plus me-2"></i>Upload Image
            </button>
        </div>
        '''
        
        if not images:
            html += '<div class="alert alert-info">No medical images found for this record. Click "Upload Image" to add one.</div>'
        else:
            html += '<div class="row g-3">'
            for image in images:
                html += f'''
                <div class="col-md-4">
                    <div class="card">
                        <img src="{image.image.url}" class="card-img-top" alt="{image.title}" 
                             style="height: 250px; object-fit: cover; cursor: pointer;"
                             onclick="window.open('{image.image.url}', '_blank')">
                        <div class="card-body">
                            <h6 class="card-title">{image.title or "Medical Image"}</h6>
                            <p class="card-text">
                                <small class="text-muted">
                                    <strong>Type:</strong> {image.get_image_type_display()}<br>
                                    {f"<strong>Description:</strong> {image.description}" if image.description else ""}
                                </small>
                            </p>
                            <button 
                                class="btn btn-sm btn-danger w-100"
                                hx-delete="/admin/htmx/medical-image/{image.id}/delete/"
                                hx-target="#medicalImagesModalBody"
                                hx-confirm="Are you sure you want to delete this image: {image.title}?"
                            >
                                <i class="fas fa-trash me-2"></i>Delete
                            </button>
                        </div>
                    </div>
                </div>
                '''
            html += '</div>'
        
        return HttpResponse(html)
    except MedicalRecord.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Medical record not found</div>',
            status=404
        )


@login_required
@require_http_methods(["GET"])
def htmx_prescriptions(request, record_id):
    """Return HTML fragment showing prescriptions for a specific record"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        record = MedicalRecord.objects.prefetch_related(
            'prescriptions__medicine'
        ).get(id=record_id)
        
        patient = record.patient
        prescriptions = record.prescriptions.all()
        
        if not prescriptions:
            return HttpResponse(
                '<div class="alert alert-info">No prescriptions found for this record.</div>'
            )
        
        html = f'''
        <div class="mb-3 d-flex justify-content-between align-items-center">
            <div>
                <h6><strong>Patient:</strong> {patient.user.get_full_name()}</h6>
                <p class="text-muted mb-0">
                    <strong>Visit Date:</strong> {record.visit_date.strftime('%B %d, %Y at %I:%M %p')}
                </p>
            </div>
            <button 
                class="btn btn-sm btn-success"
                hx-get="/admin/htmx/prescription/create-form/{record_id}/"
                hx-target="#prescriptionsModalBody"
                hx-swap="innerHTML"
            >
                <i class="fas fa-plus me-2"></i>Add Prescription
            </button>
        </div>
        <div class="table-responsive">
            <table class="table table-hover">
                <thead class="table-success">
                    <tr>
                        <th><i class="fas fa-pills me-2"></i>Medication</th>
                        <th><i class="fas fa-prescription-bottle me-2"></i>Dosage</th>
                        <th><i class="fas fa-clock me-2"></i>Duration</th>
                        <th><i class="fas fa-dollar-sign me-2"></i>Price</th>
                        <th><i class="fas fa-info-circle me-2"></i>Instructions</th>
                        <th class="text-center"><i class="fas fa-cog me-2"></i>Actions</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        total_price = 0
        for prescription in prescriptions:
            total_price += prescription.total_price
            instructions = prescription.instructions or 'Follow standard dosing instructions'
            html += f'''
                <tr>
                    <td>
                        <strong>{prescription.medicine.name}</strong>
                        <br><small class="text-muted">Qty: {prescription.quantity}</small>
                    </td>
                    <td>{prescription.dosage}</td>
                    <td>{prescription.duration or 'As needed'}</td>
                    <td>₱{prescription.total_price:,.2f}</td>
                    <td><small>{instructions}</small></td>
                    <td class="text-center">
                        <button 
                            class="btn btn-sm btn-danger"
                            hx-delete="/admin/htmx/prescription/{prescription.id}/delete/"
                            hx-target="#prescriptionsModalBody"
                            hx-confirm="Are you sure you want to delete this prescription for {prescription.medicine.name}?"
                        >
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            '''
        
        html += f'''
                </tbody>
                <tfoot class="table-light">
                    <tr>
                        <th colspan="3" class="text-end">Total:</th>
                        <th>₱{total_price:,.2f}</th>
                        <th colspan="2"></th>
                    </tr>
                </tfoot>
            </table>
        </div>
        <div class="mt-3">
            <small class="text-muted">
                <i class="fas fa-user-md me-2"></i>
                Prescribed by: {record.created_by.get_full_name() if record.created_by else 'N/A'}
                on {record.created_at.strftime('%B %d, %Y')}
            </small>
        </div>
        '''
        
        return HttpResponse(html)
    except MedicalRecord.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Medical record not found</div>',
            status=404
        )


@login_required
@require_http_methods(["GET"])
def htmx_prescription_create_form(request, record_id):
    """Return HTML fragment with prescription creation form"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        record = MedicalRecord.objects.select_related('patient__user').get(id=record_id)
        # Get all medicines from inventory
        medicines = Inventory.objects.filter(
            category='Medicine',
            status__in=['In Stock', 'Low Stock']
        ).order_by('name')
        
        return render(request, 'bookings_v2/htmx_partials/prescription_create_form.html', {
            'record': record,
            'medicines': medicines
        })
    except MedicalRecord.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Medical record not found</div>',
            status=404
        )


@login_required
@require_http_methods(["POST"])
def htmx_prescription_create(request, record_id):
    """Create prescription and return updated prescription list"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        from bookings.models import Prescription
        
        record = MedicalRecord.objects.get(id=record_id)
        medicine = Inventory.objects.get(id=request.POST.get('medicine_id'))
        
        # Create prescription
        prescription = Prescription.objects.create(
            medical_record=record,
            medicine=medicine,
            quantity=int(request.POST.get('quantity', 1)),
            dosage=request.POST.get('dosage'),
            duration=request.POST.get('duration', ''),
            instructions=request.POST.get('instructions', ''),
            unit_price=medicine.price,
            prescribed_by=request.user
        )
        
        # Return updated prescription list
        return htmx_prescriptions(request, record_id)
        
    except (MedicalRecord.DoesNotExist, Inventory.DoesNotExist):
        return HttpResponse(
            '<div class="alert alert-danger">Record or medicine not found</div>',
            status=404
        )
    except Exception as e:
        import traceback
        error_msg = f'<div class="alert alert-danger">Error creating prescription: {str(e)}<br><pre>{traceback.format_exc()}</pre></div>'
        return HttpResponse(error_msg, status=500)


@login_required
@require_http_methods(["DELETE"])
def htmx_prescription_delete(request, prescription_id):
    """Delete prescription and return updated list"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        from bookings.models import Prescription
        
        prescription = Prescription.objects.select_related('medical_record').get(id=prescription_id)
        record_id = prescription.medical_record.id
        prescription.delete()
        
        # Return updated prescription list
        return htmx_prescriptions(request, record_id)
        
    except Prescription.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Prescription not found</div>',
            status=404
        )


@login_required
@require_http_methods(["GET"])
def htmx_medical_image_upload_form(request, record_id):
    """Return HTML fragment with medical image upload form"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        record = MedicalRecord.objects.select_related('patient__user').get(id=record_id)
        
        return render(request, 'bookings_v2/htmx_partials/medical_image_upload_form.html', {
            'record': record
        })
    except MedicalRecord.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Medical record not found</div>',
            status=404
        )


@login_required
@require_http_methods(["POST"])
def htmx_medical_image_upload(request, record_id):
    """Upload medical image and return updated image list"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        from bookings.models import MedicalImage
        
        record = MedicalRecord.objects.get(id=record_id)
        
        # Handle file upload
        image_file = request.FILES.get('image')
        if not image_file:
            return HttpResponse(
                '<div class="alert alert-danger">No image file provided</div>',
                status=400
            )
        
        # Create medical image
        medical_image = MedicalImage.objects.create(
            medical_record=record,
            image=image_file,
            title=request.POST.get('title', 'Medical Image'),
            description=request.POST.get('description', ''),
            image_type=request.POST.get('image_type', 'clinical'),
            uploaded_by=request.user
        )
        
        # Return updated image list
        return htmx_medical_images(request, record_id)
        
    except MedicalRecord.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Medical record not found</div>',
            status=404
        )
    except Exception as e:
        import traceback
        error_msg = f'<div class="alert alert-danger">Error uploading image: {str(e)}<br><pre>{traceback.format_exc()}</pre></div>'
        return HttpResponse(error_msg, status=500)


@login_required
@require_http_methods(["DELETE"])
def htmx_medical_image_delete(request, image_id):
    """Delete medical image and return updated list"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        from bookings.models import MedicalImage
        
        image = MedicalImage.objects.select_related('medical_record').get(id=image_id)
        record_id = image.medical_record.id
        
        # Delete the file
        if image.image:
            image.image.delete()
        
        image.delete()
        
        # Return updated image list
        return htmx_medical_images(request, record_id)
        
    except MedicalImage.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Image not found</div>',
            status=404
        )


@login_required
@require_http_methods(["GET"])
def htmx_inventory_list(request):
    """Return HTML fragment of inventory items with optional search and filters"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    # Get filter parameters
    filter_status = request.GET.get('status', '')
    filter_category = request.GET.get('category', '')
    
    inventory_items = Inventory.objects.all()
    
    # Handle search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        from django.db.models import Q
        inventory_items = inventory_items.filter(
            Q(name__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply status filters
    if filter_status == 'in_stock':
        inventory_items = inventory_items.filter(status='In Stock')
    elif filter_status == 'low_stock':
        inventory_items = inventory_items.filter(status='Low Stock')
    elif filter_status == 'out_of_stock':
        inventory_items = inventory_items.filter(status='Out of Stock')
    
    # Apply category filters
    if filter_category:
        inventory_items = inventory_items.filter(category=filter_category)
    
    inventory_items = inventory_items.order_by('name')
    
    # Calculate summary stats
    in_stock_count = Inventory.objects.filter(status='In Stock').count()
    low_stock_count = Inventory.objects.filter(status='Low Stock').count()
    out_of_stock_count = Inventory.objects.filter(status='Out of Stock').count()
    
    return render(request, 'bookings_v2/partials/inventory_list.html', {
        'inventory_items': inventory_items,
        'in_stock_count': in_stock_count,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'filter_status': filter_status,
        'filter_category': filter_category,
        'today': date.today(),
        'thirty_days_from_now': date.today() + timedelta(days=30)
    })


@login_required
@require_http_methods(["GET"])
def htmx_inventory_adjust(request, item_id):
    """Return HTML form for adjusting inventory stock"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        from django.urls import reverse
        item = Inventory.objects.get(item_id=item_id)
        adjust_url = reverse('bookings_v2:htmx_inventory_adjust_submit', args=[item_id])
        
        html = f'''
        <form hx-post="{adjust_url}" hx-swap="innerHTML" hx-target="#inventoryAdjustModalBody">
            <div class="mb-3">
                <h5>{item.name}</h5>
                <p class="text-muted">Current Stock: <strong>{item.quantity}</strong></p>
            </div>
            <div class="mb-3">
                <label class="form-label">Adjustment Type</label>
                <select class="form-select" name="adjustment_type" required>
                    <option value="add">Add Stock</option>
                    <option value="remove">Remove Stock</option>
                    <option value="set">Set Quantity</option>
                </select>
            </div>
            <div class="mb-3">
                <label class="form-label">Quantity</label>
                <input type="number" class="form-control" name="quantity" min="0" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Notes (Optional)</label>
                <textarea class="form-control" name="notes" rows="2"></textarea>
            </div>
            <div class="d-grid gap-2">
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-save"></i> Save Adjustment
                </button>
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                    Cancel
                </button>
            </div>
        </form>
        '''
        
        return HttpResponse(html)
    except Inventory.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Item not found</div>',
            status=404
        )


@login_required
@require_http_methods(["POST"])
def htmx_inventory_adjust_submit(request, item_id):
    """Process inventory adjustment"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        item = Inventory.objects.get(item_id=item_id)
        adjustment_type = request.POST.get('adjustment_type')
        quantity = int(request.POST.get('quantity', 0))
        notes = request.POST.get('notes', '')
        
        # Store old quantity for transaction record
        old_quantity = item.quantity
        
        if adjustment_type == 'add':
            item.quantity += quantity
        elif adjustment_type == 'remove':
            item.quantity = max(0, item.quantity - quantity)
        elif adjustment_type == 'set':
            item.quantity = quantity
        
        # Save the item (status is auto-calculated in save method)
        item.save()
        
        # Create stock transaction record
        try:
            StockTransaction.objects.create(
                inventory_item=item,
                transaction_type='Stock In' if adjustment_type == 'add' else 'Stock Out',
                quantity=quantity,
                performed_by=request.user,
                notes=notes or f'{adjustment_type.capitalize()} stock adjustment'
            )
        except Exception as e:
            # If StockTransaction fails, continue anyway
            pass
        
        return HttpResponse(
            f'''
            <div class="alert alert-success">
                <i class="fas fa-check-circle"></i> Stock adjusted successfully!
                <br>Previous: <strong>{old_quantity}</strong> → New: <strong>{item.quantity}</strong>
            </div>
            <script>
                setTimeout(() => {{
                    const modal = bootstrap.Modal.getInstance(document.getElementById('inventoryAdjustModal'));
                    if (modal) modal.hide();
                    // Refresh inventory list
                    htmx.trigger('#inventoryModalBody', 'inventoryUpdated');
                }}, 1500);
            </script>
            '''
        )
    except (Inventory.DoesNotExist, ValueError) as e:
        import traceback
        return HttpResponse(
            f'''<div class="alert alert-danger">
                <strong>Error:</strong> {str(e)}
                <br><small>{traceback.format_exc()}</small>
            </div>''',
            status=400
        )


# ========================================
# STOCK TRANSACTION HISTORY
# ========================================

@login_required
@require_http_methods(["GET"])
def htmx_stock_transactions_list(request):
    """HTMX endpoint to list all stock transactions with filtering"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    # Get filter parameters
    transaction_type = request.GET.get('transaction_type', '')
    item_id = request.GET.get('item_id', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset
    transactions = StockTransaction.objects.select_related('inventory_item', 'performed_by').all()
    
    # Apply filters
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if item_id:
        transactions = transactions.filter(inventory_item__item_id=item_id)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            transactions = transactions.filter(transaction_date__date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            transactions = transactions.filter(transaction_date__date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Calculate summary stats
    total_count = transactions.count()
    stock_in_count = transactions.filter(transaction_type='Stock In').count()
    stock_out_count = transactions.filter(transaction_type='Stock Out').count()
    today_count = transactions.filter(transaction_date__date=date.today()).count()
    
    # Get all inventory items for filter dropdown
    inventory_items = Inventory.objects.all().order_by('name')
    
    context = {
        'transactions': transactions[:100],  # Limit to 100 most recent
        'total_count': total_count,
        'stock_in_count': stock_in_count,
        'stock_out_count': stock_out_count,
        'today_count': today_count,
        'inventory_items': inventory_items,
        'filter_type': transaction_type,
        'filter_item_id': item_id,
        'filter_date_from': date_from,
        'filter_date_to': date_to,
    }
    
    # If this is an HTMX request targeting just the table body, return only that
    if request.headers.get('HX-Target') == 'transactionsTableBody':
        return render(request, 'bookings_v2/partials/stock_transactions_table_body.html', context)
    
    return render(request, 'bookings_v2/partials/stock_transactions_list.html', context)


# ========================================
# POINT OF SALE (POS) SYSTEM
# ========================================

@login_required
@require_http_methods(["GET"])
def htmx_pos_interface(request):
    """POS Interface - Main sales screen"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    # Get or create pending sale for current user
    current_sale, created = POSSale.objects.get_or_create(
        created_by=request.user,
        status='Pending',
        defaults={'customer_name': 'Walk-in Customer'}
    )
    
    # Get available products (in stock only)
    products = Inventory.objects.filter(quantity__gt=0).order_by('name')
    
    # Get all patients for patient selection
    patients = Patient.objects.select_related('user').all()
    
    context = {
        'products': products,
        'current_sale': current_sale,
        'cart_items': current_sale.items.all(),
        'patients': patients,
    }
    
    return render(request, 'bookings_v2/partials/pos_interface.html', context)


@login_required
@require_http_methods(["GET"])
def htmx_pos_product_search(request):
    """Search/filter products for POS"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    
    # Base queryset - only in-stock items
    products = Inventory.objects.filter(quantity__gt=0)
    
    # Apply filters
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )
    
    if category:
        products = products.filter(category=category)
    
    products = products.order_by('name')
    
    context = {
        'products': products,
        'filter_category': category,
    }
    
    return render(request, 'bookings_v2/partials/pos_product_grid.html', context)


@login_required
@require_http_methods(["POST"])
def htmx_pos_add_to_cart(request, item_id):
    """Add product to cart"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        inventory_item = Inventory.objects.get(item_id=item_id)
        
        # Check stock
        if inventory_item.quantity <= 0:
            return HttpResponse(
                '<div class="alert alert-danger">Product out of stock</div>',
                status=400
            )
        
        # Get or create current sale
        current_sale, created = POSSale.objects.get_or_create(
            created_by=request.user,
            status='Pending',
            defaults={'customer_name': 'Walk-in Customer'}
        )
        
        # Check if item already in cart
        cart_item, created = POSSaleItem.objects.get_or_create(
            sale=current_sale,
            inventory_item=inventory_item,
            defaults={
                'quantity': 1,
                'unit_price': inventory_item.price
            }
        )
        
        if not created:
            # Item exists, increase quantity if stock allows
            if cart_item.quantity < inventory_item.quantity:
                cart_item.quantity += 1
                cart_item.save()
        
        # Get all patients for dropdown
        patients = Patient.objects.select_related('user').all()
        
        context = {
            'current_sale': current_sale,
            'cart_items': current_sale.items.all(),
            'patients': patients,
        }
        
        return render(request, 'bookings_v2/partials/pos_cart.html', context)
        
    except Inventory.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Product not found</div>',
            status=404
        )


@login_required
@require_http_methods(["POST"])
def htmx_pos_remove_from_cart(request, item_id):
    """Remove item from cart"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        cart_item = POSSaleItem.objects.get(id=item_id)
        current_sale = cart_item.sale
        cart_item.delete()
        
        patients = Patient.objects.select_related('user').all()
        
        context = {
            'current_sale': current_sale,
            'cart_items': current_sale.items.all(),
            'patients': patients,
        }
        
        return render(request, 'bookings_v2/partials/pos_cart.html', context)
        
    except POSSaleItem.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Item not found</div>', status=404)


@login_required
@require_http_methods(["POST"])
def htmx_pos_update_quantity(request, item_id):
    """Update cart item quantity"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        cart_item = POSSaleItem.objects.get(id=item_id)
        action = request.GET.get('action', 'increase')
        
        if action == 'increase':
            if cart_item.quantity < cart_item.inventory_item.quantity:
                cart_item.quantity += 1
                cart_item.save()
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
        
        current_sale = cart_item.sale
        patients = Patient.objects.select_related('user').all()
        
        context = {
            'current_sale': current_sale,
            'cart_items': current_sale.items.all(),
            'patients': patients,
        }
        
        return render(request, 'bookings_v2/partials/pos_cart.html', context)
        
    except POSSaleItem.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Item not found</div>', status=404)


@login_required
@require_http_methods(["POST"])
def htmx_pos_update_discount(request, sale_id):
    """Update sale discount"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        current_sale = POSSale.objects.get(id=sale_id, status='Pending')
        discount_percent = float(request.POST.get('discount_percent', 0))
        
        # Validate discount
        if 0 <= discount_percent <= 100:
            current_sale.discount_percent = discount_percent
            current_sale.save()
        
        patients = Patient.objects.select_related('user').all()
        
        context = {
            'current_sale': current_sale,
            'cart_items': current_sale.items.all(),
            'patients': patients,
        }
        
        return render(request, 'bookings_v2/partials/pos_cart.html', context)
        
    except POSSale.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Sale not found</div>', status=404)


@login_required
@require_http_methods(["POST"])
def htmx_pos_complete_sale(request, sale_id):
    """Complete the sale and generate receipt"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        current_sale = POSSale.objects.get(id=sale_id, status='Pending')
        
        # Validate cart not empty
        if not current_sale.items.exists():
            return HttpResponse(
                '<div class="alert alert-danger">Cannot complete sale with empty cart</div>',
                status=400
            )
        
        # Update customer info
        sale_type = request.POST.get('sale_type', 'Walk-in')
        current_sale.sale_type = sale_type
        
        if sale_type == 'Patient':
            patient_id = request.POST.get('patient_id')
            if patient_id:
                try:
                    patient = Patient.objects.get(patient_id=patient_id)
                    current_sale.patient = patient
                    current_sale.customer_name = patient.user.get_full_name()
                except Patient.DoesNotExist:
                    current_sale.customer_name = request.POST.get('customer_name', 'Walk-in Customer')
        else:
            customer_name = request.POST.get('customer_name', '').strip()
            if not customer_name:
                return HttpResponse(
                    '<div class="alert alert-danger">Customer name is required</div>',
                    status=400
                )
            current_sale.customer_name = customer_name
        
        # Update payment info
        current_sale.payment_method = request.POST.get('payment_method', 'Cash')
        
        try:
            from decimal import Decimal
            amount_received = request.POST.get('amount_received', '')
            if amount_received:
                current_sale.amount_received = Decimal(str(amount_received))
            else:
                current_sale.amount_received = current_sale.total_amount
        except (ValueError, TypeError):
            current_sale.amount_received = current_sale.total_amount
        
        current_sale.reference_number = request.POST.get('reference_number', '')
        
        # Save first to update all calculations
        current_sale.save()
        
        # Now mark as completed and save again - this will trigger inventory deduction
        current_sale.status = 'Completed'
        current_sale.save()
        
        # Deduct inventory manually for each item
        for item in current_sale.items.all():
            # Deduct from inventory
            if item.inventory_item.quantity >= item.quantity:
                item.inventory_item.quantity -= item.quantity
                item.inventory_item.save()
                
                # Create stock transaction
                try:
                    StockTransaction.objects.create(
                        inventory_item=item.inventory_item,
                        transaction_type='Stock Out',
                        quantity=item.quantity,
                        performed_by=request.user,
                        notes=f"POS Sale - Receipt #{current_sale.receipt_number}"
                    )
                except Exception:
                    # Silently continue if stock transaction creation fails
                    pass
        
        # Generate receipt HTML
        receipt_html = f'''
        <div class="text-center">
            <div class="alert alert-success">
                <i class="fas fa-check-circle fa-3x mb-3"></i>
                <h4>Sale Completed!</h4>
                <p class="mb-0">Receipt: <strong>#{current_sale.receipt_number}</strong></p>
            </div>
            
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">Receipt #{current_sale.receipt_number}</h5>
                    <hr>
                    <p class="mb-1"><strong>Customer:</strong> {current_sale.customer_name}</p>
                    <p class="mb-1"><strong>Date:</strong> {current_sale.sale_date.strftime("%B %d, %Y %I:%M %p")}</p>
                    <p class="mb-3"><strong>Payment:</strong> {current_sale.payment_method}</p>
                    
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Item</th>
                                <th class="text-end">Qty</th>
                                <th class="text-end">Price</th>
                                <th class="text-end">Total</th>
                            </tr>
                        </thead>
                        <tbody>
        '''
        
        for item in current_sale.items.all():
            receipt_html += f'''
                            <tr>
                                <td>{item.inventory_item.name}</td>
                                <td class="text-end">{item.quantity}</td>
                                <td class="text-end">₱{item.unit_price}</td>
                                <td class="text-end">₱{item.line_total}</td>
                            </tr>
            '''
        
        receipt_html += f'''
                        </tbody>
                    </table>
                    
                    <hr>
                    <div class="d-flex justify-content-between mb-1">
                        <span>Subtotal:</span>
                        <strong>₱{current_sale.subtotal}</strong>
                    </div>
        '''
        
        if current_sale.discount_amount > 0:
            receipt_html += f'''
                    <div class="d-flex justify-content-between mb-1 text-success">
                        <span>Discount ({current_sale.discount_percent}%):</span>
                        <strong>-₱{current_sale.discount_amount}</strong>
                    </div>
            '''
        
        receipt_html += f'''
                    <div class="d-flex justify-content-between mb-2">
                        <h5>Total:</h5>
                        <h5 class="text-primary">₱{current_sale.total_amount}</h5>
                    </div>
                    
                    <div class="d-flex justify-content-between mb-1">
                        <span>Amount Received:</span>
                        <strong>₱{current_sale.amount_received}</strong>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span>Change:</span>
                        <strong>₱{current_sale.change_amount}</strong>
                    </div>
                </div>
            </div>
            
            <div class="d-grid gap-2">
                <button 
                    class="btn btn-primary"
                    onclick="window.print()"
                >
                    <i class="fas fa-print"></i> Print Receipt
                </button>
                <button 
                    class="btn btn-success"
                    hx-get="/admin/htmx/pos/"
                    hx-target="#posModalBody"
                    hx-swap="innerHTML"
                >
                    <i class="fas fa-plus"></i> New Sale
                </button>
                <button 
                    class="btn btn-outline-secondary"
                    hx-get="/admin/htmx/pos-sales/"
                    hx-target="#posModalBody"
                    hx-swap="innerHTML"
                >
                    <i class="fas fa-list"></i> View All Sales
                </button>
            </div>
        </div>
        '''
        
        return HttpResponse(receipt_html)
        
    except (POSSale.DoesNotExist, Patient.DoesNotExist, ValueError) as e:
        import traceback
        return HttpResponse(
            f'''<div class="alert alert-danger">
                <strong>Error:</strong> {str(e)}
                <br><small>{traceback.format_exc()}</small>
            </div>''',
            status=400
        )


@login_required
@require_http_methods(["POST"])
def htmx_pos_cancel_sale(request, sale_id):
    """Cancel current sale"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        current_sale = POSSale.objects.get(id=sale_id, status='Pending')
        current_sale.status = 'Cancelled'
        current_sale.save()
        
        # Create new pending sale
        new_sale = POSSale.objects.create(
            created_by=request.user,
            customer_name='Walk-in Customer',
            status='Pending'
        )
        
        patients = Patient.objects.select_related('user').all()
        
        context = {
            'current_sale': new_sale,
            'cart_items': [],
            'patients': patients,
        }
        
        return render(request, 'bookings_v2/partials/pos_cart.html', context)
        
    except POSSale.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Sale not found</div>', status=404)


@login_required
@require_http_methods(["GET"])
def htmx_pos_sales_list(request):
    """List all POS sales with filtering"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    # Get filter parameters
    status = request.GET.get('status', '')
    payment_method = request.GET.get('payment_method', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset - exclude pending sales
    sales = POSSale.objects.exclude(status='Pending').select_related('patient__user', 'created_by').order_by('-sale_date')
    
    # Apply filters
    if status:
        sales = sales.filter(status=status)
    
    if payment_method:
        sales = sales.filter(payment_method=payment_method)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            sales = sales.filter(sale_date__date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            sales = sales.filter(sale_date__date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Calculate summary stats
    today = date.today()
    today_sales = POSSale.objects.filter(status='Completed', sale_date__date=today)
    today_count = today_sales.count()
    today_revenue = today_sales.aggregate(total=Sum('total_amount'))['total'] or 0
    
    month_start = today.replace(day=1)
    month_sales = POSSale.objects.filter(status='Completed', sale_date__date__gte=month_start)
    month_count = month_sales.count()
    month_revenue = month_sales.aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'sales': sales[:100],  # Limit to 100 most recent
        'total_count': sales.count(),
        'today_count': today_count,
        'today_revenue': today_revenue,
        'month_count': month_count,
        'month_revenue': month_revenue,
        'filter_status': status,
        'filter_payment': payment_method,
        'filter_date_from': date_from,
        'filter_date_to': date_to,
    }
    
    # If HTMX targeting just table body
    if request.headers.get('HX-Target') == 'salesTableBody':
        return render(request, 'bookings_v2/partials/pos_sales_table_body.html', context)
    
    return render(request, 'bookings_v2/partials/pos_sales_list.html', context)


@login_required
@require_http_methods(["GET"])
def htmx_pos_sale_detail(request, sale_id):
    """View detailed receipt for a sale"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        sale = POSSale.objects.get(id=sale_id)
        
        receipt_html = f'''
        <div class="text-center">
            <div class="card mb-3">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">Receipt #{sale.receipt_number}</h5>
                </div>
                <div class="card-body text-start">
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <p class="mb-1"><strong>Customer:</strong> {sale.customer_name}</p>
                            <p class="mb-1"><strong>Type:</strong> {sale.sale_type}</p>
                        </div>
                        <div class="col-md-6">
                            <p class="mb-1"><strong>Date:</strong> {sale.sale_date.strftime("%B %d, %Y")}</p>
                            <p class="mb-1"><strong>Time:</strong> {sale.sale_date.strftime("%I:%M %p")}</p>
                        </div>
                    </div>
                    
                    <p class="mb-2"><strong>Payment Method:</strong> {sale.payment_method}</p>
                    {f'<p class="mb-2"><strong>Reference:</strong> {sale.reference_number}</p>' if sale.reference_number else ''}
                    
                    <hr>
                    
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Item</th>
                                <th class="text-center">Qty</th>
                                <th class="text-end">Price</th>
                                <th class="text-end">Total</th>
                            </tr>
                        </thead>
                        <tbody>
        '''
        
        for item in sale.items.all():
            receipt_html += f'''
                            <tr>
                                <td>{item.inventory_item.name}</td>
                                <td class="text-center">{item.quantity}</td>
                                <td class="text-end">₱{item.unit_price}</td>
                                <td class="text-end">₱{item.line_total}</td>
                            </tr>
            '''
        
        receipt_html += f'''
                        </tbody>
                    </table>
                    
                    <hr>
                    
                    <div class="row">
                        <div class="col-6 text-end"><strong>Subtotal:</strong></div>
                        <div class="col-6 text-end">₱{sale.subtotal}</div>
                    </div>
        '''
        
        if sale.discount_amount > 0:
            receipt_html += f'''
                    <div class="row text-success">
                        <div class="col-6 text-end"><strong>Discount ({sale.discount_percent}%):</strong></div>
                        <div class="col-6 text-end">-₱{sale.discount_amount}</div>
                    </div>
            '''
        
        receipt_html += f'''
                    <hr>
                    <div class="row">
                        <div class="col-6 text-end"><h5>Total:</h5></div>
                        <div class="col-6 text-end"><h5 class="text-primary">₱{sale.total_amount}</h5></div>
                    </div>
                    
                    <div class="row mt-2">
                        <div class="col-6 text-end">Amount Received:</div>
                        <div class="col-6 text-end">₱{sale.amount_received}</div>
                    </div>
                    <div class="row">
                        <div class="col-6 text-end">Change:</div>
                        <div class="col-6 text-end">₱{sale.change_amount}</div>
                    </div>
                    
                    <hr>
                    
                    <p class="text-center mb-2">
                        <span class="badge bg-{sale.get_status_badge_class()}">{sale.status}</span>
                    </p>
                    <p class="text-muted small text-center mb-0">
                        Served by: {sale.created_by.get_full_name() if sale.created_by else 'Unknown'}
                    </p>
                </div>
            </div>
            
            <div class="d-grid gap-2">
                <button 
                    class="btn btn-primary"
                    onclick="window.print()"
                >
                    <i class="fas fa-print"></i> Print Receipt
                </button>
                <button 
                    class="btn btn-outline-secondary"
                    hx-get="/admin/htmx/pos-sales/"
                    hx-target="#posModalBody"
                    hx-swap="innerHTML"
                >
                    <i class="fas fa-arrow-left"></i> Back to Sales List
                </button>
            </div>
        </div>
        '''
        
        return HttpResponse(receipt_html)
        
    except POSSale.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Sale not found</div>', status=404)


# ========================================
# PENDING BOOKINGS MANAGEMENT
# ========================================

@login_required
@require_http_methods(["GET"])
def htmx_pending_bookings(request):
    """HTMX endpoint to list all pending bookings"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    pending_bookings = Booking.objects.filter(status='Pending').select_related('service').order_by('date', 'time')
    
    return render(request, 'bookings_v2/htmx_partials/pending_bookings.html', {
        'bookings': pending_bookings
    })


@login_required
@require_http_methods(["POST"])
def htmx_accept_booking(request, booking_id):
    """Accept a pending booking and create patient records"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        booking = Booking.objects.get(id=booking_id, status='Pending')
        
        # Update booking status to Confirmed
        booking.status = 'Confirmed'
        booking.save()  # This triggers signals that create Patient, MedicalRecord, Billing
        
        # Return success message (row will be removed)
        return HttpResponse(
            f'''<tr id="booking-row-{booking_id}">
                <td colspan="7" class="text-center py-3">
                    <div class="alert alert-success mb-0">
                        <i class="fas fa-check-circle"></i> 
                        Booking for <strong>{booking.patient_name}</strong> has been accepted! 
                        Patient records created automatically.
                    </div>
                </td>
            </tr>
            <script>
                setTimeout(() => {{
                    const row = document.getElementById('booking-row-{booking_id}');
                    const notesRow = document.getElementById('notes-{booking_id}');
                    if (row) {{
                        row.style.transition = 'opacity 0.3s ease';
                        row.style.opacity = '0';
                        if (notesRow) {{
                            notesRow.style.transition = 'opacity 0.3s ease';
                            notesRow.style.opacity = '0';
                        }}
                        setTimeout(() => {{
                            row.remove();
                            if (notesRow) notesRow.remove();
                            // Optionally refresh the list
                            const refreshBtn = document.querySelector('#pendingBookingsContainer .btn-outline-primary');
                            if (refreshBtn) refreshBtn.click();
                        }}, 300);
                    }}
                }}, 2000);
            </script>'''
        )
        
    except Booking.DoesNotExist:
        return HttpResponse(
            '<tr><td colspan="7"><div class="alert alert-danger">Booking not found or already processed</div></td></tr>',
            status=404
        )
    except Exception as e:
        return HttpResponse(
            f'<tr><td colspan="7"><div class="alert alert-danger">Error: {str(e)}</div></td></tr>',
            status=500
        )


@login_required
@require_http_methods(["POST"])
def htmx_decline_booking(request, booking_id):
    """Decline a pending booking"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        booking = Booking.objects.get(id=booking_id, status='Pending')
        patient_name = booking.patient_name
        
        # Update status to Cancelled (or delete if preferred)
        booking.status = 'Cancelled'
        booking.save()
        
        # Return success message (row will be removed)
        return HttpResponse(
            f'''<tr id="booking-row-{booking_id}">
                <td colspan="7" class="text-center py-3">
                    <div class="alert alert-warning mb-0">
                        <i class="fas fa-times-circle"></i> 
                        Booking for <strong>{patient_name}</strong> has been declined.
                    </div>
                </td>
            </tr>
            <script>
                setTimeout(() => {{
                    const row = document.getElementById('booking-row-{booking_id}');
                    const notesRow = document.getElementById('notes-{booking_id}');
                    if (row) {{
                        row.style.transition = 'opacity 0.3s ease';
                        row.style.opacity = '0';
                        if (notesRow) {{
                            notesRow.style.transition = 'opacity 0.3s ease';
                            notesRow.style.opacity = '0';
                        }}
                        setTimeout(() => {{
                            row.remove();
                            if (notesRow) notesRow.remove();
                            // Optionally refresh the list
                            const refreshBtn = document.querySelector('#pendingBookingsContainer .btn-outline-primary');
                            if (refreshBtn) refreshBtn.click();
                        }}, 300);
                    }}
                }}, 2000);
            </script>'''
        )
        
    except Booking.DoesNotExist:
        return HttpResponse(
            '<tr><td colspan="7"><div class="alert alert-danger">Booking not found</div></td></tr>',
            status=404
        )
    except Exception as e:
        return HttpResponse(
            f'<tr><td colspan="7"><div class="alert alert-danger">Error: {str(e)}</div></td></tr>',
            status=500
        )


# ========================================
# USER MANAGEMENT VIEWS
# ========================================

@login_required
@require_http_methods(["GET"])
def htmx_users_list(request):
    """HTMX endpoint to list all users"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    from django.contrib.auth.models import User
    
    # Get filter parameters
    role = request.GET.get('role', 'all')
    search = request.GET.get('search', '')
    
    # Base queryset
    users = User.objects.all().order_by('-date_joined')
    
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
@require_http_methods(["GET"])
def htmx_user_detail(request, user_id):
    """HTMX endpoint to show user details"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    from django.contrib.auth.models import User
    
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
@require_http_methods(["GET"])
def htmx_user_edit(request, user_id):
    """HTMX endpoint to show user edit form"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    from django.contrib.auth.models import User
    
    try:
        user = User.objects.get(id=user_id)
        
        # Only superusers can edit staff/superuser accounts
        if not request.user.is_superuser:
            if user.is_staff or user.is_superuser:
                return HttpResponse('<div class="alert alert-danger">Only superusers can edit staff accounts</div>', status=403)
        
        # Get user's group names
        user_groups = user.groups.values_list('name', flat=True)
        
        return render(request, 'bookings_v2/htmx_partials/user_form.html', {
            'user': user,
            'user_groups': list(user_groups)
        })
    except User.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">User not found</div>', status=404)


@login_required
@require_http_methods(["GET"])
def htmx_user_create_form(request):
    """HTMX endpoint to show user creation form"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    return render(request, 'bookings_v2/htmx_partials/user_form.html')


@login_required
@require_http_methods(["POST"])
def htmx_user_create(request):
    """HTMX endpoint to create a new user"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    from django.contrib.auth.models import User, Group
    
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
        
        # Return updated user list
        users = User.objects.all().order_by('-date_joined')
        if not request.user.is_superuser:
            users = users.filter(Q(is_staff=False) | Q(id=request.user.id))
        
        response = render(request, 'bookings_v2/htmx_partials/users_list.html', {'users': users})
        response['HX-Trigger'] = 'userCreated'
        messages.success(request, f'User "{username}" created successfully!')
        return response
        
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


@login_required
@require_http_methods(["POST"])
def htmx_user_update(request, user_id):
    """HTMX endpoint to update user"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    from django.contrib.auth.models import User, Group
    
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
        
        # Return updated user list
        users = User.objects.all().order_by('-date_joined')
        if not request.user.is_superuser:
            users = users.filter(Q(is_staff=False) | Q(id=request.user.id))
        
        response = render(request, 'bookings_v2/htmx_partials/users_list.html', {'users': users})
        response['HX-Trigger'] = 'userUpdated'
        messages.success(request, f'User "{user.username}" updated successfully!')
        return response
        
    except User.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">User not found</div>', status=404)
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


@login_required
@require_http_methods(["DELETE"])
def htmx_user_delete(request, user_id):
    """HTMX endpoint to deactivate user"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    from django.contrib.auth.models import User
    
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
        
        messages.success(request, f'User "{user.username}" has been deactivated')
        return HttpResponse('')  # Return empty for swap delete
        
    except User.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">User not found</div>', status=404)
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


# ========================================
# APPOINTMENT CRUD ENDPOINTS
# ========================================

@login_required
@require_http_methods(["GET"])
def htmx_appointment_create_form(request):
    """Return HTML form for creating a new appointment"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    services = Service.objects.all()
    return render(request, 'bookings_v2/htmx_partials/appointment_form.html', {
        'today': date.today().isoformat(),
        'services': services
    })


@login_required
@require_http_methods(["POST"])
def htmx_appointment_create(request):
    """Create a new appointment"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        service_id = request.POST.get('service')
        service = Service.objects.get(id=service_id)
        
        appointment = Booking.objects.create(
            patient_name=request.POST.get('name'),
            patient_email=request.POST.get('email'),
            patient_phone=request.POST.get('phone'),
            date=request.POST.get('date'),
            time=request.POST.get('time'),
            service=service,
            status=request.POST.get('status', 'Pending'),
            consultation_status='Not Yet'
        )
        
        messages.success(request, f'Appointment created for {appointment.patient_name}')
        
        # Return updated appointments list
        appointments = Booking.objects.select_related('service').order_by('-date', '-time')
        return render(request, 'bookings_v2/partials/appointments_list.html', {
            'appointments': appointments
        })
        
    except Service.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Service not found</div>', status=400)
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


@login_required
@require_http_methods(["GET"])
def htmx_appointment_edit_form(request, appointment_id):
    """Return HTML form for editing an appointment"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        appointment = Booking.objects.select_related('service').get(id=appointment_id)
        services = Service.objects.all()
        return render(request, 'bookings_v2/htmx_partials/appointment_form.html', {
            'appointment': appointment,
            'services': services,
            'today': date.today().isoformat()
        })
    except Booking.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Appointment not found</div>', status=404)


@login_required
@require_http_methods(["POST"])
def htmx_appointment_update(request, appointment_id):
    """Update an existing appointment"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        appointment = Booking.objects.get(id=appointment_id)
        
        # Update service if provided
        service_id = request.POST.get('service')
        if service_id:
            appointment.service = Service.objects.get(id=service_id)
        
        appointment.patient_name = request.POST.get('name')
        appointment.patient_email = request.POST.get('email')
        appointment.patient_phone = request.POST.get('phone')
        appointment.date = request.POST.get('date')
        appointment.time = request.POST.get('time')
        appointment.status = request.POST.get('status')
        appointment.consultation_status = request.POST.get('consultation_status', appointment.consultation_status)
        appointment.save()
        
        messages.success(request, f'Appointment updated for {appointment.patient_name}')
        
        # Return updated appointments list
        appointments = Booking.objects.select_related('service').order_by('-date', '-time')
        return render(request, 'bookings_v2/partials/appointments_list.html', {
            'appointments': appointments
        })
        
    except Booking.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Appointment not found</div>', status=404)
    except Service.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Service not found</div>', status=400)
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


# ========================================
# PATIENT CRUD ENDPOINTS  
# ========================================

@login_required
@require_http_methods(["GET"])
def htmx_patient_create_form(request):
    """Return HTML form for creating a new patient"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    return render(request, 'bookings_v2/htmx_partials/patient_form.html', {
        'today': date.today().isoformat()
    })


@login_required
@require_http_methods(["POST"])
def htmx_patient_create(request):
    """Create a new patient with user account"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        from django.contrib.auth.models import User
        
        # Check if username already exists
        username = request.POST.get('username')
        if User.objects.filter(username=username).exists():
            return HttpResponse('<div class="alert alert-danger">Username already exists</div>', status=400)
        
        # Check if email already exists
        email = request.POST.get('email')
        if User.objects.filter(email=email).exists():
            return HttpResponse('<div class="alert alert-danger">Email already exists</div>', status=400)
        
        # Check password match
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 != password2:
            return HttpResponse('<div class="alert alert-danger">Passwords do not match</div>', status=400)
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name')
        )
        
        # Create patient profile
        patient = Patient.objects.create(
            user=user,
            date_of_birth=request.POST.get('date_of_birth'),
            gender=request.POST.get('gender'),
            blood_type=request.POST.get('blood_type', 'UK'),
            phone=request.POST.get('phone', ''),
            address=request.POST.get('address', ''),
            emergency_contact_name=request.POST.get('emergency_contact_name', ''),
            emergency_contact_phone=request.POST.get('emergency_contact_phone', ''),
            allergies=request.POST.get('allergies', ''),
            current_medications=request.POST.get('current_medications', ''),
            medical_history=request.POST.get('medical_history', ''),
            created_by=request.user
        )
        
        messages.success(request, f'Patient {user.get_full_name()} created successfully')
        
        # Return updated patients list
        patients = Patient.objects.select_related('user').prefetch_related('medical_records').all()[:20]
        return render(request, 'bookings_v2/partials/patients_list.html', {
            'patients': patients
        })
        
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


@login_required
@require_http_methods(["GET"])
def htmx_patient_edit_form(request, patient_id):
    """Return HTML form for editing a patient"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        patient = Patient.objects.select_related('user').get(id=patient_id)
        return render(request, 'bookings_v2/htmx_partials/patient_form.html', {
            'patient': patient,
            'today': date.today().isoformat()
        })
    except Patient.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Patient not found</div>', status=404)


@login_required
@require_http_methods(["POST"])
def htmx_patient_update(request, patient_id):
    """Update an existing patient"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        patient = Patient.objects.select_related('user').get(id=patient_id)
        user = patient.user
        
        # Update user info
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        
        # Update patient profile
        patient.date_of_birth = request.POST.get('date_of_birth')
        patient.gender = request.POST.get('gender')
        patient.blood_type = request.POST.get('blood_type', 'UK')
        patient.phone = request.POST.get('phone', '')
        patient.address = request.POST.get('address', '')
        patient.emergency_contact_name = request.POST.get('emergency_contact_name', '')
        patient.emergency_contact_phone = request.POST.get('emergency_contact_phone', '')
        patient.allergies = request.POST.get('allergies', '')
        patient.current_medications = request.POST.get('current_medications', '')
        patient.medical_history = request.POST.get('medical_history', '')
        patient.save()
        
        messages.success(request, f'Patient {user.get_full_name()} updated successfully')
        
        # Return updated patients list
        patients = Patient.objects.select_related('user').prefetch_related('medical_records').all()[:20]
        return render(request, 'bookings_v2/partials/patients_list.html', {
            'patients': patients
        })
        
    except Patient.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Patient not found</div>', status=404)
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


# ========================================
# PAYMENT CRUD ENDPOINTS
# ========================================

@login_required
@require_http_methods(["GET"])
def htmx_payment_create_form(request):
    """Return HTML form for recording a new payment"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    # Get unpaid billings
    unpaid_billings = Billing.objects.filter(
        Q(is_paid=False) | Q(balance__gt=0)
    ).select_related('booking').order_by('-issued_date')[:50]
    
    return render(request, 'bookings_v2/htmx_partials/payment_form.html', {
        'unpaid_billings': unpaid_billings
    })


@login_required
@require_http_methods(["POST"])
def htmx_payment_create(request):
    """Record a new payment"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        from .models import Payment
        
        billing_id = request.POST.get('billing_id')
        billing = Billing.objects.get(id=billing_id)
        
        # Create payment
        payment = Payment.objects.create(
            billing=billing,
            amount_paid=request.POST.get('amount_paid'),
            payment_method=request.POST.get('payment_method'),
            reference_number=request.POST.get('reference_number', ''),
            notes=request.POST.get('notes', ''),
            recorded_by=request.user
        )
        
        messages.success(request, f'Payment of ₱{payment.amount_paid} recorded successfully')
        
        # Return updated billings list
        billings = Billing.objects.select_related('booking').order_by('-issued_date')[:50]
        return render(request, 'bookings_v2/partials/billings_list.html', {
            'billings': billings
        })
        
    except Billing.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Billing record not found</div>', status=404)
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


# ========================================
# INVENTORY CRUD ENDPOINTS
# ========================================

@login_required
@require_http_methods(["GET"])
def htmx_inventory_create_form(request):
    """Return HTML form for creating a new inventory item"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    return render(request, 'bookings_v2/htmx_partials/inventory_form.html', {
        'today': date.today().isoformat()
    })


@login_required
@require_http_methods(["POST"])
def htmx_inventory_create(request):
    """Create a new inventory item"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', '').strip()
        price = request.POST.get('price', '0')
        quantity = request.POST.get('quantity', '0')
        stock = request.POST.get('stock', '0')
        expiry_date = request.POST.get('expiry_date', '').strip()
        
        # Validate required fields
        if not name or not description or not category:
            return HttpResponse('<div class="alert alert-danger">Name, description, and category are required</div>', status=400)
        
        # Convert numeric fields
        try:
            price = float(price)
            quantity = int(quantity)
            stock = int(stock)
        except ValueError:
            return HttpResponse('<div class="alert alert-danger">Invalid numeric values for price, quantity, or stock</div>', status=400)
        
        # Handle expiry date
        if expiry_date:
            expiry_date_obj = expiry_date
        else:
            expiry_date_obj = None
            
        # Create item
        item = Inventory.objects.create(
            name=name,
            description=description,
            category=category,
            price=price,
            quantity=quantity,
            stock=stock,
            expiry_date=expiry_date_obj
        )
        
        # Return updated inventory list with all stats
        inventory_items = Inventory.objects.all().order_by('name')
        in_stock_count = Inventory.objects.filter(status='In Stock').count()
        low_stock_count = Inventory.objects.filter(status='Low Stock').count()
        out_of_stock_count = Inventory.objects.filter(status='Out of Stock').count()
        
        return render(request, 'bookings_v2/partials/inventory_list.html', {
            'inventory_items': inventory_items,
            'in_stock_count': in_stock_count,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'filter_status': '',
            'filter_category': '',
            'today': date.today(),
            'thirty_days_from_now': date.today() + timedelta(days=30)
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return HttpResponse(f'<div class="alert alert-danger">Error creating item: {str(e)}<br><pre>{error_details}</pre></div>', status=400)


@login_required
@require_http_methods(["GET"])
def htmx_inventory_edit_form(request, item_id):
    """Return HTML form for editing an inventory item"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        item = Inventory.objects.get(item_id=item_id)
        return render(request, 'bookings_v2/htmx_partials/inventory_form.html', {
            'item': item,
            'today': date.today().isoformat()
        })
    except Inventory.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Inventory item not found</div>', status=404)


@login_required
@require_http_methods(["POST"])
def htmx_inventory_update(request, item_id):
    """Update an existing inventory item"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        item = Inventory.objects.get(item_id=item_id)
        
        # Get form data
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', '').strip()
        price = request.POST.get('price', '0')
        quantity = request.POST.get('quantity', '0')
        stock = request.POST.get('stock', '0')
        expiry_date = request.POST.get('expiry_date', '').strip()
        
        # Validate required fields
        if not name or not description or not category:
            return HttpResponse('<div class="alert alert-danger">Name, description, and category are required</div>', status=400)
        
        # Convert numeric fields
        try:
            price = float(price)
            quantity = int(quantity)
            stock = int(stock)
        except ValueError:
            return HttpResponse('<div class="alert alert-danger">Invalid numeric values for price, quantity, or stock</div>', status=400)
        
        # Update item
        item.name = name
        item.description = description
        item.category = category
        item.price = price
        item.quantity = quantity
        item.stock = stock
        item.expiry_date = expiry_date if expiry_date else None
        
        item.save()
        
        # Return updated inventory list with all stats
        inventory_items = Inventory.objects.all().order_by('name')
        in_stock_count = Inventory.objects.filter(status='In Stock').count()
        low_stock_count = Inventory.objects.filter(status='Low Stock').count()
        out_of_stock_count = Inventory.objects.filter(status='Out of Stock').count()
        
        return render(request, 'bookings_v2/partials/inventory_list.html', {
            'inventory_items': inventory_items,
            'in_stock_count': in_stock_count,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'filter_status': '',
            'filter_category': '',
            'today': date.today(),
            'thirty_days_from_now': date.today() + timedelta(days=30)
        })
        
    except Inventory.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Inventory item not found</div>', status=404)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return HttpResponse(f'<div class="alert alert-danger">Error updating item: {str(e)}<br><pre>{error_details}</pre></div>', status=400)


@login_required
@require_http_methods(["DELETE", "POST"])
def htmx_inventory_delete(request, item_id):
    """Delete an inventory item"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        item = Inventory.objects.get(item_id=item_id)
        item_name = item.name
        item.delete()
        
        # Return updated inventory list
        inventory_items = Inventory.objects.all().order_by('name')
        in_stock_count = Inventory.objects.filter(status='In Stock').count()
        low_stock_count = Inventory.objects.filter(status='Low Stock').count()
        out_of_stock_count = Inventory.objects.filter(status='Out of Stock').count()
        
        return render(request, 'bookings_v2/partials/inventory_list.html', {
            'inventory_items': inventory_items,
            'in_stock_count': in_stock_count,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'filter_status': '',
            'filter_category': '',
            'today': date.today(),
            'thirty_days_from_now': date.today() + timedelta(days=30)
        })
        
    except Inventory.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Inventory item not found</div>', status=404)
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error deleting item: {str(e)}</div>', status=400)


# ========================================
# SERVICES CRUD ENDPOINTS
# ========================================

@login_required
@require_http_methods(["GET"])
def htmx_services_list(request):
    """Return HTML fragment of all services"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    services = Service.objects.all().order_by('name')
    
    return render(request, 'bookings_v2/partials/services_list.html', {
        'services': services
    })


@login_required
@require_http_methods(["GET"])
def htmx_service_create_form(request):
    """Return HTML form for creating a new service"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    return render(request, 'bookings_v2/htmx_partials/service_form.html')


@login_required
@require_http_methods(["POST"])
def htmx_service_create(request):
    """Create a new service"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        service = Service.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            price=request.POST.get('price'),
            image=request.FILES.get('image')
        )
        
        messages.success(request, f'Service "{service.name}" created successfully')
        
        # Return updated services list
        services = Service.objects.all().order_by('name')
        return render(request, 'bookings_v2/partials/services_list.html', {
            'services': services
        })
        
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


@login_required
@require_http_methods(["GET"])
def htmx_service_edit_form(request, service_id):
    """Return HTML form for editing a service"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        service = Service.objects.get(id=service_id)
        return render(request, 'bookings_v2/htmx_partials/service_form.html', {
            'service': service
        })
    except Service.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Service not found</div>', status=404)


@login_required
@require_http_methods(["POST"])
def htmx_service_update(request, service_id):
    """Update an existing service"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        service = Service.objects.get(id=service_id)
        service.name = request.POST.get('name')
        service.description = request.POST.get('description')
        service.price = request.POST.get('price')
        
        # Update image only if a new one is uploaded
        if request.FILES.get('image'):
            service.image = request.FILES.get('image')
        
        service.save()
        
        messages.success(request, f'Service "{service.name}" updated successfully')
        
        # Return updated services list
        services = Service.objects.all().order_by('name')
        return render(request, 'bookings_v2/partials/services_list.html', {
            'services': services
        })
        
    except Service.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Service not found</div>', status=404)
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


@login_required
@require_http_methods(["DELETE"])
def htmx_service_delete(request, service_id):
    """Delete a service"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
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
        
        messages.success(request, f'Service "{service_name}" deleted successfully')
        
        # Return empty response - HTMX will swap and remove the row
        return HttpResponse('', status=200)
        
    except Service.DoesNotExist:
        return HttpResponse('<tr><td colspan="5" class="text-center text-danger">Service not found</td></tr>', status=404)
    except Exception as e:
        return HttpResponse(f'<tr><td colspan="5" class="text-center text-danger">Error: {str(e)}</td></tr>', status=400)





