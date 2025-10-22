"""
Formatting utilities for display purposes
Provides reusable formatters for currency, badges, colors, etc.
"""
from django.utils.html import format_html


def format_currency(amount):
    """
    Format a number as Philippine Peso currency
    
    Args:
        amount: Decimal or float value
        
    Returns:
        Formatted string like "₱1,234.56"
    """
    return f"₱{amount:,.2f}"


def format_status_badge(status, status_colors=None):
    """
    Generate a colored HTML badge for status display
    
    Args:
        status: The status text to display
        status_colors: Optional dict mapping status values to color codes
                      If not provided, uses default color scheme
                      
    Returns:
        SafeString with HTML badge markup
        
    Example:
        >>> format_status_badge('Pending', {'Pending': '#ffc107'})
        <span style="background-color: #ffc107; ...">Pending</span>
    """
    if status_colors is None:
        # Default color scheme
        status_colors = {
            'Pending': '#ffc107',
            'Confirmed': '#28a745',
            'Completed': '#28a745',
            'Done': '#28a745',
            'Cancelled': '#dc3545',
            'Refunded': '#6c757d',
            'Not Yet': '#6c757d',
            'Ongoing': '#ffc107',
            'Paid': '#28a745',
            'Partial': '#ffc107',
            'Unpaid': '#dc3545',
        }
    
    color = status_colors.get(status, '#6c757d')  # Default gray
    
    return format_html(
        '<span style="background-color: {}; color: white; padding: 3px 10px; '
        'border-radius: 3px; font-weight: bold;">{}</span>',
        color,
        status
    )


def format_colored_text(text, text_colors=None):
    """
    Generate colored text for display (without background)
    
    Args:
        text: The text to display
        text_colors: Optional dict mapping text values to color names
                    If not provided, uses default color scheme
                    
    Returns:
        SafeString with colored text markup
        
    Example:
        >>> format_colored_text('In Stock', {'In Stock': 'green'})
        <span style="color: green; ...">In Stock</span>
    """
    if text_colors is None:
        # Default color scheme
        text_colors = {
            'In Stock': 'green',
            'Low Stock': 'orange',
            'Out of Stock': 'red',
        }
    
    color = text_colors.get(text, 'black')  # Default black
    
    return format_html(
        '<span style="color: {}; font-weight: bold;">{}</span>',
        color,
        text
    )


def format_image_preview(image_url, max_width=200, max_height=200):
    """
    Generate HTML for image preview thumbnail
    
    Args:
        image_url: URL to the image
        max_width: Maximum width in pixels (default: 200)
        max_height: Maximum height in pixels (default: 200)
        
    Returns:
        SafeString with img tag markup
    """
    return format_html(
        '<img src="{}" style="max-width: {}px; max-height: {}px;" />',
        image_url,
        max_width,
        max_height
    )
