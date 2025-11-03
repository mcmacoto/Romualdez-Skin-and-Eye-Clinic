"""
Authentication and Dashboard Views
Handles user authentication (login/logout) and dashboard pages
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from ..decorators import staff_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from datetime import date, timedelta
from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncMonth
import json

from ..models import Billing, Booking, Patient, MedicalRecord, Inventory, POSSale


def landing_v2(request):
    """Landing page - Portal selection"""
    # If user is already logged in, redirect appropriately
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('bookings_v2:admin_dashboard')
        else:
            return redirect('bookings_v2:home')
    return render(request, 'bookings_v2/landing_v2.html')


def login_v2(request):
    """Patient login"""
    if request.user.is_authenticated:
        # Redirect staff to dashboard, patients to home
        if request.user.is_staff:
            return redirect('bookings_v2:admin_dashboard')
        return redirect('bookings_v2:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Don't allow staff to login through patient portal
            if user.is_staff:
                messages.error(request, 'Staff members must use the Staff Portal.')
                return redirect('bookings_v2:staff_login')
            
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('bookings_v2:home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'bookings_v2/login_v2.html')


def staff_login_v2(request):
    """Staff login - redirects to admin dashboard"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('bookings_v2:admin_dashboard')
        else:
            messages.warning(request, 'You do not have staff access.')
            return redirect('bookings_v2:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Only allow staff members
            if not user.is_staff:
                messages.error(request, 'Access denied. Staff credentials required.')
                return render(request, 'bookings_v2/staff_login_v2.html')
            
            login(request, user)
            messages.success(request, f'Welcome, {user.get_full_name() or user.username}!')
            return redirect('bookings_v2:admin_dashboard')
        else:
            messages.error(request, 'Invalid staff credentials.')
    
    return render(request, 'bookings_v2/staff_login_v2.html')


def logout_v2(request):
    """Logout and redirect to landing"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('bookings_v2:landing')


@login_required(login_url='bookings_v2:login')
def patient_dashboard_v2(request):
    """Patient Dashboard - Shows patient's own appointments, records, and billing"""
    # Prevent staff from accessing patient portal
    if request.user.is_staff:
        messages.warning(request, 'Staff should use the Admin Dashboard.')
        return redirect('bookings_v2:admin_dashboard')
    
    # Check if user has a patient profile
    has_profile = hasattr(request.user, 'patient_profile')
    patient = None
    
    if has_profile:
        try:
            patient = request.user.patient_profile
        except Patient.DoesNotExist:
            has_profile = False
    
    # Get patient's bookings by email - works even without Patient profile
    bookings = Booking.objects.filter(
        patient_email=request.user.email
    ).select_related('service').order_by('-date', '-time')
    
    upcoming_bookings = bookings.filter(
        date__gte=date.today(),
        status__in=['Pending', 'Confirmed']
    )
    
    past_bookings = bookings.filter(
        Q(date__lt=date.today()) | Q(status='Completed')
    ).exclude(status='Cancelled')
    
    # Initialize profile-specific data
    medical_records = MedicalRecord.objects.none()
    billings = Billing.objects.none()
    pos_sales = POSSale.objects.none()
    unpaid_bills = Billing.objects.none()
    booking_outstanding = 0
    
    # Only fetch patient-specific records if profile exists
    if has_profile and patient:
        # Get medical records
        medical_records = MedicalRecord.objects.filter(
            patient=patient
        ).order_by('-visit_date')
        
        # Get billing information from bookings
        billings = Billing.objects.filter(
            booking__patient_email=request.user.email
        ).select_related('booking__service').order_by('-issued_date')
        
        # Get POS sales for this patient
        pos_sales = POSSale.objects.filter(
            patient=patient
        ).order_by('-sale_date')
        
        # Calculate outstanding balance from bookings
        unpaid_bills = billings.filter(is_paid=False)
        booking_outstanding = unpaid_bills.aggregate(total=Sum('balance'))['total'] or 0
    
    # Calculate total outstanding including unpaid POS sales (if any are unpaid)
    # For now, POS sales are paid immediately, but we'll include for completeness
    total_outstanding = booking_outstanding
    
    context = {
        'has_profile': has_profile,
        'patient': patient,
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'total_bookings': bookings.count(),
        'medical_records': medical_records,
        'total_records': medical_records.count(),
        'billings': billings,
        'pos_sales': pos_sales,
        'unpaid_bills': unpaid_bills,
        'total_outstanding': total_outstanding,
    }
    
    return render(request, 'bookings_v2/patient_dashboard_v2.html', context)


@login_required(login_url='bookings_v2:staff_login')
@staff_required
def admin_dashboard_v2(request):
    """Admin Dashboard - V2 with Bootstrap/HTMX/Alpine - Staff Only"""
    
    # Get statistics - Total Appointments shows bookings with consultation_status "Not Yet" or "Ongoing"
    total_appointments = Booking.objects.filter(
        status='Confirmed',
        consultation_status__in=['Not Yet', 'Ongoing']
    ).count()
    
    # Booking statistics
    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status='Pending').count()
    confirmed_bookings = Booking.objects.filter(status='Confirmed').count()
    completed_bookings = Booking.objects.filter(status='Completed').count()
    today_bookings = Booking.objects.filter(date=date.today()).count()
    
    # Patient and medical records statistics
    total_medical_records = MedicalRecord.objects.count()
    total_patient_profiles = Patient.objects.count()
    
    # Inventory statistics
    total_inventory_items = Inventory.objects.count()
    low_stock_items = Inventory.objects.filter(status='Low Stock').count()
    out_of_stock_items = Inventory.objects.filter(status='Out of Stock').count()
    
    # Billing statistics
    total_billings = Billing.objects.count()
    paid_bills = Billing.objects.filter(is_paid=True).count()
    unpaid_bills = Billing.objects.filter(is_paid=False).count()
    partially_paid_bills = Billing.objects.filter(is_paid=False, amount_paid__gt=0).count()
    
    total_revenue = Billing.objects.filter(is_paid=True).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    total_amount_billed = Billing.objects.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    total_amount_paid = Billing.objects.aggregate(
        total=Sum('amount_paid')
    )['total'] or 0
    
    total_balance_outstanding = Billing.objects.filter(is_paid=False).aggregate(
        total=Sum('balance')
    )['total'] or 0
    
    # Chart Data - Monthly Appointments (Last 6 months)
    six_months_ago = date.today() - timedelta(days=180)
    monthly_appointments = Booking.objects.filter(
        date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Format for Chart.js
    months_labels = [item['month'].strftime('%B %Y') for item in monthly_appointments]
    months_data = [item['count'] for item in monthly_appointments]
    
    # Chart Data - Services Distribution
    from ..models import Service
    services_distribution = Service.objects.annotate(
        booking_count=Count('bookings')  # Note: 'bookings' is the related name
    ).order_by('-booking_count')[:6]  # Top 6 services
    
    services_labels = [service.name for service in services_distribution]
    services_data = [service.booking_count for service in services_distribution]
    
    context = {
        'total_appointments': total_appointments,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'confirmed_bookings': confirmed_bookings,
        'completed_bookings': completed_bookings,
        'today_bookings': today_bookings,
        'total_medical_records': total_medical_records,
        'total_patient_profiles': total_patient_profiles,
        'total_inventory_items': total_inventory_items,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
        'total_billings': total_billings,
        'paid_bills': paid_bills,
        'unpaid_bills': unpaid_bills,
        'partially_paid_bills': partially_paid_bills,
        'total_revenue': total_revenue,
        'total_amount_billed': total_amount_billed,
        'total_amount_paid': total_amount_paid,
        'total_balance_outstanding': total_balance_outstanding,
        # Chart data (JSON serialized for JavaScript)
        'months_labels_json': json.dumps(months_labels),
        'months_data_json': json.dumps(months_data),
        'services_labels_json': json.dumps(services_labels),
        'services_data_json': json.dumps(services_data),
    }
    
    return render(request, 'bookings_v2/admin_dashboard_v2.html', context)
