"""
HTMX partial view for dashboard statistics refresh
Returns only the stats grid for auto-refresh functionality
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..decorators import staff_required
from datetime import date
from django.db.models import Q, Sum, Count, F
from django.db import models

from ..models import Billing, Booking, Patient, MedicalRecord, Inventory


@login_required
@staff_required
def htmx_dashboard_stats(request):
    """
    HTMX endpoint to refresh dashboard statistics
    Returns only the stats grid HTML for seamless updates
    """
    # Same calculations as admin_dashboard_v2 view
    total_appointments = Booking.objects.filter(status='Confirmed').count()
    total_bookings = Booking.objects.all().count()
    pending_bookings = Booking.objects.filter(status='Pending').count()
    confirmed_bookings = Booking.objects.filter(status='Confirmed').count()
    completed_bookings = Booking.objects.filter(status='Completed').count()
    today_bookings = Booking.objects.filter(
        date=date.today(),
        status__in=['Confirmed', 'Completed']
    ).count()
    
    total_medical_records = MedicalRecord.objects.count()
    total_patient_profiles = Patient.objects.count()
    
    total_inventory_items = Inventory.objects.count()
    low_stock_items = Inventory.objects.filter(
        quantity__lte=F('stock')
    ).count()
    out_of_stock_items = Inventory.objects.filter(quantity=0).count()
    
    total_billings = Billing.objects.count()
    paid_bills = Billing.objects.filter(is_paid=True).count()
    unpaid_bills = Billing.objects.filter(is_paid=False).count()
    partially_paid_bills = Billing.objects.filter(
        is_paid=False,
        amount_paid__gt=0
    ).count()
    
    total_revenue = Billing.objects.filter(is_paid=True).aggregate(
        total=Sum('amount_paid')
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
    }
    
    return render(request, 'bookings_v2/htmx_partials/dashboard_stats.html', context)


@login_required
@staff_required
def htmx_financial_overview(request):
    """
    HTMX endpoint to refresh financial overview and transaction summary
    Returns only the financial stats HTML for seamless updates
    """
    # Calculate financial statistics
    total_billings = Billing.objects.count()
    paid_bills = Billing.objects.filter(is_paid=True).count()
    unpaid_bills = Billing.objects.filter(is_paid=False).count()
    
    total_revenue = Billing.objects.filter(is_paid=True).aggregate(
        total=Sum('amount_paid')
    )['total'] or 0
    
    total_amount_billed = Billing.objects.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    total_balance_outstanding = Billing.objects.filter(is_paid=False).aggregate(
        total=Sum('balance')
    )['total'] or 0
    
    context = {
        'total_billings': total_billings,
        'paid_bills': paid_bills,
        'unpaid_bills': unpaid_bills,
        'total_revenue': total_revenue,
        'total_amount_billed': total_amount_billed,
        'total_balance_outstanding': total_balance_outstanding,
    }
    
    return render(request, 'bookings_v2/htmx_partials/financial_overview.html', context)
