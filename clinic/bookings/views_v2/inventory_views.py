"""
Inventory and Point of Sale (POS) Management Views for v2
Handles inventory tracking, stock adjustments, and POS sales
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum
from datetime import datetime, date, timedelta
from decimal import Decimal

from ..models import Inventory, StockTransaction, POSSale, POSSaleItem, Patient


@login_required
@require_http_methods(["GET"])
def htmx_inventory_list(request):
    """Return HTML fragment of inventory items with optional search and filters"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    # Get filter parameters
    filter_status = request.GET.get('status', '')
    filter_category = request.GET.get('category', '')
    
    inventory_items = Inventory.objects.all()
    
    # Handle search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        inventory_items = inventory_items.filter(
            Q(name__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply status filters
    if filter_status == 'in_stock':
        inventory_items = inventory_items.filter(status='In Stock')
    elif filter_status == 'low_stock':
        inventory_items = inventory_items.filter(status='Low Stock')
    elif filter_status == 'out_of_stock':
        inventory_items = inventory_items.filter(status='Out of Stock')
    
    # Apply category filters
    if filter_category:
        inventory_items = inventory_items.filter(category=filter_category)
    
    inventory_items = inventory_items.order_by('name')
    
    # Calculate summary stats
    in_stock_count = Inventory.objects.filter(status='In Stock').count()
    low_stock_count = Inventory.objects.filter(status='Low Stock').count()
    out_of_stock_count = Inventory.objects.filter(status='Out of Stock').count()
    
    return render(request, 'bookings_v2/partials/inventory_list.html', {
        'inventory_items': inventory_items,
        'in_stock_count': in_stock_count,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'filter_status': filter_status,
        'filter_category': filter_category,
        'today': date.today(),
        'thirty_days_from_now': date.today() + timedelta(days=30)
    })


@login_required
@require_http_methods(["GET"])
def htmx_inventory_adjust(request, item_id):
    """Return HTML form for adjusting inventory stock"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        from django.urls import reverse
        item = Inventory.objects.get(item_id=item_id)
        adjust_url = reverse('bookings_v2:htmx_inventory_adjust_submit', args=[item_id])
        
        html = f'''
        <form hx-post="{adjust_url}" hx-swap="innerHTML" hx-target="#inventoryAdjustModalBody">
            <div class="mb-3">
                <h5>{item.name}</h5>
                <p class="text-muted">Current Stock: <strong>{item.quantity}</strong></p>
            </div>
            <div class="mb-3">
                <label class="form-label">Adjustment Type</label>
                <select class="form-select" name="adjustment_type" required>
                    <option value="add">Add Stock</option>
                    <option value="remove">Remove Stock</option>
                    <option value="set">Set Quantity</option>
                </select>
            </div>
            <div class="mb-3">
                <label class="form-label">Quantity</label>
                <input type="number" class="form-control" name="quantity" min="0" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Notes (Optional)</label>
                <textarea class="form-control" name="notes" rows="2"></textarea>
            </div>
            <div class="d-grid gap-2">
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-save"></i> Save Adjustment
                </button>
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                    Cancel
                </button>
            </div>
        </form>
        '''
        
        return HttpResponse(html)
    except Inventory.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Item not found</div>',
            status=404
        )


@login_required
@require_http_methods(["POST"])
def htmx_inventory_adjust_submit(request, item_id):
    """Process inventory adjustment with validation"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        from django.db import transaction
        
        with transaction.atomic():
            # Lock item to prevent concurrent adjustments
            item = Inventory.objects.select_for_update().get(item_id=item_id)
            adjustment_type = request.POST.get('adjustment_type')
            quantity = int(request.POST.get('quantity', 0))
            notes = request.POST.get('notes', '')
            
            # Validate quantity
            if quantity < 0:
                return HttpResponse(
                    '<div class="alert alert-danger">Quantity cannot be negative</div>',
                    status=400
                )
            
            # Store old quantity for transaction record
            old_quantity = item.quantity
            
            if adjustment_type == 'add':
                item.quantity += quantity
            elif adjustment_type == 'remove':
                # Validate sufficient stock before removing
                if item.quantity < quantity:
                    return HttpResponse(
                        f'<div class="alert alert-danger">Insufficient stock! Current: {item.quantity}, Requested: {quantity}</div>',
                        status=400
                    )
                item.quantity -= quantity
            elif adjustment_type == 'set':
                item.quantity = quantity
            else:
                return HttpResponse(
                    '<div class="alert alert-danger">Invalid adjustment type</div>',
                    status=400
                )
            
            # Save the item (status is auto-calculated in save method)
            item.save()
            
            # Create stock transaction record
            StockTransaction.objects.create(
                inventory_item=item,
                transaction_type='Stock In' if adjustment_type == 'add' else 'Stock Out',
                quantity=quantity,
                performed_by=request.user,
                notes=notes or f'{adjustment_type.capitalize()} stock adjustment'
            )
        
        return HttpResponse(
            f'''
            <div class="alert alert-success">
                <i class="fas fa-check-circle"></i> Stock adjusted successfully!
                <br>Previous: <strong>{old_quantity}</strong> → New: <strong>{item.quantity}</strong>
            </div>
            <script>
                setTimeout(() => {{
                    const modal = bootstrap.Modal.getInstance(document.getElementById('inventoryAdjustModal'));
                    if (modal) modal.hide();
                    // Refresh inventory list
                    htmx.trigger('#inventoryModalBody', 'inventoryUpdated');
                }}, 1500);
            </script>
            '''
        )
    except (Inventory.DoesNotExist, ValueError) as e:
        import traceback
        return HttpResponse(
            f'''<div class="alert alert-danger">
                <strong>Error:</strong> {str(e)}
                <br><small>{traceback.format_exc()}</small>
            </div>''',
            status=400
        )


@login_required
@require_http_methods(["GET"])
def htmx_inventory_create_form(request):
    """Return HTML form for creating a new inventory item"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    return render(request, 'bookings_v2/htmx_partials/inventory_form.html', {
        'today': date.today().isoformat()
    })


@login_required
@require_http_methods(["POST"])
def htmx_inventory_create(request):
    """Create a new inventory item"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', '').strip()
        price = request.POST.get('price', '0')
        quantity = request.POST.get('quantity', '0')
        stock = request.POST.get('stock', '0')
        expiry_date = request.POST.get('expiry_date', '').strip()
        
        # Validate required fields
        if not name or not description or not category:
            return HttpResponse('<div class="alert alert-danger">Name, description, and category are required</div>', status=400)
        
        # Convert numeric fields
        try:
            price = float(price)
            quantity = int(quantity)
            stock = int(stock)
        except ValueError:
            return HttpResponse('<div class="alert alert-danger">Invalid numeric values for price, quantity, or stock</div>', status=400)
        
        # Handle expiry date
        if expiry_date:
            expiry_date_obj = expiry_date
        else:
            expiry_date_obj = None
            
        # Create item
        item = Inventory.objects.create(
            name=name,
            description=description,
            category=category,
            price=price,
            quantity=quantity,
            stock=stock,
            expiry_date=expiry_date_obj
        )
        
        # Return updated inventory list with all stats
        inventory_items = Inventory.objects.all().order_by('name')
        in_stock_count = Inventory.objects.filter(status='In Stock').count()
        low_stock_count = Inventory.objects.filter(status='Low Stock').count()
        out_of_stock_count = Inventory.objects.filter(status='Out of Stock').count()
        
        return render(request, 'bookings_v2/partials/inventory_list.html', {
            'inventory_items': inventory_items,
            'in_stock_count': in_stock_count,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'filter_status': '',
            'filter_category': '',
            'today': date.today(),
            'thirty_days_from_now': date.today() + timedelta(days=30)
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return HttpResponse(f'<div class="alert alert-danger">Error creating item: {str(e)}<br><pre>{error_details}</pre></div>', status=400)


@login_required
@require_http_methods(["GET"])
def htmx_inventory_edit_form(request, item_id):
    """Return HTML form for editing an inventory item"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        item = Inventory.objects.get(item_id=item_id)
        return render(request, 'bookings_v2/htmx_partials/inventory_form.html', {
            'item': item,
            'today': date.today().isoformat()
        })
    except Inventory.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Inventory item not found</div>', status=404)


@login_required
@require_http_methods(["POST"])
def htmx_inventory_update(request, item_id):
    """Update an existing inventory item"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        item = Inventory.objects.get(item_id=item_id)
        
        # Get form data
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', '').strip()
        price = request.POST.get('price', '0')
        quantity = request.POST.get('quantity', '0')
        stock = request.POST.get('stock', '0')
        expiry_date = request.POST.get('expiry_date', '').strip()
        
        # Validate required fields
        if not name or not description or not category:
            return HttpResponse('<div class="alert alert-danger">Name, description, and category are required</div>', status=400)
        
        # Convert numeric fields
        try:
            price = float(price)
            quantity = int(quantity)
            stock = int(stock)
        except ValueError:
            return HttpResponse('<div class="alert alert-danger">Invalid numeric values for price, quantity, or stock</div>', status=400)
        
        # Update item
        item.name = name
        item.description = description
        item.category = category
        item.price = price
        item.quantity = quantity
        item.stock = stock
        item.expiry_date = expiry_date if expiry_date else None
        
        item.save()
        
        # Return updated inventory list with all stats
        inventory_items = Inventory.objects.all().order_by('name')
        in_stock_count = Inventory.objects.filter(status='In Stock').count()
        low_stock_count = Inventory.objects.filter(status='Low Stock').count()
        out_of_stock_count = Inventory.objects.filter(status='Out of Stock').count()
        
        return render(request, 'bookings_v2/partials/inventory_list.html', {
            'inventory_items': inventory_items,
            'in_stock_count': in_stock_count,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'filter_status': '',
            'filter_category': '',
            'today': date.today(),
            'thirty_days_from_now': date.today() + timedelta(days=30)
        })
        
    except Inventory.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Inventory item not found</div>', status=404)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return HttpResponse(f'<div class="alert alert-danger">Error updating item: {str(e)}<br><pre>{error_details}</pre></div>', status=400)


@login_required
@require_http_methods(["DELETE", "POST"])
def htmx_inventory_delete(request, item_id):
    """Delete an inventory item"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        item = Inventory.objects.get(item_id=item_id)
        item_name = item.name
        item.delete()
        
        # Return updated inventory list
        inventory_items = Inventory.objects.all().order_by('name')
        in_stock_count = Inventory.objects.filter(status='In Stock').count()
        low_stock_count = Inventory.objects.filter(status='Low Stock').count()
        out_of_stock_count = Inventory.objects.filter(status='Out of Stock').count()
        
        return render(request, 'bookings_v2/partials/inventory_list.html', {
            'inventory_items': inventory_items,
            'in_stock_count': in_stock_count,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'filter_status': '',
            'filter_category': '',
            'today': date.today(),
            'thirty_days_from_now': date.today() + timedelta(days=30)
        })
        
    except Inventory.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Inventory item not found</div>', status=404)
    except Exception as e:
        return HttpResponse(f'<div class="alert alert-danger">Error deleting item: {str(e)}</div>', status=400)


# ========================================
# STOCK TRANSACTION HISTORY
# ========================================

@login_required
@require_http_methods(["GET"])
def htmx_stock_transactions_list(request):
    """HTMX endpoint to list all stock transactions with filtering"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    # Get filter parameters
    transaction_type = request.GET.get('transaction_type', '')
    item_id = request.GET.get('item_id', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset
    transactions = StockTransaction.objects.select_related('inventory_item', 'performed_by').all()
    
    # Apply filters
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if item_id:
        transactions = transactions.filter(inventory_item__item_id=item_id)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            transactions = transactions.filter(transaction_date__date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            transactions = transactions.filter(transaction_date__date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Calculate summary stats
    total_count = transactions.count()
    stock_in_count = transactions.filter(transaction_type='Stock In').count()
    stock_out_count = transactions.filter(transaction_type='Stock Out').count()
    today_count = transactions.filter(transaction_date__date=date.today()).count()
    
    # Get all inventory items for filter dropdown
    inventory_items = Inventory.objects.all().order_by('name')
    
    context = {
        'transactions': transactions[:100],  # Limit to 100 most recent
        'total_count': total_count,
        'stock_in_count': stock_in_count,
        'stock_out_count': stock_out_count,
        'today_count': today_count,
        'inventory_items': inventory_items,
        'filter_type': transaction_type,
        'filter_item_id': item_id,
        'filter_date_from': date_from,
        'filter_date_to': date_to,
    }
    
    # If this is an HTMX request targeting just the table body, return only that
    if request.headers.get('HX-Target') == 'transactionsTableBody':
        return render(request, 'bookings_v2/partials/stock_transactions_table_body.html', context)
    
    return render(request, 'bookings_v2/partials/stock_transactions_list.html', context)


# ========================================
# POINT OF SALE (POS) SYSTEM
# ========================================

@login_required
@require_http_methods(["GET"])
def htmx_pos_interface(request):
    """POS Interface - Main sales screen"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    # Get or create pending sale for current user
    current_sale, created = POSSale.objects.get_or_create(
        created_by=request.user,
        status='Pending',
        defaults={'customer_name': 'Walk-in Customer'}
    )
    
    # Get available products (in stock only)
    products = Inventory.objects.filter(quantity__gt=0).order_by('name')
    
    # Get all patients for patient selection
    patients = Patient.objects.select_related('user').all()
    
    context = {
        'products': products,
        'current_sale': current_sale,
        'cart_items': current_sale.items.all(),
        'patients': patients,
    }
    
    return render(request, 'bookings_v2/partials/pos_interface.html', context)


@login_required
@require_http_methods(["GET"])
def htmx_pos_product_search(request):
    """Search/filter products for POS"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    
    # Base queryset - only in-stock items
    products = Inventory.objects.filter(quantity__gt=0)
    
    # Apply filters
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )
    
    if category:
        products = products.filter(category=category)
    
    products = products.order_by('name')
    
    context = {
        'products': products,
        'filter_category': category,
    }
    
    return render(request, 'bookings_v2/partials/pos_product_grid.html', context)


@login_required
@require_http_methods(["POST"])
def htmx_pos_add_to_cart(request, item_id):
    """Add product to cart"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        inventory_item = Inventory.objects.get(item_id=item_id)
        
        # Check stock
        if inventory_item.quantity <= 0:
            return HttpResponse(
                '<div class="alert alert-danger">Product out of stock</div>',
                status=400
            )
        
        # Get or create current sale
        current_sale, created = POSSale.objects.get_or_create(
            created_by=request.user,
            status='Pending',
            defaults={'customer_name': 'Walk-in Customer'}
        )
        
        # Check if item already in cart
        cart_item, created = POSSaleItem.objects.get_or_create(
            sale=current_sale,
            inventory_item=inventory_item,
            defaults={
                'quantity': 1,
                'unit_price': inventory_item.price
            }
        )
        
        if not created:
            # Item exists, increase quantity if stock allows
            if cart_item.quantity < inventory_item.quantity:
                cart_item.quantity += 1
                cart_item.save()
        
        # Get all patients for dropdown
        patients = Patient.objects.select_related('user').all()
        
        context = {
            'current_sale': current_sale,
            'cart_items': current_sale.items.all(),
            'patients': patients,
        }
        
        return render(request, 'bookings_v2/partials/pos_cart_items.html', context)
        
    except Inventory.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Product not found</div>',
            status=404
        )


@login_required
@require_http_methods(["POST"])
def htmx_pos_remove_from_cart(request, item_id):
    """Remove item from cart"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        cart_item = POSSaleItem.objects.get(id=item_id)
        current_sale = cart_item.sale
        cart_item.delete()
        
        patients = Patient.objects.select_related('user').all()
        
        context = {
            'current_sale': current_sale,
            'cart_items': current_sale.items.all(),
            'patients': patients,
        }
        
        return render(request, 'bookings_v2/partials/pos_cart_items.html', context)
        
    except POSSaleItem.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Item not found</div>', status=404)


@login_required
@require_http_methods(["POST"])
def htmx_pos_update_quantity(request, item_id):
    """Update cart item quantity"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        cart_item = POSSaleItem.objects.get(id=item_id)
        action = request.GET.get('action', 'increase')
        
        if action == 'increase':
            if cart_item.quantity < cart_item.inventory_item.quantity:
                cart_item.quantity += 1
                cart_item.save()
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
        
        current_sale = cart_item.sale
        patients = Patient.objects.select_related('user').all()
        
        context = {
            'current_sale': current_sale,
            'cart_items': current_sale.items.all(),
            'patients': patients,
        }
        
        return render(request, 'bookings_v2/partials/pos_cart_items.html', context)
        
    except POSSaleItem.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Item not found</div>', status=404)


@login_required
@require_http_methods(["POST"])
def htmx_pos_update_discount(request, sale_id):
    """Update sale discount"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    try:
        current_sale = POSSale.objects.get(id=sale_id, status='Pending')
        discount_percent = float(request.POST.get('discount_percent', 0))
        
        # Validate discount
        if 0 <= discount_percent <= 100:
            current_sale.discount_percent = discount_percent
            current_sale.save()
            
            return JsonResponse({
                'success': True,
                'discount_percent': current_sale.discount_percent,
                'discount_amount': float(current_sale.discount_amount),
                'total_amount': float(current_sale.total_amount),
                'subtotal': float(current_sale.subtotal)
            })
        else:
            return JsonResponse({'success': False, 'error': 'Invalid discount'}, status=400)
        
    except POSSale.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Sale not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def htmx_pos_complete_sale(request, sale_id):
    """Complete the sale and generate receipt"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        current_sale = POSSale.objects.get(id=sale_id, status='Pending')
        
        # Validate cart not empty
        if not current_sale.items.exists():
            return HttpResponse(
                '<div class="alert alert-danger">Cannot complete sale with empty cart</div>',
                status=400
            )
        
        # Update customer info
        sale_type = request.POST.get('sale_type', 'Walk-in')
        current_sale.sale_type = sale_type
        
        if sale_type == 'Patient':
            patient_id = request.POST.get('patient_id')
            if patient_id:
                try:
                    patient = Patient.objects.get(id=patient_id)
                    current_sale.patient = patient
                    # Use full name if available, otherwise username
                    full_name = patient.user.get_full_name()
                    customer_name = full_name if full_name.strip() else patient.user.username
                    current_sale.customer_name = customer_name
                except Patient.DoesNotExist:
                    current_sale.customer_name = request.POST.get('customer_name', 'Walk-in Customer')
            else:
                current_sale.customer_name = 'Walk-in Customer'
        else:
            customer_name = request.POST.get('customer_name', '').strip()
            if not customer_name:
                return HttpResponse(
                    '<div class="alert alert-danger">Customer name is required</div>',
                    status=400
                )
            current_sale.customer_name = customer_name
        
        # Update payment info
        current_sale.payment_method = request.POST.get('payment_method', 'Cash')
        
        # Update discount if provided
        discount_percent = request.POST.get('discount_percent', '')
        if discount_percent:
            try:
                current_sale.discount_percent = Decimal(str(discount_percent))
            except (ValueError, TypeError):
                pass
        
        try:
            amount_received = request.POST.get('amount_received', '')
            if amount_received:
                current_sale.amount_received = Decimal(str(amount_received))
            else:
                current_sale.amount_received = current_sale.total_amount
        except (ValueError, TypeError):
            current_sale.amount_received = current_sale.total_amount
        
        current_sale.reference_number = request.POST.get('reference_number', '')
        
        # Save first to update all calculations
        current_sale.save()
        
        # Now mark as completed and save again - this will trigger inventory deduction
        current_sale.status = 'Completed'
        current_sale.save()
        
        # Deduct inventory manually for each item
        for item in current_sale.items.all():
            # Deduct from inventory
            if item.inventory_item.quantity >= item.quantity:
                item.inventory_item.quantity -= item.quantity
                item.inventory_item.save()
                
                # Create stock transaction
                try:
                    StockTransaction.objects.create(
                        inventory_item=item.inventory_item,
                        transaction_type='Stock Out',
                        quantity=item.quantity,
                        performed_by=request.user,
                        notes=f"POS Sale - Receipt #{current_sale.receipt_number}"
                    )
                except Exception:
                    # Silently continue if stock transaction creation fails
                    pass
        
        # Generate receipt HTML
        receipt_html = f'''
        <div class="text-center">
            <div class="alert alert-success">
                <i class="fas fa-check-circle fa-3x mb-3"></i>
                <h4>Sale Completed!</h4>
                <p class="mb-0">Receipt: <strong>#{current_sale.receipt_number}</strong></p>
            </div>
            
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">Receipt #{current_sale.receipt_number}</h5>
                    <hr>
                    <p class="mb-1"><strong>Customer:</strong> {current_sale.customer_name}</p>
                    <p class="mb-1"><strong>Date:</strong> {current_sale.sale_date.strftime("%B %d, %Y %I:%M %p")}</p>
                    <p class="mb-3"><strong>Payment:</strong> {current_sale.payment_method}</p>
                    
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Item</th>
                                <th class="text-end">Qty</th>
                                <th class="text-end">Price</th>
                                <th class="text-end">Total</th>
                            </tr>
                        </thead>
                        <tbody>
        '''
        
        for item in current_sale.items.all():
            receipt_html += f'''
                            <tr>
                                <td>{item.inventory_item.name}</td>
                                <td class="text-end">{item.quantity}</td>
                                <td class="text-end">₱{item.unit_price}</td>
                                <td class="text-end">₱{item.line_total}</td>
                            </tr>
            '''
        
        receipt_html += f'''
                        </tbody>
                    </table>
                    
                    <hr>
                    <div class="d-flex justify-content-between mb-1">
                        <span>Subtotal:</span>
                        <strong>₱{current_sale.subtotal}</strong>
                    </div>
        '''
        
        if current_sale.discount_amount > 0:
            receipt_html += f'''
                    <div class="d-flex justify-content-between mb-1 text-success">
                        <span>Discount ({current_sale.discount_percent}%):</span>
                        <strong>-₱{current_sale.discount_amount}</strong>
                    </div>
            '''
        
        receipt_html += f'''
                    <div class="d-flex justify-content-between mb-2">
                        <h5>Total:</h5>
                        <h5 class="text-primary">₱{current_sale.total_amount}</h5>
                    </div>
                    
                    <div class="d-flex justify-content-between mb-1">
                        <span>Amount Received:</span>
                        <strong>₱{current_sale.amount_received}</strong>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span>Change:</span>
                        <strong>₱{current_sale.change_amount}</strong>
                    </div>
                </div>
            </div>
            
            <div class="d-grid gap-2">
                <button 
                    class="btn btn-primary"
                    onclick="window.print()"
                >
                    <i class="fas fa-print"></i> Print Receipt
                </button>
                <button 
                    class="btn btn-success"
                    hx-get="/admin/htmx/pos/"
                    hx-target="#posModalBody"
                    hx-swap="innerHTML"
                >
                    <i class="fas fa-plus"></i> New Sale
                </button>
                <button 
                    class="btn btn-outline-secondary"
                    hx-get="/admin/htmx/pos-sales/"
                    hx-target="#posModalBody"
                    hx-swap="innerHTML"
                >
                    <i class="fas fa-list"></i> View All Sales
                </button>
            </div>
        </div>
        '''
        
        return HttpResponse(receipt_html)
        
    except (POSSale.DoesNotExist, Patient.DoesNotExist, ValueError) as e:
        import traceback
        return HttpResponse(
            f'''<div class="alert alert-danger">
                <strong>Error:</strong> {str(e)}
                <br><small>{traceback.format_exc()}</small>
            </div>''',
            status=400
        )


@login_required
@require_http_methods(["POST"])
def htmx_pos_cancel_sale(request, sale_id):
    """Cancel current sale"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        current_sale = POSSale.objects.get(id=sale_id, status='Pending')
        current_sale.status = 'Cancelled'
        current_sale.save()
        
        # Create new pending sale
        new_sale = POSSale.objects.create(
            created_by=request.user,
            customer_name='Walk-in Customer',
            status='Pending'
        )
        
        patients = Patient.objects.select_related('user').all()
        
        context = {
            'current_sale': new_sale,
            'cart_items': [],
            'patients': patients,
        }
        
        return render(request, 'bookings_v2/partials/pos_cart.html', context)
        
    except POSSale.DoesNotExist:
        return HttpResponse('<div class="alert alert-danger">Sale not found</div>', status=404)


@login_required
@require_http_methods(["GET"])
def htmx_pos_sales_list(request):
    """List all POS sales with filtering"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    # Get filter parameters
    status = request.GET.get('status', '')
    payment_method = request.GET.get('payment_method', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset - exclude pending sales
    sales = POSSale.objects.exclude(status='Pending').select_related('patient__user', 'created_by').order_by('-sale_date')
    
    # Apply filters
    if status:
        sales = sales.filter(status=status)
    
    if payment_method:
        sales = sales.filter(payment_method=payment_method)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            sales = sales.filter(sale_date__date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            sales = sales.filter(sale_date__date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Calculate summary stats
    today = date.today()
    today_sales = POSSale.objects.filter(status='Completed', sale_date__date=today)
    today_count = today_sales.count()
    today_revenue = today_sales.aggregate(total=Sum('total_amount'))['total'] or 0
    
    month_start = today.replace(day=1)
    month_sales = POSSale.objects.filter(status='Completed', sale_date__date__gte=month_start)
    month_count = month_sales.count()
    month_revenue = month_sales.aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'sales': sales[:100],  # Limit to 100 most recent
        'total_count': sales.count(),
        'today_count': today_count,
        'today_revenue': today_revenue,
        'month_count': month_count,
        'month_revenue': month_revenue,
        'filter_status': status,
        'filter_payment': payment_method,
        'filter_date_from': date_from,
        'filter_date_to': date_to,
    }
    
    # If HTMX targeting just table body
    if request.headers.get('HX-Target') == 'salesTableBody':
        return render(request, 'bookings_v2/partials/pos_sales_table_body.html', context)
    
    return render(request, 'bookings_v2/partials/pos_sales_list.html', context)


@login_required
@require_http_methods(["GET"])
def htmx_pos_sale_detail(request, sale_id):
    """View detailed receipt for a sale"""
    if not request.user.is_staff:
        return HttpResponse('<div class="alert alert-danger">Permission denied</div>', status=403)
    
    try:
        sale = POSSale.objects.get(id=sale_id)
        
        context = {
            'sale': sale,
            'items': sale.items.all()
        }
        
        return render(request, 'bookings_v2/partials/pos_sale_detail.html', context)
        
    except POSSale.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Sale not found</div>',
            status=404
        )
