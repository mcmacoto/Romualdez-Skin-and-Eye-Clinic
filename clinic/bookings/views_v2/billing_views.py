"""
Billing and Payment Management Views for v2
Handles billing lists, payment recording, and financial operations
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q

from ..models import Billing, Payment


@login_required
@require_http_methods(["GET"])
def htmx_unpaid_patients(request):
    """Return HTML fragment of unpaid patients for HTMX"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    unpaid_billings = Billing.objects.filter(
        is_paid=False
    ).select_related('booking__service').order_by('-issued_date')
    
    return render(request, 'bookings_v2/partials/unpaid_patients.html', {
        'unpaid_billings': unpaid_billings
    })


@login_required
@require_http_methods(["GET"])
def htmx_all_billings(request):
    """Return HTML fragment of all billings for HTMX with optional search"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    billings = Billing.objects.select_related('booking__service')
    
    # Handle search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        billings = billings.filter(
            Q(booking__patient_name__icontains=search_query) |
            Q(booking__patient_email__icontains=search_query) |
            Q(booking__service__name__icontains=search_query)
        )
    
    billings = billings.order_by('-issued_date')
    
    # Calculate summary statistics
    total_count = billings.count()
    paid_count = billings.filter(is_paid=True).count()
    unpaid_count = billings.filter(is_paid=False, amount_paid=0).count()
    partial_count = billings.filter(is_paid=False, amount_paid__gt=0).count()
    
    total_revenue = sum(b.total_amount for b in billings)
    amount_collected = sum(b.amount_paid for b in billings)
    outstanding_balance = sum(b.balance for b in billings)
    
    return render(request, 'bookings_v2/partials/all_billings_list.html', {
        'billings': billings,
        'total_count': total_count,
        'paid_count': paid_count,
        'unpaid_count': unpaid_count,
        'partial_count': partial_count,
        'total_revenue': total_revenue,
        'amount_collected': amount_collected,
        'outstanding_balance': outstanding_balance,
    })


@login_required
@require_http_methods(["POST"])
def htmx_mark_paid(request, billing_id):
    """Mark billing as paid - returns updated HTML fragment"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        billing = Billing.objects.get(id=billing_id)
        billing.is_paid = True
        billing.amount_paid = billing.total_amount
        billing.balance = 0
        billing.save()
        
        # Return success message to replace the row
        return HttpResponse(
            '<div class="alert alert-success alert-dismissible fade show" role="alert">'
            f'✓ Billing for {billing.booking.patient_name} marked as paid!'
            '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>'
            '</div>'
        )
    except Billing.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Billing not found</div>',
            status=404
        )


@login_required
@require_http_methods(["GET"])
def htmx_paid_billings(request):
    """Return HTML fragment of paid billings"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    billings = Billing.objects.select_related(
        'booking__service'
    ).filter(is_paid=True).order_by('-issued_date')
    
    return render(request, 'bookings_v2/partials/all_billings_list.html', {
        'billings': billings
    })


@login_required
@require_http_methods(["GET"])
def htmx_unpaid_billings(request):
    """Return HTML fragment of unpaid billings"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    billings = Billing.objects.select_related(
        'booking__service'
    ).filter(is_paid=False).order_by('-issued_date')
    
    return render(request, 'bookings_v2/partials/all_billings_list.html', {
        'billings': billings
    })


@login_required
@require_http_methods(["GET"])
def htmx_payment_create_form(request):
    """Return HTML form for recording a new payment"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    # Get unpaid billings
    unpaid_billings = Billing.objects.filter(
        Q(is_paid=False) | Q(balance__gt=0)
    ).select_related('booking').order_by('-issued_date')[:50]
    
    return render(request, 'bookings_v2/htmx_partials/payment_form.html', {
        'unpaid_billings': unpaid_billings
    })


@login_required
@require_http_methods(["POST"])
def htmx_payment_create(request):
    """Record a new payment"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        billing_id = request.POST.get('billing_id')
        billing = Billing.objects.get(id=billing_id)
        
        # Create payment
        payment = Payment.objects.create(
            billing=billing,
            amount_paid=request.POST.get('amount_paid'),
            payment_method=request.POST.get('payment_method'),
            reference_number=request.POST.get('reference_number', ''),
            notes=request.POST.get('notes', ''),
            recorded_by=request.user
        )
        
        messages.success(request, f'Payment of ₱{payment.amount_paid} recorded successfully')
        
        # Return updated billings list
        billings = Billing.objects.select_related('booking').order_by('-issued_date')[:50]
        return render(request, 'bookings_v2/partials/billings_list.html', {
            'billings': billings
        })
        
    except Billing.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Billing record not found</div>', status=404)
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=400)
