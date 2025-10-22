"""
Helper functions for common operations
Provides utility functions for calculations, queries, etc.
"""
from decimal import Decimal


def calculate_billing_total(service_fee=0, medicine_fee=0):
    """
    Calculate total billing amount from service and medicine fees
    
    Args:
        service_fee: Service fee amount (Decimal or float)
        medicine_fee: Medicine fee amount (Decimal or float)
        
    Returns:
        Decimal: Total amount
    """
    service_fee = Decimal(str(service_fee)) if service_fee else Decimal('0')
    medicine_fee = Decimal(str(medicine_fee)) if medicine_fee else Decimal('0')
    return service_fee + medicine_fee


def calculate_billing_balance(total_amount, amount_paid):
    """
    Calculate remaining balance for billing
    
    Args:
        total_amount: Total billing amount (Decimal or float)
        amount_paid: Amount already paid (Decimal or float)
        
    Returns:
        Decimal: Remaining balance
    """
    total = Decimal(str(total_amount)) if total_amount else Decimal('0')
    paid = Decimal(str(amount_paid)) if amount_paid else Decimal('0')
    return total - paid


def get_status_color(status, context='booking'):
    """
    Get color code for a given status and context
    
    Args:
        status: Status value (string)
        context: Context type - 'booking', 'consultation', 'payment', 'inventory', 'pos'
        
    Returns:
        str: Hex color code
    """
    color_schemes = {
        'booking': {
            'Pending': '#ffc107',
            'Confirmed': '#28a745',
            'Completed': '#17a2b8',
            'Cancelled': '#dc3545',
        },
        'consultation': {
            'Not Yet': '#6c757d',
            'Ongoing': '#ffc107',
            'Done': '#28a745',
        },
        'payment': {
            'Paid': '#28a745',
            'Partial': '#ffc107',
            'Unpaid': '#dc3545',
        },
        'inventory': {
            'In Stock': 'green',
            'Low Stock': 'orange',
            'Out of Stock': 'red',
        },
        'pos': {
            'Pending': '#ffc107',
            'Completed': '#28a745',
            'Cancelled': '#dc3545',
            'Refunded': '#6c757d',
        }
    }
    
    scheme = color_schemes.get(context, {})
    return scheme.get(status, '#6c757d')  # Default gray
