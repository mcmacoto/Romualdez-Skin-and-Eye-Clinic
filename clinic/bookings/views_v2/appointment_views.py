"""
Appointment and Booking Management Views for v2
Handles appointment lists, booking confirmations, and consultation status
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import date
import logging

from ..models import Booking, Service, Doctor
from ..decorators import staff_required
from ..utils.responses import htmx_error, htmx_success
from ..utils.email_utils import send_booking_confirmation_email, send_booking_status_update_email

logger = logging.getLogger(__name__)

@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_appointments_list(request):
    """Return HTML fragment of all appointments with optional search and filter"""
    
    # Get filter parameters
    filter_status = request.GET.get('status', 'all')
    filter_consultation = request.GET.get('consultation', 'all')
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    service_id = request.GET.get('service', '').strip()
    
    # Optimize query with select_related
    appointments = Booking.objects.select_related('service', 'created_by')
    
    # Handle search (multi-field)
    search_query = request.GET.get('search', '').strip()
    if search_query:
        appointments = appointments.filter(
            Q(patient_name__icontains=search_query) |
            Q(patient_email__icontains=search_query) |
            Q(patient_phone__icontains=search_query) |
            Q(service__name__icontains=search_query)
        )
        logger.info(f"Appointments search query: '{search_query}' by user {request.user.username}")
    
    # Apply date range filter
    if start_date:
        try:
            from datetime import datetime
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            appointments = appointments.filter(date__gte=start)
        except ValueError:
            pass
    
    if end_date:
        try:
            from datetime import datetime
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            appointments = appointments.filter(date__lte=end)
        except ValueError:
            pass
    
    # Apply service filter
    if service_id:
        try:
            appointments = appointments.filter(service_id=int(service_id))
        except ValueError:
            pass
    
    # Apply status filters
    if filter_status == 'confirmed':
        appointments = appointments.filter(status='Confirmed')
    elif filter_status == 'pending':
        appointments = appointments.filter(status='Pending')
    elif filter_status == 'completed':
        appointments = appointments.filter(status='Completed')
    elif filter_status == 'today':
        appointments = appointments.filter(date=date.today())
    
    # Apply consultation status filter
    if filter_consultation == 'done':
        appointments = appointments.filter(consultation_status='Done')
    elif filter_consultation == 'not_done':
        appointments = appointments.exclude(consultation_status='Done')
    
    # Handle column sorting
    sort_by = request.GET.get('sort', '').strip()
    sort_order = request.GET.get('order', 'asc').strip()
    
    # Define valid sort fields
    sort_fields = {
        'patient': 'patient_name',
        'date': 'date',
        'time': 'time',
        'service': 'service__name',
        'status': 'status',
    }
    
    if sort_by in sort_fields:
        field = sort_fields[sort_by]
        if sort_order == 'desc':
            field = f'-{field}'
        appointments = appointments.order_by(field)
    else:
        appointments = appointments.order_by('-date', '-time')
    
    # Add pagination (25 items per page)
    paginator = Paginator(appointments, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all available doctors for the dropdown
    available_doctors = Doctor.objects.filter(is_available=True).order_by('last_name', 'first_name')
    
    return render(request, 'bookings_v2/partials/appointments_list.html', {
        'appointments': page_obj,
        'paginator': paginator,
        'page_obj': page_obj,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'filter_consultation': filter_consultation,
        'available_doctors': available_doctors,
    })


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_mark_consultation_done(request, booking_id):
    """Mark consultation as done - returns updated HTML fragment"""
    
    try:
        booking = Booking.objects.select_related('service').get(id=booking_id)
        booking.consultation_status = 'Done'
        booking.status = 'Completed'
        booking.save()
        
        logger.info(f"Consultation marked as done for booking #{booking_id} by {request.user.username}")
        
        # Get available doctors for the dropdown in the response
        available_doctors = Doctor.objects.filter(is_available=True).order_by('last_name', 'first_name')
        
        # Return just the updated row
        response = render(request, 'bookings_v2/partials/appointment_row.html', {
            'appointment': booking,
            'available_doctors': available_doctors,
        })
        # Trigger both stats and financials refresh (new billing created)
        response['HX-Trigger'] = '{"refreshStats": {}, "refreshFinancials": {}}'
        return response
    except Booking.DoesNotExist:
        logger.warning(f"Attempted to mark non-existent booking #{booking_id} as done")
        return htmx_error("Booking not found", status=404)
    except Exception as e:
        logger.error(f"Error marking consultation done for booking #{booking_id}: {str(e)}", exc_info=True)
        return htmx_error("An error occurred while updating the consultation status")


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_update_consultation_status(request, booking_id):
    """Update consultation status via dropdown - returns updated row"""
    
    try:
        booking = Booking.objects.select_related('service').get(id=booking_id)
        new_status = request.POST.get('consultation_status')
        
        # Validate status
        valid_statuses = ['Not Yet', 'Ongoing', 'Done', 'No-Show']
        if new_status not in valid_statuses:
            logger.warning(f"Invalid consultation status '{new_status}' attempted for booking #{booking_id}")
            return htmx_error("Invalid status", status=400)
        
        booking.consultation_status = new_status
        
        # If marking as done, also mark booking as completed
        if new_status == 'Done':
            booking.status = 'Completed'
        # If marking as no-show, mark booking as cancelled
        elif new_status == 'No-Show':
            booking.status = 'Cancelled'
        
        booking.save()
        
        logger.info(f"Consultation status updated to '{new_status}' for booking #{booking_id} by {request.user.username}")
        
        # Get available doctors for the dropdown in the response
        available_doctors = Doctor.objects.filter(is_available=True).order_by('last_name', 'first_name')
        
        # Return just the updated row
        response = render(request, 'bookings_v2/partials/appointment_row.html', {
            'appointment': booking,
            'available_doctors': available_doctors,
        })
        # Trigger both stats and financials refresh (new billing created when status = Done)
        response['HX-Trigger'] = '{"refreshStats": {}, "refreshFinancials": {}}'
        return response
    except Booking.DoesNotExist:
        logger.warning(f"Attempted to update non-existent booking #{booking_id}")
        return htmx_error("Booking not found", status=404)
    except Exception as e:
        logger.error(f"Error updating consultation status for booking #{booking_id}: {str(e)}", exc_info=True)
        return htmx_error("An error occurred while updating the status")


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_update_appointment_doctor(request, booking_id):
    """Update appointment doctor via dropdown - returns updated row"""
    
    try:
        booking = Booking.objects.select_related('service', 'doctor').get(id=booking_id)
        doctor_id = request.POST.get('doctor')
        
        # If empty string, remove doctor assignment
        if not doctor_id:
            booking.doctor = None
            logger.info(f"Doctor removed from booking #{booking_id} by {request.user.username}")
        else:
            try:
                doctor = Doctor.objects.get(id=doctor_id, is_available=True)
                booking.doctor = doctor
                logger.info(f"Doctor '{doctor.get_full_name()}' assigned to booking #{booking_id} by {request.user.username}")
            except Doctor.DoesNotExist:
                logger.warning(f"Invalid doctor ID {doctor_id} for booking #{booking_id}")
                return htmx_error("Doctor not found or not available", status=400)
        
        booking.save()
        
        # Get available doctors for the dropdown in the response
        available_doctors = Doctor.objects.filter(is_available=True).order_by('last_name', 'first_name')
        
        # Return just the updated row
        return render(request, 'bookings_v2/partials/appointment_row.html', {
            'appointment': booking,
            'available_doctors': available_doctors,
        })
    except Booking.DoesNotExist:
        logger.warning(f"Attempted to update non-existent booking #{booking_id}")
        return htmx_error("Booking not found", status=404)
    except Exception as e:
        logger.error(f"Error updating doctor for booking #{booking_id}: {str(e)}", exc_info=True)
        return htmx_error("An error occurred while updating the doctor")


@login_required
@staff_required
@require_http_methods(["DELETE"])
def htmx_delete_appointment(request, booking_id):
    """Delete appointment - returns empty response to remove row"""
    
    try:
        booking = Booking.objects.get(id=booking_id)
        
        # Check if there are medical records associated (soft delete consideration)
        has_records = hasattr(booking, 'patient') and booking.patient and booking.patient.medicalrecord_set.exists()
        
        if has_records:
            # Soft delete: just mark as cancelled instead of hard delete
            booking.status = 'Cancelled'
            booking.save()
            logger.info(f"Booking #{booking_id} cancelled (has medical records) by {request.user.username}")
        else:
            # Hard delete: completely remove the appointment
            logger.info(f"Booking #{booking_id} deleted by {request.user.username}")
            booking.delete()
        
        # Return empty response - HTMX will swap and remove the row
        response = HttpResponse('', status=200)
        # Trigger dashboard stats refresh
        response['HX-Trigger'] = 'refreshStats'
        return response
        
    except Booking.DoesNotExist:
        logger.warning(f"Attempted to delete non-existent booking #{booking_id}")
        return htmx_error("Appointment not found", status=404)
    except Exception as e:
        logger.error(f"Error deleting booking #{booking_id}: {str(e)}", exc_info=True)
        return htmx_error("An error occurred while deleting the appointment")


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_pending_bookings(request):
    """HTMX endpoint to list all pending bookings"""
    
    pending_bookings = Booking.objects.filter(
        status='Pending'
    ).select_related('service').order_by('date', 'time')
    
    return render(request, 'bookings_v2/htmx_partials/pending_bookings.html', {
        'bookings': pending_bookings
    })


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_accept_booking(request, booking_id):
    """Accept a pending booking and create patient records"""
    try:
        booking = Booking.objects.get(id=booking_id, status='Pending')
        
        # Store old status for email
        old_status = booking.status
        
        # Update booking status to Confirmed
        booking.status = 'Confirmed'
        booking.save()  # This triggers signals that create Patient, MedicalRecord, Billing
        
        # Send confirmation email
        email_sent = send_booking_status_update_email(booking, old_status, 'Confirmed')
        if email_sent:
            logger.info(f"Confirmation email sent for booking #{booking_id}")
        
        # Return success message (row will be removed)
        response = HttpResponse(
            f'''<tr id="booking-row-{booking_id}">
                <td colspan="7" class="text-center py-3">
                    <div class="alert alert-success mb-0">
                        <i class="fas fa-check-circle"></i> 
                        Booking for <strong>{booking.patient_name}</strong> has been accepted! 
                        Patient records created automatically.
                        {' <small>(Confirmation email sent)</small>' if email_sent else ''}
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
        # Trigger dashboard stats refresh
        response['HX-Trigger'] = 'refreshStats'
        return response
        
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
@staff_required
@require_http_methods(["POST"])
def htmx_decline_booking(request, booking_id):
    """Decline a pending booking"""
    try:
        booking = Booking.objects.get(id=booking_id, status='Pending')
        patient_name = booking.patient_name
        
        # Update status to Cancelled (or delete if preferred)
        booking.status = 'Cancelled'
        booking.save()
        
        # Return success message (row will be removed)
        response = HttpResponse(
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
        # Trigger dashboard stats refresh
        response['HX-Trigger'] = 'refreshStats'
        return response
        
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


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_appointment_create_form(request):
    """Return HTML form for creating a new appointment"""
    from ..models import Doctor
    services = Service.objects.all()
    doctors = Doctor.objects.filter(is_available=True).order_by('last_name', 'first_name')
    return render(request, 'bookings_v2/htmx_partials/appointment_form.html', {
        'today': date.today().isoformat(),
        'services': services,
        'doctors': doctors
    })


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_appointment_create(request):
    """Create a new appointment"""
    try:
        from ..models import Doctor
        service_id = request.POST.get('service')
        service = Service.objects.get(id=service_id)
        
        # Get doctor if assigned
        doctor = None
        doctor_id = request.POST.get('doctor')
        if doctor_id:
            doctor = Doctor.objects.get(id=doctor_id)
        
        appointment = Booking.objects.create(
            patient_name=request.POST.get('name'),
            patient_email=request.POST.get('email'),
            patient_phone=request.POST.get('phone'),
            date=request.POST.get('date'),
            time=request.POST.get('time'),
            service=service,
            doctor=doctor,
            status=request.POST.get('status', 'Pending'),
            consultation_status='Not Yet'
        )
        
        messages.success(request, f'Appointment created for {appointment.patient_name}')
        
        # Return updated appointments list
        appointments = Booking.objects.select_related('service', 'doctor').order_by('-date', '-time')
        response = render(request, 'bookings_v2/partials/appointments_list.html', {
            'appointments': appointments
        })
        response['HX-Trigger'] = 'refreshStats'
        return response
        
    except Service.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Service not found</div>', status=400)
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)


@login_required
@staff_required
@require_http_methods(["GET"])
def htmx_appointment_edit_form(request, appointment_id):
    """Return HTML form for editing an appointment"""
    try:
        from ..models import Doctor
        appointment = Booking.objects.select_related('service', 'doctor').get(id=appointment_id)
        services = Service.objects.all()
        doctors = Doctor.objects.all().order_by('last_name', 'first_name')
        return render(request, 'bookings_v2/htmx_partials/appointment_form.html', {
            'appointment': appointment,
            'services': services,
            'doctors': doctors,
            'today': date.today().isoformat()
        })
    except Booking.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Appointment not found</div>', status=404)


@login_required
@staff_required
@require_http_methods(["POST"])
def htmx_appointment_update(request, appointment_id):
    """Update an existing appointment"""
    try:
        from ..models import Doctor
        appointment = Booking.objects.get(id=appointment_id)
        
        # Update service if provided
        service_id = request.POST.get('service')
        if service_id:
            appointment.service = Service.objects.get(id=service_id)
        
        # Update doctor if provided
        doctor_id = request.POST.get('doctor')
        if doctor_id:
            appointment.doctor = Doctor.objects.get(id=doctor_id)
        else:
            appointment.doctor = None
        
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
        appointments = Booking.objects.select_related('service', 'doctor').order_by('-date', '-time')
        response = render(request, 'bookings_v2/partials/appointments_list.html', {
            'appointments': appointments
        })
        response['HX-Trigger'] = 'refreshStats'
        return response
        
    except Booking.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Appointment not found</div>', status=404)
    except Service.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Service not found</div>', status=400)
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)
