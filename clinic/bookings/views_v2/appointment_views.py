"""
Appointment and Booking Management Views for v2
Handles appointment lists, booking confirmations, and consultation status
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q
from datetime import date

from ..models import Booking, Service


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
