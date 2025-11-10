"""
Public-Facing Views
Handles pages accessible to all users (home, about, services, contact, etc.)
Includes HTMX endpoints for booking and contact forms
"""
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from datetime import datetime, date, time as datetime_time
import logging

from ..models import Service, Booking, Calendar, ClinicSettings, Patient
from ..utils.responses import htmx_error, htmx_success
from ..utils.email_utils import send_booking_confirmation_email

logger = logging.getLogger(__name__)


def home_v2(request):
    """Homepage - V2 with Bootstrap/HTMX/Alpine"""
    return render(request, 'bookings_v2/home_v2.html')


def booking_v2(request):
    """Booking page - V2 with Bootstrap/HTMX/Alpine"""
    services = Service.objects.all()
    
    # Check if logged-in user has an existing patient profile
    existing_patient = None
    if request.user.is_authenticated:
        try:
            existing_patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            pass
    
    # Get all blocked dates (including Sundays)
    from datetime import timedelta
    today = date.today()
    end_date = today + timedelta(days=180)  # Next 6 months
    
    # Get blocked dates from database
    blocked_dates_db = Calendar.objects.filter(
        date__gte=today,
        date__lte=end_date,
        event_type='blocked'
    ).order_by('date')
    
    blocked_dates_list = list(blocked_dates_db.values_list('date', flat=True))
    
    # Generate all Sundays in the next 6 months
    sundays = []
    current_date = today
    while current_date <= end_date:
        if current_date.weekday() == 6:  # 6 = Sunday
            sundays.append(current_date)
        current_date += timedelta(days=1)
    
    # Combine blocked dates and Sundays
    all_blocked_dates = set(blocked_dates_list + sundays)
    blocked_dates_json = [d.strftime('%Y-%m-%d') for d in all_blocked_dates]
    
    # Min date is tomorrow
    from datetime import timedelta
    min_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Format blocked dates for display (show first 10)
    blocked_dates_display = []
    for blocked_date_obj in blocked_dates_db[:10]:
        formatted = blocked_date_obj.date.strftime('%b %d')
        if blocked_date_obj.reason:
            formatted += f' ({blocked_date_obj.reason})'
        blocked_dates_display.append(formatted)
    
    # Add "All Sundays" to the display list
    if sundays:
        blocked_dates_display.append('All Sundays')
    
    return render(request, 'bookings_v2/booking_v2.html', {
        'services': services,
        'blocked_dates': blocked_dates_json,
        'blocked_dates_display': blocked_dates_display,
        'minDate': min_date,
        'existing_patient': existing_patient
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


# === HTMX Endpoints for Public Pages ===

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
            '<select class="form-select form-select-lg form-control-professional" name="time" required disabled>'
            '<option value="">Select service and date first...</option>'
            '</select>'
        )
    
    try:
        # Parse the date
        selected_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
        
        # Check if date is in the past
        if selected_date < date.today():
            return HttpResponse(
                '<select class="form-select form-select-lg form-control-professional" name="time" required disabled>'
                '<option value="">Past dates are not available</option>'
                '</select>'
            )
        
        # Check if date is blocked
        if Calendar.is_date_blocked(selected_date):
            return HttpResponse(
                '<select class="form-select form-select-lg form-control-professional" name="time" required disabled>'
                '<option value="">This date is not available (clinic closed)</option>'
                '</select>'
            )
        
        # Get clinic settings for operating hours
        settings = ClinicSettings.load()
        opening_time = settings.opening_time or datetime_time(9, 0)
        closing_time = settings.closing_time or datetime_time(17, 0)
        
        # Generate hourly time slots between opening and closing time
        clinic_hours = []
        current_hour = opening_time.hour
        closing_hour = closing_time.hour
        
        # Skip lunch hour (12:00 PM)
        while current_hour < closing_hour:
            if current_hour != 12:  # Skip lunch hour
                time_str = f"{current_hour:02d}:00"
                # Format display time (AM/PM)
                if current_hour == 0:
                    display = "12:00 AM"
                elif current_hour < 12:
                    display = f"{current_hour}:00 AM"
                elif current_hour == 12:
                    display = "12:00 PM"
                else:
                    display = f"{current_hour - 12}:00 PM"
                
                clinic_hours.append({
                    'time': time_str,
                    'display': display
                })
            current_hour += 1
        
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
    """Handle HTMX booking form submission - REQUIRES AUTHENTICATION"""
    # Block unauthenticated users
    if not request.user.is_authenticated:
        return HttpResponse(
            '<div class="alert alert-danger">'
            '<i class="fas fa-exclamation-circle"></i> '
            'You must be logged in to book an appointment. '
            'Please visit the clinic in person to create an account.'
            '</div>',
            status=403
        )
    
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
            created_by=request.user  # Always authenticated at this point
        )
        
        # Send confirmation email
        email_sent = send_booking_confirmation_email(booking)
        if email_sent:
            logger.info(f"Booking confirmation email sent for booking #{booking.id}")
        
        # Redirect to success page using HX-Redirect
        response = HttpResponse()
        response['HX-Redirect'] = f'/admin/success/?booking_id={booking.id}'
        return response
        
    except Exception as e:
        # Log the error (in production, use proper logging)
        logger.error(f"Booking creation failed: {str(e)}", exc_info=True)
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
        logger.info(f"Contact form submission from {name} ({email})")
        logger.debug(f"Subject: {subject}")
        logger.debug(f"Phone: {phone}")
        logger.debug(f"Message: {message}")
        
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
        logger.error(f"Contact form submission failed: {str(e)}", exc_info=True)
        return HttpResponse(
            '<div class="alert alert-danger">'
            '<i class="fas fa-exclamation-circle"></i> '
            'An error occurred while sending your message. Please try again or contact us directly.'
            '</div>',
            status=500
        )
