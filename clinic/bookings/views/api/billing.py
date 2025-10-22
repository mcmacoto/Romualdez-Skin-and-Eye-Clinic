"""
API endpoints for billing management
Handles billing records, payments, and fee updates
"""
from decimal import Decimal
import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from ...models import Billing, Payment


@login_required
@require_http_methods(["GET"])
def api_get_unpaid_patients(request):
    """Get all patients with unpaid billings"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to access this resource.'
        }, status=403)
    
    try:
        unpaid_billings = Billing.objects.filter(
            is_paid=False
        ).select_related('booking__service').order_by('-issued_date')
        
        unpaid_data = []
        for billing in unpaid_billings:
            unpaid_data.append({
                'billing_id': billing.id,  # Changed from 'id' to 'billing_id'
                'patient_name': billing.booking.patient_name,
                'patient_email': billing.booking.patient_email,  # Added patient_email
                'service': billing.booking.service.name,
                'booking_date': billing.booking.date.strftime('%B %d, %Y'),  # Changed format to match expected
                'service_fee': float(billing.service_fee),  # Added service_fee
                'medicine_fee': float(billing.medicine_fee),  # Added medicine_fee
                'total_amount': float(billing.total_amount),
                'amount_paid': float(billing.amount_paid),
                'balance': float(billing.balance),
                'issued_date': billing.issued_date.strftime('%B %d, %Y'),  # Changed format to match expected
                'status': billing.get_status_text(),
            })
        
        # Return array directly (not wrapped in object) to match frontend expectations
        return JsonResponse(unpaid_data, safe=False)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_get_all_billings(request):
    """Get all billing records"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to access this resource.'
        }, status=403)
    
    try:
        billings = Billing.objects.select_related('booking__service').order_by('-issued_date')
        
        billings_data = []
        for billing in billings:
            billings_data.append({
                'id': billing.id,
                'patient_name': billing.booking.patient_name,
                'service': billing.booking.service.name,
                'booking_date': billing.booking.date.strftime('%Y-%m-%d'),
                'total_amount': float(billing.total_amount),
                'amount_paid': float(billing.amount_paid),
                'balance': float(billing.balance),
                'is_paid': billing.is_paid,
                'issued_date': billing.issued_date.strftime('%Y-%m-%d'),
                'status': billing.get_status_text(),
            })
        
        return JsonResponse({
            'success': True,
            'billings': billings_data,
            'count': len(billings_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_mark_billing_paid(request, billing_id):
    """Mark a billing as paid"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to access this resource.'
        }, status=403)
    
    try:
        billing = Billing.objects.get(id=billing_id)
        
        # Mark as paid
        billing.is_paid = True
        billing.amount_paid = billing.total_amount
        billing.balance = Decimal('0.00')
        billing.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Billing marked as paid successfully'
        })
        
    except Billing.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Billing not found'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_update_billing_fees(request, billing_id):
    """Update billing fees (service, consultation, etc.)"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to access this resource.'
        }, status=403)
    
    try:
        billing = Billing.objects.get(id=billing_id)
        
        # Parse request data
        data = json.loads(request.body)
        
        # Update fees
        if 'service_fee' in data:
            billing.service_fee = Decimal(str(data['service_fee']))
        if 'consultation_fee' in data:
            billing.consultation_fee = Decimal(str(data['consultation_fee']))
        if 'additional_charges' in data:
            billing.additional_charges = Decimal(str(data['additional_charges']))
        if 'discount' in data:
            billing.discount = Decimal(str(data['discount']))
        
        # Recalculate total
        billing.save()  # The save method will recalculate total_amount
        
        return JsonResponse({
            'success': True,
            'message': 'Billing fees updated successfully',
            'billing': {
                'id': billing.id,
                'service_fee': float(billing.service_fee),
                'consultation_fee': float(billing.consultation_fee),
                'additional_charges': float(billing.additional_charges),
                'discount': float(billing.discount),
                'total_amount': float(billing.total_amount),
                'balance': float(billing.balance),
            }
        })
        
    except Billing.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Billing not found'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
