"""
Booking-related views
Handles appointment booking creation and success pages
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from datetime import date, datetime, timedelta

from ..models import Service, Booking


def booking_success(request):
    """Booking success confirmation page"""
    return render(request, 'bookings/success.html')


@login_required(login_url='/landing/')
def booking(request):
    """Booking form page with validation and submission"""
    if request.method == "POST":
        # Check if it's an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
            # Extract form data
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            date_str = request.POST.get('date', '').strip()
            time_str = request.POST.get('time', '').strip()
            message = request.POST.get('message', '').strip()
            appointment_type = request.POST.get('appointment_type', 'dermatology').strip()
            
            # Validation
            if not all([name, email, phone, date_str, time_str, appointment_type]):
                error_msg = "All required fields must be filled out."
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'error': error_msg
                    }, status=400)
                messages.error(request, error_msg)
                return redirect('booking')
            
            # Date validation - must be at least 1 day ahead
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            today = date.today()
            tomorrow = today + timedelta(days=1)
            
            if booking_date < tomorrow:
                error_msg = "Bookings must be made at least 1 day in advance. Please select a date starting from tomorrow onwards."
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'error': error_msg
                    }, status=400)
                messages.error(request, error_msg)
                return redirect('booking')
            
            # Get or create the service based on appointment type
            service_map = {
                'dermatology': 'Dermatology Consultation',
                'cosmetic': 'Cosmetic Treatment',
                'screening': 'Skin Cancer Screening',
            }
            
            service_name = service_map.get(appointment_type, 'General Consultation')
            service, created = Service.objects.get_or_create(
                name=service_name,
                defaults={
                    'description': f'{service_name} service',
                    'image': 'services/default.jpg'  # Make sure you have a default image
                }
            )
            
            # Create the booking
            booking = Booking.objects.create(
                patient_name=name,
                patient_email=email,
                patient_phone=phone,
                date=date_str,
                time=time_str,
                service=service,
                notes=message,
                status='Pending',
                created_by=request.user if request.user.is_authenticated else None
            )
            
            success_msg = f"Thank you {name}! Your {appointment_type} appointment request has been submitted successfully. We'll contact you within 24 hours to confirm."
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': success_msg,
                    'booking_id': booking.id
                })
            
            messages.success(request, success_msg)
            return redirect('booking')
            
        except Exception as e:
            error_msg = f"An error occurred while processing your booking: {str(e)}"
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                }, status=500)
            messages.error(request, error_msg)
            return redirect('booking')
        
    # GET request
    tomorrow = date.today() + timedelta(days=1)
    context = {
        'today': date.today(),
        'tomorrow': tomorrow,
        'services': Service.objects.all()
    }
    return render(request, 'bookings/booking.html', context)
