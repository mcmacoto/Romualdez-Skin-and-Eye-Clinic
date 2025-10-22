"""
API endpoints for booking management
Handles pending bookings, accept/decline operations
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction

from ...models import Booking, Appointment


@login_required
@require_http_methods(["GET"])
def api_get_pending_bookings(request):
    """API endpoint to get all pending bookings"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to access this resource.'
        }, status=403)
    
    try:
        pending_bookings = Booking.objects.filter(status='Pending').select_related('service').order_by('-created_at')
        
        bookings_data = []
        for booking in pending_bookings:
            bookings_data.append({
                'id': booking.id,
                'patient_name': booking.patient_name,
                'patient_email': booking.patient_email,
                'patient_phone': booking.patient_phone,
                'service': booking.service.name if booking.service else 'N/A',
                'date': booking.date.strftime('%Y-%m-%d'),
                'time': booking.time.strftime('%H:%M'),
                'notes': booking.notes or '',
                'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M'),
            })
        
        return JsonResponse({
            'success': True,
            'bookings': bookings_data,
            'count': len(bookings_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_accept_booking(request, booking_id):
    """
    API endpoint to accept a booking
    Creates Patient, MedicalRecord, and Billing automatically
    """
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to perform this action.'
        }, status=403)
    
    try:
        with transaction.atomic():
            # Get the booking
            booking = Booking.objects.select_related('service').get(id=booking_id, status='Pending')
            
            # Update booking status
            booking.status = 'Confirmed'
            booking.save()  # This triggers the signals that create Patient, MedicalRecord, Billing
            
            # Get updated statistics for dashboard
            pending_bookings = Booking.objects.filter(status='Pending').count()
            confirmed_appointments = Appointment.objects.filter(status='Confirmed').count()
            total_appointments = Appointment.objects.count()
            
            return JsonResponse({
                'success': True,
                'message': f'Booking accepted for {booking.patient_name}. Patient profile, medical record, and billing created automatically.',
                'booking_id': booking.id,
                'stats': {
                    'pending_bookings': pending_bookings,
                    'confirmed_appointments': confirmed_appointments,
                    'total_appointments': total_appointments
                }
            })
            
    except Booking.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Booking not found or already processed'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error accepting booking: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_decline_booking(request, booking_id):
    """API endpoint to decline/reject a booking"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to perform this action.'
        }, status=403)
    
    try:
        with transaction.atomic():
            # Get the booking
            booking = Booking.objects.get(id=booking_id, status='Pending')
            
            # Update booking status to Cancelled
            booking.status = 'Cancelled'
            booking.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Booking declined for {booking.patient_name}',
                'booking_id': booking.id
            })
            
    except Booking.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Booking not found or already processed'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error declining booking: {str(e)}'
        }, status=500)
