"""
API endpoints for appointment management
Handles appointments, consultations, and status updates
"""
import json

from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum

from ...models import Booking, Billing, Patient, MedicalRecord


@login_required
@require_http_methods(["GET"])
def api_get_all_appointments(request):
    """Get all appointments with consultation status for the appointments modal"""
    try:
        # Get all confirmed bookings (which have appointments) that are NOT done
        bookings = Booking.objects.filter(
            status='Confirmed',
            consultation_status__in=['Not Yet', 'Ongoing']
        ).select_related('service').order_by('date', 'time')  # Order chronologically
        
        appointments_data = []
        for booking in bookings:
            appointments_data.append({
                'booking_id': booking.id,
                'patient_name': booking.patient_name,
                'patient_email': booking.patient_email,
                'booking_date': booking.date.strftime('%B %d, %Y'),
                'booking_time': booking.time.strftime('%I:%M %p'),
                'service': booking.service.name if booking.service else 'N/A',
                'consultation_status': booking.consultation_status
            })
        
        return JsonResponse(appointments_data, safe=False)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@staff_member_required
@require_http_methods(["POST"])
def api_mark_consultation_done(request, booking_id):
    """Mark a consultation as done, which triggers patient record creation"""
    try:
        # Get the booking
        booking = Booking.objects.get(id=booking_id, status='Confirmed')
        
        # Check if already done
        if booking.consultation_status == 'Done':
            return JsonResponse({
                'success': False,
                'error': 'Consultation already marked as done'
            }, status=400)
        
        # Update consultation status to Done
        # Set flag to trigger the post_save signal for creating Patient, MedicalRecord, and Billing
        booking.consultation_status = 'Done'
        booking._consultation_completed = True  # Signal flag
        booking.save()
        
        # Calculate new total appointments count (Not Yet + Ongoing)
        new_total = Booking.objects.filter(
            status='Confirmed',
            consultation_status__in=['Not Yet', 'Ongoing']
        ).count()
        
        # Get updated financial statistics
        
        # Get all billings
        all_billings = Billing.objects.all()
        
        # Calculate financial metrics
        total_billed = all_billings.aggregate(total=Sum('total_amount'))['total'] or 0
        total_paid = all_billings.filter(is_paid=True).aggregate(total=Sum('total_amount'))['total'] or 0
        total_outstanding = all_billings.filter(is_paid=False).aggregate(total=Sum('balance'))['total'] or 0
        
        # Count billing statuses
        paid_count = all_billings.filter(is_paid=True).count()
        partial_count = all_billings.filter(is_paid=False, amount_paid__gt=0).count()
        unpaid_count = all_billings.filter(is_paid=False, amount_paid=0).count()
        total_bills = all_billings.count()
        
        # Get clinic statistics
        total_patients = Patient.objects.count()
        total_medical_records = MedicalRecord.objects.count()
        
        return JsonResponse({
            'success': True,
            'message': f'Consultation marked as done for {booking.patient_name}',
            'new_total_appointments': new_total,
            'financial_stats': {
                'total_billed': float(total_billed),
                'total_paid': float(total_paid),
                'outstanding_balance': float(total_outstanding),
                'paid_bills': paid_count,
                'partial_bills': partial_count,
                'unpaid_bills': unpaid_count,
                'total_bills': total_bills
            },
            'clinic_stats': {
                'total_patients': total_patients,
                'total_medical_records': total_medical_records
            }
        })
        
    except Booking.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Booking not found'
        }, status=404)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@staff_member_required
@require_http_methods(["POST"])
def api_update_consultation_status(request, booking_id):
    """Update consultation status (Not Yet, Ongoing) without triggering done actions"""
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        
        # Validate status
        if new_status not in ['Not Yet', 'Ongoing']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid status. Use api_mark_consultation_done for Done status.'
            }, status=400)
        
        # Get the booking
        booking = Booking.objects.get(id=booking_id, status='Confirmed')
        
        # Update consultation status
        booking.consultation_status = new_status
        booking.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Status updated to {new_status}'
        })
        
    except Booking.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Booking not found'
        }, status=404)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@staff_member_required
@require_http_methods(["DELETE"])
def api_delete_appointment(request, booking_id):
    """Delete/cancel an appointment"""
    try:
        # Get the booking
        booking = Booking.objects.get(id=booking_id)
        patient_name = booking.patient_name
        
        # Delete the booking
        booking.delete()
        
        # Get updated total appointments count
        new_total = Booking.objects.filter(status='Confirmed').count()
        
        return JsonResponse({
            'success': True,
            'message': f'Appointment for {patient_name} has been cancelled',
            'new_total_appointments': new_total
        })
        
    except Booking.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Appointment not found'
        }, status=404)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)
