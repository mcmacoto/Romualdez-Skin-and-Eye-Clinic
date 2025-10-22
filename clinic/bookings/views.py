from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.db.models import Sum, F, Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from datetime import date, datetime, timedelta
import json

from .models import (
    Appointment, Service, Booking, Patient, MedicalRecord, 
    Billing, Inventory, Prescription, Payment, POSSale
)

# Create your views here.
def booking_form(request):
    if request.method == "POST":
        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']
        date = request.POST['date']
        time = request.POST['time']
        message = request.POST.get('message', '')

        Appointment.objects.create(
            name=name, email=email, phone=phone, date=date, time=time, message=message
        )

        messages.success(request, "Your appointment request has been sent!")
        return redirect('success')

    return render(request, 'bookings/form.html')

def booking_success(request):
    return render(request, 'bookings/success.html')

def is_authenticated(user):
    return user.is_authenticated

def landing(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'bookings/landing.html')

@login_required(login_url='/landing/')
def home(request):  # Remove @login_required
    return render(request, 'bookings/home.html')

@login_required(login_url='/landing/')
def booking(request):
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


@login_required(login_url='/landing/')
def about(request):  # Remove @login_required
    return render(request, 'bookings/about.html')

@login_required(login_url='/landing/')
def services(request):  # Remove @login_required
    services = Service.objects.all()
    return render(request, 'bookings/services.html', {'services': services})

def contact(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you could save the contact message to a model or send an email
        # For now, we'll just show a success message
        messages.success(request, f"Thank you {name}! Your message has been sent. We'll get back to you soon.")
        return redirect('contact')
        
    return render(request, 'bookings/contact.html')


# ===== PENDING BOOKINGS API ENDPOINTS =====

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


# ===== PATIENTS API ENDPOINTS =====

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


# ===== MEDICAL RECORDS API ENDPOINTS =====

@login_required
@require_http_methods(["GET"])
def api_get_medical_records(request):
    """API endpoint to get all medical records"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to access this resource.'
        }, status=403)
    
    try:
        records = MedicalRecord.objects.select_related(
            'patient__user', 'created_by'
        ).prefetch_related('prescriptions', 'images').order_by('-visit_date')
        
        records_data = []
        for record in records:
            # Count prescriptions for this record
            prescriptions_count = record.prescriptions.count()
            
            # Get images for this record
            images_list = []
            for image in record.images.all():
                if image.image:
                    images_list.append({
                        'id': image.id,
                        'url': request.build_absolute_uri(image.image.url),
                        'title': image.title,
                        'description': image.description or '',
                        'image_type': image.image_type,
                        'uploaded_at': image.uploaded_at.strftime('%Y-%m-%d %H:%M'),
                        'uploaded_by': image.uploaded_by.get_full_name() if image.uploaded_by else 'Unknown'
                    })
            
            records_data.append({
                'id': record.id,
                'patient_name': record.patient.user.get_full_name() or record.patient.user.username,
                'patient_email': record.patient.user.email,
                'visit_date': record.visit_date.strftime('%Y-%m-%d'),
                'chief_complaint': record.chief_complaint or 'N/A',
                'symptoms': record.symptoms or 'N/A',
                'diagnosis': record.diagnosis or 'Pending',
                'treatment_plan': record.treatment_plan or 'N/A',
                'prescriptions_count': prescriptions_count,
                'images': images_list,
                'images_count': len(images_list),
                'notes': record.additional_notes or 'None',
                'created_at': record.created_at.strftime('%Y-%m-%d %H:%M'),
                'created_by': record.created_by.get_full_name() if record.created_by else 'System',
            })
        
        return JsonResponse({
            'success': True,
            'records': records_data,
            'count': len(records_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ===== INVENTORY API ENDPOINTS =====

@login_required
@require_http_methods(["GET"])
def api_get_inventory(request):
    """API endpoint to get all inventory items"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to access this resource.'
        }, status=403)
    
    try:
        inventory_items = Inventory.objects.all().order_by('name')
        
        inventory_data = []
        for item in inventory_items:
            # Calculate status badge color
            status_color = {
                'In Stock': 'success',
                'Low Stock': 'warning',
                'Out of Stock': 'danger'
            }.get(item.status, 'secondary')
            
            inventory_data.append({
                'id': item.item_id,
                'name': item.name,
                'description': item.description,
                'category': item.category,
                'quantity': item.quantity,
                'stock': item.stock,  # Minimum threshold
                'price': float(item.price),
                'status': item.status,
                'status_color': status_color,
                'expiry_date': item.expiry_date.strftime('%Y-%m-%d') if item.expiry_date else 'N/A',
                'date_stock_in': item.date_stock_in.strftime('%Y-%m-%d'),
            })
        
        return JsonResponse({
            'success': True,
            'inventory': inventory_data,
            'count': len(inventory_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@staff_member_required
def api_pos_sales(request):
    """API endpoint to fetch POS sales data for dashboard modal"""
    if not request.user.is_staff:
        return JsonResponse({
            'error': 'You do not have permission to access this resource.'
        }, status=403)
    
    try:
        # Get all POS sales, ordered by most recent first
        pos_sales = POSSale.objects.select_related('patient', 'created_by').all().order_by('-sale_date')
        
        sales_data = []
        for sale in pos_sales:
            sales_data.append({
                'id': sale.id,
                'receipt_number': sale.receipt_number,
                'sale_date': sale.sale_date.isoformat(),
                'customer_name': sale.customer_name,
                'patient_name': sale.patient.user.get_full_name() if sale.patient else None,
                'sale_type': sale.sale_type,
                'payment_method': sale.payment_method,
                'subtotal': float(sale.subtotal),
                'discount_amount': float(sale.discount_amount),
                'tax_amount': float(sale.tax_amount),
                'total_amount': float(sale.total_amount),
                'status': sale.status,
                'created_by': sale.created_by.username if sale.created_by else None,
                'notes': sale.notes or '',
            })
        
        return JsonResponse(sales_data, safe=False)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ===== PATIENT PROFILE API ENDPOINT =====

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


@staff_member_required
@require_http_methods(["GET"])
def api_get_unpaid_patients(request):
    """
    API endpoint to fetch all unpaid patients with their billing information
    """
    try:
        # Get all unpaid billings
        unpaid_billings = Billing.objects.filter(
            is_paid=False
        ).select_related('booking').order_by('-issued_date')
        
        unpaid_patients = []
        for billing in unpaid_billings:
            unpaid_patients.append({
                'billing_id': billing.id,
                'patient_name': billing.booking.patient_name,
                'patient_email': billing.booking.patient_email,
                'booking_date': billing.booking.date.strftime('%B %d, %Y'),
                'service': billing.booking.service.name if billing.booking.service else 'N/A',
                'service_fee': float(billing.service_fee),
                'medicine_fee': float(billing.medicine_fee),
                'total_amount': float(billing.total_amount),
                'amount_paid': float(billing.amount_paid),
                'balance': float(billing.balance),
                'issued_date': billing.issued_date.strftime('%B %d, %Y'),
            })
        
        return JsonResponse(unpaid_patients, safe=False)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@staff_member_required
@require_http_methods(["GET"])
def api_get_all_billings(request):
    """
    API endpoint to fetch all billings (both paid and unpaid)
    """
    try:
        # Get all billings
        all_billings = Billing.objects.all().select_related('booking', 'booking__service').order_by('-issued_date')
        
        billings_list = []
        for billing in all_billings:
            try:
                billings_list.append({
                    'id': billing.id,
                    'patient_name': billing.booking.patient_name,
                    'patient_email': billing.booking.patient_email,
                    'booking_date': billing.booking.date.strftime('%B %d, %Y') if billing.booking.date else 'N/A',
                    'service': billing.booking.service.name if billing.booking.service else 'General Consultation',
                    'service_fee': str(billing.service_fee),
                    'medicine_fee': str(billing.medicine_fee),
                    'total_amount': str(billing.total_amount),
                    'amount_paid': str(billing.amount_paid),
                    'balance': str(billing.balance),
                    'is_paid': billing.is_paid,
                    'issued_date': billing.issued_date.strftime('%B %d, %Y') if billing.issued_date else 'N/A',
                    'date_updated': billing.updated_at.isoformat() if billing.updated_at else '',
                })
            except Exception as e:
                # Skip this billing if there's an error
                print(f"Error processing billing {billing.id}: {str(e)}")
                continue
        
        return JsonResponse({
            'billings': billings_list,
            'count': len(billings_list)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@staff_member_required
@require_http_methods(["POST"])
def api_mark_billing_paid(request, billing_id):
    """
    API endpoint to mark a billing as paid
    """
    try:
        # Get the billing
        billing = Billing.objects.get(id=billing_id)
        
        # Calculate the payment amount (remaining balance)
        payment_amount = billing.balance
        
        # Mark as paid
        billing.amount_paid = billing.total_amount
        billing.balance = 0
        billing.is_paid = True
        billing.save()
        
        # Create a payment record
        Payment.objects.create(
            billing=billing,
            amount_paid=payment_amount,
            payment_method='cash',  # Default to cash, can be updated later
            reference_number=f'ADMIN-PAID-{billing_id}-{timezone.now().strftime("%Y%m%d%H%M%S")}',
            notes='Marked as paid by administrator'
        )
        
        # Calculate new outstanding balance
        new_outstanding_balance = Billing.objects.filter(
            is_paid=False
        ).aggregate(total=Sum('balance'))['total'] or 0
        
        return JsonResponse({
            'success': True,
            'message': 'Billing marked as paid successfully',
            'new_outstanding_balance': float(new_outstanding_balance)
        })
        
    except Billing.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Billing not found'
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
def api_update_billing_fees(request, billing_id):
    """Update service fee and medicine fee for a billing"""
    try:
        from decimal import Decimal
        
        data = json.loads(request.body)
        service_fee = data.get('service_fee')
        medicine_fee = data.get('medicine_fee')
        
        # Validate inputs
        if service_fee is None or medicine_fee is None:
            return JsonResponse({
                'success': False,
                'error': 'Both service fee and medicine fee are required'
            }, status=400)
        
        try:
            service_fee = Decimal(str(service_fee))
            medicine_fee = Decimal(str(medicine_fee))
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Invalid fee values'
            }, status=400)
        
        if service_fee < 0 or medicine_fee < 0:
            return JsonResponse({
                'success': False,
                'error': 'Fees cannot be negative'
            }, status=400)
        
        # Get the billing record
        billing = Billing.objects.get(id=billing_id, is_paid=False)
        
        # Update the fees
        billing.service_fee = service_fee
        billing.medicine_fee = medicine_fee
        billing.save()  # This will recalculate total_amount in the save() method
        
        # Recalculate balance based on payments
        billing.update_payment_status()
        
        # Calculate updated financial statistics
        all_billings = Billing.objects.all()
        
        total_billed = all_billings.aggregate(total=Sum('total_amount'))['total'] or 0
        total_paid = Payment.objects.aggregate(total=Sum('amount_paid'))['total'] or 0
        total_outstanding = all_billings.filter(is_paid=False).aggregate(total=Sum('balance'))['total'] or 0
        
        return JsonResponse({
            'success': True,
            'message': f'Billing fees updated successfully',
            'new_balance': float(billing.balance),
            'financial_stats': {
                'total_billed': float(total_billed),
                'total_paid': float(total_paid),
                'outstanding_balance': float(total_outstanding)
            }
        })
        
    except Billing.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Billing not found or already paid'
        }, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@staff_member_required
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


