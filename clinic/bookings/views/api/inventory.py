"""
API endpoints for inventory management
Handles inventory items and point-of-sale records
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from ...models import Inventory, POSSale


@login_required
@require_http_methods(["GET"])
def api_get_inventory(request):
    """Get all inventory items with stock levels"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to access this resource.'
        }, status=403)
    
    try:
        items = Inventory.objects.all().order_by('name')
        
        inventory_data = []
        for item in items:
            # Determine stock status
            if item.quantity <= item.reorder_level:
                stock_status = 'Low Stock'
                status_class = 'danger'
            elif item.quantity <= item.reorder_level * 2:
                stock_status = 'Medium Stock'
                status_class = 'warning'
            else:
                stock_status = 'Good Stock'
                status_class = 'success'
            
            inventory_data.append({
                'id': item.id,
                'name': item.name,
                'description': item.description or 'N/A',
                'quantity': item.quantity,
                'unit': item.unit,
                'reorder_level': item.reorder_level,
                'price': float(item.price) if item.price else 0.0,
                'stock_status': stock_status,
                'status_class': status_class,
                'last_updated': item.last_updated.strftime('%Y-%m-%d %H:%M'),
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


@login_required
@require_http_methods(["GET"])
def api_pos_sales(request):
    """Get all point-of-sale transactions"""
    # Check if user is staff
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to access this resource.'
        }, status=403)
    
    try:
        sales = POSSale.objects.select_related('cashier').prefetch_related('items__inventory').order_by('-sale_date')
        
        sales_data = []
        for sale in sales:
            # Get items for this sale
            items_list = []
            for item in sale.items.all():
                items_list.append({
                    'id': item.id,
                    'inventory_name': item.inventory.name,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'subtotal': float(item.subtotal),
                })
            
            sales_data.append({
                'id': sale.id,
                'receipt_number': sale.receipt_number,
                'sale_date': sale.sale_date.strftime('%Y-%m-%d %H:%M'),
                'total_amount': float(sale.total_amount),
                'payment_method': sale.get_payment_method_display(),
                'cashier': sale.cashier.get_full_name() if sale.cashier else 'N/A',
                'customer_name': sale.customer_name or 'Walk-in',
                'items': items_list,
                'items_count': len(items_list),
            })
        
        return JsonResponse({
            'success': True,
            'sales': sales_data,
            'count': len(sales_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
