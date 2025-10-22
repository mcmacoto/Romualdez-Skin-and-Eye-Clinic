"""
API endpoints for patient management
Handles patient profiles, medical records, and related operations
"""
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum

from ...models import Patient, MedicalRecord, Booking, Billing, Payment


@login_required
@require_http_methods(["GET"])
def api_get_patients(request):
    """API endpoint to get all patients"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to access this resource.'
        }, status=403)
    
    try:
        patients = Patient.objects.select_related('user', 'created_by').order_by('-created_at')
        
        patients_data = []
        for patient in patients:
            # Count medical records for this patient
            medical_records_count = patient.medical_records.count()
            
            # Combine emergency contact info
            emergency_contact = 'N/A'
            if patient.emergency_contact_name or patient.emergency_contact_phone:
                emergency_contact = f"{patient.emergency_contact_name or 'N/A'} - {patient.emergency_contact_phone or 'N/A'}"
            
            patients_data.append({
                'id': patient.id,
                'name': patient.user.get_full_name() or patient.user.username,
                'email': patient.user.email,
                'phone': patient.phone,
                'date_of_birth': patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else 'N/A',
                'gender': patient.get_gender_display(),
                'address': patient.address or 'N/A',
                'emergency_contact': emergency_contact,
                'medical_history': patient.medical_history or 'None',
                'allergies': patient.allergies or 'None',
                'medical_records_count': medical_records_count,
                'created_at': patient.created_at.strftime('%Y-%m-%d %H:%M'),
                'created_by': patient.created_by.get_full_name() if patient.created_by else 'System',
            })
        
        return JsonResponse({
            'success': True,
            'patients': patients_data,
            'count': len(patients_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_get_patient_profile(request):
    """API endpoint to get current patient's profile and medical records"""
    try:
        # Try to get patient profile for the logged-in user
        try:
            patient = Patient.objects.select_related('user').get(user=request.user)
        except Patient.DoesNotExist:
            return JsonResponse({
                'error': 'You have no existing profile yet.'
            }, status=404)
        
        # Get patient basic information
        gender_display = {
            'M': 'Male',
            'F': 'Female',
            'O': 'Other'
        }.get(patient.gender, 'Not specified')
        
        profile_data = {
            'id': patient.id,
            'full_name': patient.user.get_full_name() or patient.user.username,
            'email': patient.user.email,
            'username': patient.user.username,
            'date_of_birth': patient.date_of_birth.strftime('%B %d, %Y'),
            'gender': gender_display,
            'phone': patient.phone,
            'address': patient.address,
            'emergency_contact_name': patient.emergency_contact_name,
            'emergency_contact_phone': patient.emergency_contact_phone,
            'blood_type': patient.blood_type,
            'allergies': patient.allergies,
            'current_medications': patient.current_medications,
            'medical_history': patient.medical_history,
        }
        
        # Get billing information for this patient (using email match since Booking uses email)
        
        # Find all bookings associated with this patient's email
        patient_bookings = Booking.objects.filter(patient_email=patient.user.email)
        
        # Get all billings for these bookings
        patient_billings = Billing.objects.filter(
            booking__patient_email=patient.user.email
        ).select_related('booking').prefetch_related('payments')
        
        # Calculate financial summary
        total_billings = patient_billings.count()
        paid_billings = patient_billings.filter(is_paid=True).count()
        unpaid_billings = patient_billings.filter(is_paid=False).count()
        
        total_billed = patient_billings.aggregate(total=Sum('total_amount'))['total'] or 0
        total_paid = patient_billings.aggregate(total=Sum('amount_paid'))['total'] or 0
        remaining_balance = patient_billings.filter(is_paid=False).aggregate(total=Sum('balance'))['total'] or 0
        
        # Get recent billing transactions
        recent_billings = []
        for billing in patient_billings.order_by('-issued_date')[:5]:
            recent_billings.append({
                'id': billing.id,
                'booking_date': billing.booking.date.strftime('%B %d, %Y'),
                'service': billing.booking.service.name,
                'total_amount': float(billing.total_amount),
                'amount_paid': float(billing.amount_paid),
                'balance': float(billing.balance),
                'is_paid': billing.is_paid,
                'status': billing.get_status_text(),
                'issued_date': billing.issued_date.strftime('%B %d, %Y'),
            })
        
        # Get recent payments
        recent_payments = []
        all_payments = Payment.objects.filter(
            billing__booking__patient_email=patient.user.email
        ).select_related('billing').order_by('-payment_date')[:5]
        
        for payment in all_payments:
            recent_payments.append({
                'id': payment.id,
                'amount': float(payment.amount_paid),
                'payment_method': payment.payment_method,
                'payment_date': payment.payment_date.strftime('%B %d, %Y at %I:%M %p'),
                'reference_number': payment.reference_number,
                'billing_id': payment.billing.id,
            })
        
        profile_data['billing_summary'] = {
            'total_billings': total_billings,
            'paid_billings': paid_billings,
            'unpaid_billings': unpaid_billings,
            'total_billed': float(total_billed),
            'total_paid': float(total_paid),
            'remaining_balance': float(remaining_balance),
            'recent_billings': recent_billings,
            'recent_payments': recent_payments,
        }
        
        # Get medical records
        medical_records = MedicalRecord.objects.filter(
            patient=patient
        ).prefetch_related('images').order_by('-visit_date')
        
        records_data = []
        for record in medical_records:
            # Check if record has vital signs
            has_vitals = any([
                record.temperature,
                record.blood_pressure_systolic,
                record.heart_rate,
                record.weight,
                record.height
            ])
            
            # Format blood pressure
            blood_pressure = None
            if record.blood_pressure_systolic and record.blood_pressure_diastolic:
                blood_pressure = f"{record.blood_pressure_systolic}/{record.blood_pressure_diastolic}"
            
            # Get medical images
            images_list = []
            for image in record.images.all():
                if image.image:
                    images_list.append({
                        'id': image.id,
                        'url': request.build_absolute_uri(image.image.url),
                        'title': image.title,
                        'description': image.description,
                        'image_type': image.get_image_type_display(),
                    })
            
            records_data.append({
                'id': record.id,
                'visit_date': record.visit_date.strftime('%B %d, %Y at %I:%M %p'),
                'chief_complaint': record.chief_complaint,
                'symptoms': record.symptoms,
                'diagnosis': record.diagnosis,
                'treatment_plan': record.treatment_plan,
                'has_vitals': has_vitals,
                'temperature': float(record.temperature) if record.temperature else None,
                'blood_pressure': blood_pressure,
                'heart_rate': record.heart_rate,
                'weight': float(record.weight) if record.weight else None,
                'height': float(record.height) if record.height else None,
                'follow_up_date': record.follow_up_date.strftime('%B %d, %Y') if record.follow_up_date else None,
                'additional_notes': record.additional_notes,
                'images': images_list,
            })
        
        profile_data['medical_records'] = records_data
        
        return JsonResponse(profile_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_get_patient_medical_records(request, patient_id):
    """Get all medical records for a specific patient"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to access this resource.'
        }, status=403)
    
    try:
        # Get patient
        patient = Patient.objects.get(id=patient_id)
        
        # Get all medical records
        records = MedicalRecord.objects.filter(patient=patient).select_related('created_by').order_by('-visit_date')
        
        records_data = []
        for record in records:
            records_data.append({
                'id': record.id,
                'visit_date': record.visit_date.strftime('%Y-%m-%d %H:%M'),
                'chief_complaint': record.chief_complaint,
                'diagnosis': record.diagnosis or 'N/A',
                'treatment_plan': record.treatment_plan or 'N/A',
                'created_by': record.created_by.get_full_name() if record.created_by else 'System',
            })
        
        return JsonResponse({
            'success': True,
            'records': records_data,
            'count': len(records_data)
        })
        
    except Patient.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Patient not found'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["DELETE"])
def api_delete_patient(request, patient_id):
    """Delete a patient and all associated records"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to access this resource.'
        }, status=403)
    
    try:
        # Get patient
        patient = Patient.objects.get(id=patient_id)
        patient_name = patient.user.get_full_name()
        
        # Delete patient (cascade will handle related records)
        patient.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Patient {patient_name} deleted successfully'
        })
        
    except Patient.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Patient not found'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
