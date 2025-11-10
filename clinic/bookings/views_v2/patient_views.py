"""
Patient and Medical Records Management Views for v2
Handles patient profiles, medical records, prescriptions, and medical images
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import datetime, date
import logging
import traceback

from ..models import (
    Patient, MedicalRecord, Billing, Booking, Inventory,
    Prescription, MedicalImage
)
from ..decorators import staff_required
from ..utils.responses import htmx_error, htmx_success
from ..utils.db_helpers import atomic_save

logger = logging.getLogger(__name__)


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_patients_list(request):
    """Return HTML fragment of all patients with optional search and pagination"""
    
    try:
        # Start with all patients - optimize query
        patients = Patient.objects.select_related('user').prefetch_related('medical_records')
        
        # Handle multi-field search
        search_query = request.GET.get('search', '').strip()
        if search_query:  # Only apply filter if search_query has content
            patients = patients.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(address__icontains=search_query)
            )
            logger.info(f"Patient search query: '{search_query}' by {request.user.username}")
        
        # Filter by gender
        gender = request.GET.get('gender', '').strip()
        if gender and gender in ['M', 'F', 'O']:
            patients = patients.filter(gender=gender)
        
        # Filter by blood type
        blood_type = request.GET.get('blood_type', '').strip()
        if blood_type:
            patients = patients.filter(blood_type=blood_type)
        
        # Filter by age range (approximate)
        age_min = request.GET.get('age_min', '').strip()
        age_max = request.GET.get('age_max', '').strip()
        
        if age_min:
            try:
                from datetime import timedelta
                years_ago = date.today() - timedelta(days=int(age_min) * 365)
                patients = patients.filter(date_of_birth__lte=years_ago)
            except (ValueError, TypeError):
                pass
        
        if age_max:
            try:
                from datetime import timedelta
                years_ago = date.today() - timedelta(days=int(age_max) * 365)
                patients = patients.filter(date_of_birth__gte=years_ago)
            except (ValueError, TypeError):
                pass
        
        # Handle column sorting
        sort_by = request.GET.get('sort', '').strip()
        sort_order = request.GET.get('order', 'asc').strip()
        
        # Define valid sort fields and their mappings
        sort_fields = {
            'name': 'user__last_name',
            'email': 'user__email',
            'phone': 'phone',
            'gender': 'gender',
            'dob': 'date_of_birth',
        }
        
        if sort_by in sort_fields:
            field = sort_fields[sort_by]
            if sort_order == 'desc':
                field = f'-{field}'
            patients = patients.order_by(field)
        else:
            patients = patients.order_by('-created_at')
        
        # Add pagination
        paginator = Paginator(patients, 25)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'bookings_v2/partials/patients_list.html', {
            'patients': page_obj,
            'paginator': paginator,
            'page_obj': page_obj,
            'sort_by': sort_by,
            'sort_order': sort_order,
        })
    except Exception as e:
        logger.error(f"Error in patients list view: {str(e)}", exc_info=True)
        return htmx_error(f"Error loading patients: {str(e)}", status=500)


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_patient_records(request, patient_id):
    """Return HTML fragment of medical records for a specific patient"""
    try:
        logger.info(f"Loading medical records for patient ID: {patient_id}")
        patient = Patient.objects.get(id=patient_id)
        
        logger.info(f"Patient found: {patient.user.get_full_name()}")
        
        records = MedicalRecord.objects.filter(
            patient=patient
        ).select_related('created_by').prefetch_related(
            'prescriptions__medicine', 'images'
        ).order_by('-visit_date')
        
        logger.info(f"Found {records.count()} medical records for patient {patient_id}")
        
        return render(request, 'bookings_v2/partials/patient_medical_records.html', {
            'records': records,
            'patient': patient
        })
    except Patient.DoesNotExist:
        logger.warning(f"Patient ID {patient_id} not found")
        return HttpResponse(
            '<div class="alert alert-danger">Patient not found</div>',
            status=404
        )
    except Exception as e:
        logger.error(f"Error loading medical records for patient {patient_id}: {str(e)}", exc_info=True)
        return HttpResponse(
            f'<div class="alert alert-danger">Error loading medical records: {str(e)}</div>',
            status=500
        )


@login_required
@staff_required
def htmx_patient_detail(request, patient_id):
    """Return HTML fragment with detailed patient profile"""
    try:
        patient = Patient.objects.select_related('user').get(id=patient_id)
        
        # Get patient's full name for lookups
        patient_full_name = patient.user.get_full_name() or patient.user.username
        
        # Get statistics
        total_appointments = Booking.objects.filter(
            patient_name=patient_full_name
        ).count()
        
        total_records = MedicalRecord.objects.filter(patient=patient).count()
        
        # Calculate outstanding balance
        # Billing is linked to Booking, so we need to find billings through bookings
        unpaid_billings = Billing.objects.filter(
            booking__patient_name=patient_full_name,
            is_paid=False
        )
        total_outstanding = sum(billing.total_amount for billing in unpaid_billings) if unpaid_billings.exists() else 0
        
        # Get recent appointments (last 5)
        recent_appointments = Booking.objects.filter(
            patient_name=patient_full_name
        ).select_related('service').order_by('-date', '-time')[:5]
        
        # Get recent medical records (last 3)
        recent_records = MedicalRecord.objects.filter(
            patient=patient
        ).select_related('created_by').prefetch_related('prescriptions').order_by('-visit_date')[:3]
        
        # Get recent billings (last 5)
        recent_billings = Billing.objects.filter(
            booking__patient_name=patient_full_name
        ).select_related('booking__service').order_by('-issued_date')[:5]
        
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
@staff_required
@require_http_methods(["POST"])
def upload_profile_picture(request):
    """Upload and save profile picture for a user's patient profile"""
    from django.http import JsonResponse
    import os
    
    try:
        user_id = request.POST.get('user_id')
        profile_picture = request.FILES.get('profile_picture')
        
        if not user_id or not profile_picture:
            return JsonResponse({'success': False, 'error': 'Missing user ID or image file'}, status=400)
        
        user = User.objects.get(id=user_id)
        
        # Get or create patient profile for this user
        try:
            patient = Patient.objects.get(user=user)
        except Patient.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'No patient profile found for this user'}, status=404)
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
        if profile_picture.content_type not in allowed_types:
            return JsonResponse({'success': False, 'error': 'Invalid file type. Only JPG and PNG allowed.'}, status=400)
        
        # Validate file size (max 5MB)
        if profile_picture.size > 5 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'File size must be less than 5MB'}, status=400)
        
        # Delete old profile picture if exists
        if patient.profile_picture:
            old_picture_path = patient.profile_picture.path
            if os.path.exists(old_picture_path):
                os.remove(old_picture_path)
        
        # Save new profile picture with automatic retry on database locks
        patient.profile_picture = profile_picture
        atomic_save(patient)
        
        logger.info(f"Profile picture uploaded for user {user.get_full_name()} by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Profile picture uploaded successfully',
            'profile_picture_url': patient.profile_picture.url
        })
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
    except Exception as e:
        logger.error(f"Error uploading profile picture: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@staff_required
@require_http_methods(["DELETE"])
def htmx_delete_patient(request, patient_id):
    """Delete patient - handles cascade and returns empty response"""
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
                '<tr><td colspan="7" class="alert alert-warning m-2">Cannot delete patient with unpaid bills. Please settle all bills first.</td></tr>',
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
        response = HttpResponse('', status=200)
        response['HX-Trigger'] = 'refreshStats'
        return response
        
    except Patient.DoesNotExist:
        return HttpResponse(
            '<tr><td colspan="7" class="alert alert-danger m-2">Patient not found</td></tr>',
            status=404
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return HttpResponse(
            f'<tr><td colspan="7" class="alert alert-danger m-2">Error deleting patient: {str(e)}<br><small class="text-muted"><pre>{error_details}</pre></small></td></tr>',
            status=500
        )


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_patient_create_form(request):

    """Return HTML form for creating a new patient"""
    return render(request, 'bookings_v2/htmx_partials/patient_form.html', {
        'today': date.today().isoformat()
    })


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_patient_create(request):
    """Create a new patient with user account"""
    try:
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
        response = render(request, 'bookings_v2/partials/patients_list.html', {
            'patients': patients
        })
        response['HX-Trigger'] = 'refreshStats'
        return response
        
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_patient_edit_form(request, patient_id):
    """Return HTML form for editing a patient"""
    try:
        patient = Patient.objects.select_related('user').get(id=patient_id)
        return render(request, 'bookings_v2/htmx_partials/patient_form.html', {
            'patient': patient,
            'today': date.today().isoformat()
        })
    except Patient.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Patient not found</div>', status=404)


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_patient_update(request, patient_id):
    """Update an existing patient"""
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
        response = render(request, 'bookings_v2/partials/patients_list.html', {
            'patients': patients
        })
        response['HX-Trigger'] = 'refreshStats'
        return response
        
    except Patient.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Patient not found</div>', status=404)
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


# ========================================
# MEDICAL RECORDS MANAGEMENT
# ========================================

@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_medical_records_list(request):
    """Return HTML fragment of all medical records with optional search"""
    # Start with all medical records
    records = MedicalRecord.objects.select_related(
        'patient__user', 'created_by'
    ).prefetch_related(
        'prescriptions', 'images'
    )
    
    # Handle search - only filter if search query is not empty
    search_query = request.GET.get('search', '').strip()
    if search_query:  # Only apply filter if search_query has content
        records = records.filter(
            Q(patient__user__first_name__icontains=search_query) |
            Q(patient__user__last_name__icontains=search_query) |
            Q(diagnosis__icontains=search_query) |
            Q(chief_complaint__icontains=search_query) |
            Q(treatment_plan__icontains=search_query)
        )
    # If search_query is empty, return all records (no filter applied)
    
    records = records.order_by('-visit_date')
    
    return render(request, 'bookings_v2/partials/medical_records_list.html', {
        'records': records
    })


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_medical_record_edit_form(request, record_id):
    """Return HTML fragment with medical record edit form"""
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
@staff_required
@require_http_methods(["PUT", "POST"])
def htmx_medical_record_update(request, record_id):
    """Update medical record and return updated list"""
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
        
        response = render(request, 'bookings_v2/partials/medical_records_list.html', {
            'records': records
        })
        response['HX-Trigger'] = 'refreshStats'
        return response
        
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
@staff_required
@require_http_methods(["GET"])
def htmx_medical_record_create_form(request):
    """Return HTML fragment with medical record creation form"""
    # Get all patients for the dropdown
    patients = Patient.objects.select_related('user').order_by('user__last_name', 'user__first_name')
    
    return render(request, 'bookings_v2/htmx_partials/medical_record_create_form.html', {
        'patients': patients
    })


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_medical_record_create(request):
    """Create new medical record and return updated list"""
    try:
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
        response = render(request, 'bookings_v2/htmx_partials/medical_record_form.html', {
            'record': record,
            'just_created': True  # Flag to show success message
        })
        response['HX-Trigger'] = 'refreshStats'
        return response
        
    except Patient.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Patient not found</div>',
            status=404
        )
    except Exception as e:
        import traceback
        error_msg = f'<div class="alert alert-danger">Error creating record: {str(e)}<br><pre>{traceback.format_exc()}</pre></div>'
        logger.error(f"Error creating medical record: {traceback.format_exc()}")
        return HttpResponse(error_msg, status=500)


# ========================================
# PRESCRIPTION MANAGEMENT
# ========================================

@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_prescriptions(request, record_id):
    """Return HTML fragment showing prescriptions for a specific record"""
    try:
        record = MedicalRecord.objects.prefetch_related(
            'prescriptions__medicine'
        ).get(id=record_id)
        
        patient = record.patient
        prescriptions = record.prescriptions.all()
        
        # Always show header with "Add Prescription" button
        from django.urls import reverse
        html = f'''
        <div class="mb-3 d-flex justify-content-between align-items-center">
            <div>
                <h6><strong>Patient:</strong> {patient.user.get_full_name() or patient.user.username}</h6>
                <p class="text-muted mb-0">
                    <strong>Visit Date:</strong> {record.visit_date.strftime('%B %d, %Y at %I:%M %p')}
                </p>
            </div>
            <button 
                class="btn btn-sm btn-success"
                hx-get="{reverse('bookings_v2:htmx_prescription_create_form', args=[record_id])}"
                hx-target="#prescriptionsModalBody"
                hx-swap="innerHTML"
            >
                <i class="fas fa-plus me-2"></i>Add Prescription
            </button>
        </div>
        '''
        
        if not prescriptions:
            html += '''
            <div class="alert alert-info text-center">
                <i class="fas fa-pills fa-3x mb-3"></i>
                <h5>No Prescriptions Yet</h5>
                <p class="mb-0">Click "Add Prescription" above to create the first prescription for this visit.</p>
            </div>
            '''
            return HttpResponse(html)
        
        html += '''
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
            try:
                total_price += prescription.total_price
                instructions = prescription.instructions or 'Follow standard dosing instructions'
                
                # Get medicine name (custom or from inventory)
                if prescription.custom_medicine_name:
                    medicine_name = prescription.custom_medicine_name
                    medicine_badge = '<span class="badge bg-warning text-dark ms-2">External</span>'
                elif prescription.medicine:
                    medicine_name = prescription.medicine.name
                    medicine_badge = ''
                else:
                    medicine_name = 'Unknown Medicine'
                    medicine_badge = '<span class="badge bg-secondary ms-2">Error</span>'
                
                # Escape HTML to prevent issues with special characters
                from html import escape
                medicine_name_safe = escape(medicine_name)
                instructions_safe = escape(instructions)
                dosage_safe = escape(prescription.dosage)
                duration_safe = escape(prescription.duration or 'As needed')
                
                html += f'''
                    <tr>
                        <td>
                            <strong>{medicine_name_safe}</strong>{medicine_badge}
                            <br><small class="text-muted">Qty: {prescription.quantity}</small>
                        </td>
                        <td>{dosage_safe}</td>
                        <td>{duration_safe}</td>
                        <td>₱{prescription.total_price:,.2f}</td>
                        <td><small>{instructions_safe}</small></td>
                        <td class="text-center">
                            <button 
                                class="btn btn-sm btn-danger"
                                hx-delete="/admin/htmx/prescription/{prescription.id}/delete/"
                                hx-target="#prescriptionsModalBody"
                                hx-confirm="Are you sure you want to delete this prescription for {medicine_name_safe}?"
                            >
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                '''
            except Exception as e:
                logger.error(f"Error rendering prescription {prescription.id}: {str(e)}", exc_info=True)
                import traceback
                traceback.print_exc()
                # Skip this prescription if there's an error
                continue
        
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
    except Exception as e:
        import traceback
        error_msg = f'<div class="alert alert-danger"><strong>Error Loading Prescriptions:</strong><br>{str(e)}<br><pre class="mt-2">{traceback.format_exc()}</pre></div>'
        return HttpResponse(error_msg, status=500)


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_prescription_create_form(request, record_id):
    """Return HTML fragment with prescription creation form"""
    try:
        record = MedicalRecord.objects.select_related('patient__user').get(id=record_id)
        
        # Get all medicines from inventory
        # Include all items categorized as Medicine regardless of stock status
        # This allows prescribing even when showing "Out of Stock" warning
        medicines = Inventory.objects.filter(
            category='Medicine'
        ).order_by('name')
        
        # Debug: Log available medicines
        logger.debug(f"Available medicines count: {medicines.count()}")
        for med in medicines:
            logger.debug(f"  Medicine: {med.name} | Category: {med.category} | Status: {med.status} | Qty: {med.quantity}")
        
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
@csrf_exempt
@require_http_methods(["POST"])
def htmx_prescription_create(request, record_id):
    """Create prescription and return updated prescription list"""
    try:
        # Debug: Log POST data
        logger.debug(f"POST data: {dict(request.POST)}")
        
        record = MedicalRecord.objects.get(id=record_id)
        medicine_id = request.POST.get('medicine_id', '').strip()
        
        logger.debug(f"medicine_id: '{medicine_id}'")
        
        # Validate that a medicine was selected
        if not medicine_id:
            return HttpResponse(
                '<div class="alert alert-danger">Please select a medicine. Received: ' + str(request.POST.get('medicine_id', 'NOTHING')) + '</div>',
                status=400
            )
        
        # Check if "Other" option is selected
        if medicine_id == 'other':
            # Custom medicine not in inventory
            custom_medicine_name = request.POST.get('custom_medicine_name', '').strip()
            if not custom_medicine_name:
                return HttpResponse(
                    '<div class="alert alert-danger">Please provide a medicine name</div>',
                    status=400
                )
            
            custom_price = request.POST.get('custom_price', '0')
            try:
                unit_price = float(custom_price) if custom_price else 0
            except ValueError:
                unit_price = 0
            
            # Create prescription without inventory medicine
            prescription = Prescription.objects.create(
                medical_record=record,
                medicine=None,
                custom_medicine_name=custom_medicine_name,
                quantity=int(request.POST.get('quantity', 1)),
                dosage=request.POST.get('dosage'),
                duration=request.POST.get('duration', ''),
                instructions=request.POST.get('instructions', ''),
                unit_price=unit_price,
                prescribed_by=request.user
            )
        else:
            # Medicine from inventory
            medicine = Inventory.objects.get(item_id=medicine_id)
            
            # Create prescription
            prescription = Prescription.objects.create(
                medical_record=record,
                medicine=medicine,
                custom_medicine_name='',
                quantity=int(request.POST.get('quantity', 1)),
                dosage=request.POST.get('dosage'),
                duration=request.POST.get('duration', ''),
                instructions=request.POST.get('instructions', ''),
                unit_price=medicine.price,
                prescribed_by=request.user
            )
        
        logger.info(f"Prescription created successfully: ID={prescription.id}")
        
        # Return success message and trigger reload of prescription list via HTMX GET request
        # We can't call htmx_prescriptions() directly because it requires GET method
        # and this is a POST handler. Instead, we use HTMX to trigger a GET request.
        return HttpResponse(f'''
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            <i class="bi bi-check-circle-fill me-2"></i>
            Prescription added successfully!
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
        <div hx-get="/admin/htmx/prescriptions/{record_id}/" 
             hx-trigger="load" 
             hx-swap="outerHTML">
            <div class="text-center p-3">
                <div class="spinner-border spinner-border-sm text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                Loading prescriptions...
            </div>
        </div>
        ''')
        
    except MedicalRecord.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Medical record not found</div>',
            status=404
        )
    except Inventory.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Medicine not found in inventory</div>',
            status=404
        )
    except Exception as e:
        import traceback
        error_msg = f'<div class="alert alert-danger">Error creating prescription: {str(e)}<br><pre>{traceback.format_exc()}</pre></div>'
        return HttpResponse(error_msg, status=500)


@login_required
@staff_required
@require_http_methods(["DELETE"])
def htmx_prescription_delete(request, prescription_id):
    """Delete prescription and return updated list"""
    try:
        prescription = Prescription.objects.select_related('medical_record').get(id=prescription_id)
        record_id = prescription.medical_record.id
        prescription.delete()
        
        # Return success message and trigger reload of prescription list
        # We can't call htmx_prescriptions() directly from DELETE request
        return HttpResponse(f'''
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            <i class="bi bi-check-circle-fill me-2"></i>
            Prescription deleted successfully!
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
        <div hx-get="/admin/htmx/prescriptions/{record_id}/" 
             hx-trigger="load" 
             hx-swap="outerHTML">
            <div class="text-center p-3">
                <div class="spinner-border spinner-border-sm text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                Loading prescriptions...
            </div>
        </div>
        ''')
        
    except Prescription.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Prescription not found</div>',
            status=404
        )


# ========================================
# MEDICAL IMAGE MANAGEMENT
# ========================================

@login_required
@staff_required
@require_http_methods(["GET", "POST"])  # Allow POST for internal calls from upload
def htmx_medical_images(request, record_id):
    """Return HTML fragment showing medical images for a specific record"""
    try:
        record = MedicalRecord.objects.select_related('patient__user').prefetch_related('images').get(id=record_id)
        images = record.images.all()
        
        html = f'''
        <!-- Back Button -->
        <div class="mb-3">
            <button 
                type="button"
                class="btn btn-outline-secondary btn-sm"
                hx-get="/admin/htmx/medical-record/{record_id}/edit/"
                hx-target="#medicalImagesModalBody"
                hx-swap="innerHTML"
            >
                <i class="fas fa-arrow-left me-2"></i>Back to Medical Record
            </button>
        </div>
        
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
@staff_required
@require_http_methods(["GET"])
def htmx_medical_image_upload_form(request, record_id):
    """Return HTML fragment with medical image upload form"""
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
@staff_required
@require_http_methods(["POST"])
def htmx_medical_image_upload(request, record_id):
    """Upload medical image and return updated image list"""
    try:
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
@staff_required
@require_http_methods(["DELETE"])
def htmx_medical_image_delete(request, image_id):
    """Delete medical image and return updated list"""
    try:
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
@staff_required
@require_http_methods(["GET"])
def htmx_medical_record_detail(request, record_id):
    """Display detailed view of a medical record"""
    try:
        record = MedicalRecord.objects.select_related(
            'patient__user',
            'created_by',
            'updated_by'
        ).prefetch_related(
            'prescriptions__medicine',
            'images'
        ).get(id=record_id)
        
        return render(request, 'bookings_v2/partials/medical_record_detail.html', {
            'record': record
        })
        
    except MedicalRecord.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Medical record not found</div>',
            status=404
        )
    except Exception as e:
        import traceback
        error_msg = f'<div class="alert alert-danger">Error loading record: {str(e)}<br><pre>{traceback.format_exc()}</pre></div>'
        return HttpResponse(error_msg, status=500)


@login_required
@staff_required
@require_http_methods(["DELETE"])
def htmx_delete_medical_record(request, record_id):
    """Delete a medical record and all associated data"""
    try:
        record = MedicalRecord.objects.get(id=record_id)
        
        # Delete all associated medical images (files and DB records)
        for image in record.images.all():
            if image.image:
                image.image.delete()
            image.delete()
        
        # Delete all prescriptions
        record.prescriptions.all().delete()
        
        # Delete the record itself
        record.delete()
        
        # Return empty response (row will be removed from table)
        return HttpResponse('', status=200)
        
    except MedicalRecord.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Medical record not found</div>',
            status=404
        )
    except Exception as e:
        import traceback
        error_msg = f'<div class="alert alert-danger">Error deleting record: {str(e)}<br><pre>{traceback.format_exc()}</pre></div>'
        return HttpResponse(error_msg, status=500)
