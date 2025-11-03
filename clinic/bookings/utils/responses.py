"""
Utility functions for generating consistent HTTP responses
Especially useful for HTMX views
"""
from django.http import HttpResponse
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)


def htmx_error(message, status=400, icon="fa-exclamation-triangle"):
    """
    Generate a standardized HTMX error response with alert styling
    
    Args:
        message (str): Error message to display
        status (int): HTTP status code (default: 400)
        icon (str): FontAwesome icon class (default: fa-exclamation-triangle)
    
    Returns:
        HttpResponse: HTML response with error alert
    
    Example:
        return htmx_error("Invalid input data", status=400)
    """
    html = f'''
    <div class="alert alert-danger alert-dismissible fade show" role="alert">
        <i class="fas {icon}"></i> <strong>Error:</strong> {message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
    '''
    logger.debug(f"Returning error response: {message} (status: {status})")
    return HttpResponse(html.strip(), status=status)


def htmx_success(message, icon="fa-check-circle"):
    """
    Generate a standardized HTMX success response with alert styling
    
    Args:
        message (str): Success message to display
        icon (str): FontAwesome icon class (default: fa-check-circle)
    
    Returns:
        HttpResponse: HTML response with success alert
    
    Example:
        return htmx_success("Record created successfully!")
    """
    html = f'''
    <div class="alert alert-success alert-dismissible fade show" role="alert">
        <i class="fas {icon}"></i> <strong>Success:</strong> {message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
    '''
    logger.debug(f"Returning success response: {message}")
    return HttpResponse(html.strip())


def htmx_warning(message, icon="fa-exclamation-circle"):
    """
    Generate a standardized HTMX warning response with alert styling
    
    Args:
        message (str): Warning message to display
        icon (str): FontAwesome icon class (default: fa-exclamation-circle)
    
    Returns:
        HttpResponse: HTML response with warning alert
    
    Example:
        return htmx_warning("This action cannot be undone")
    """
    html = f'''
    <div class="alert alert-warning alert-dismissible fade show" role="alert">
        <i class="fas {icon}"></i> <strong>Warning:</strong> {message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
    '''
    logger.debug(f"Returning warning response: {message}")
    return HttpResponse(html.strip())


def htmx_info(message, icon="fa-info-circle"):
    """
    Generate a standardized HTMX info response with alert styling
    
    Args:
        message (str): Info message to display
        icon (str): FontAwesome icon class (default: fa-info-circle)
    
    Returns:
        HttpResponse: HTML response with info alert
    
    Example:
        return htmx_info("No records found")
    """
    html = f'''
    <div class="alert alert-info alert-dismissible fade show" role="alert">
        <i class="fas {icon}"></i> {message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
    '''
    logger.debug(f"Returning info response: {message}")
    return HttpResponse(html.strip())


def htmx_toast(message, type="success", duration=3000):
    """
    Generate a toast notification using Alpine.js
    
    Args:
        message (str): Message to display
        type (str): Toast type - success, error, warning, info
        duration (int): Duration in milliseconds before auto-dismiss
    
    Returns:
        HttpResponse: HTML response that triggers a toast
    
    Example:
        return htmx_toast("Saved successfully!", type="success")
    """
    icon_map = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-triangle',
        'warning': 'fa-exclamation-circle',
        'info': 'fa-info-circle',
    }
    
    icon = icon_map.get(type, 'fa-info-circle')
    
    html = f'''
    <div x-data="{{ show: true }}" 
         x-show="show" 
         x-init="setTimeout(() => show = false, {duration})"
         x-transition
         class="toast-notification toast-{type} position-fixed top-0 end-0 m-3" 
         style="z-index: 9999;">
        <div class="alert alert-{type} mb-0 shadow-lg">
            <i class="fas {icon}"></i> {message}
        </div>
    </div>
    '''
    return HttpResponse(html.strip())


def json_error(message, status=400, **extra_data):
    """
    Generate a JSON error response
    
    Args:
        message (str): Error message
        status (int): HTTP status code
        **extra_data: Additional data to include in response
    
    Returns:
        JsonResponse: JSON error response
    
    Example:
        return json_error("Invalid data", status=400, field="email")
    """
    from django.http import JsonResponse
    
    data = {
        'error': True,
        'message': message,
        **extra_data
    }
    logger.debug(f"Returning JSON error: {data} (status: {status})")
    return JsonResponse(data, status=status)


def json_success(message, **extra_data):
    """
    Generate a JSON success response
    
    Args:
        message (str): Success message
        **extra_data: Additional data to include in response
    
    Returns:
        JsonResponse: JSON success response
    
    Example:
        return json_success("Created", id=123, name="John")
    """
    from django.http import JsonResponse
    
    data = {
        'success': True,
        'message': message,
        **extra_data
    }
    logger.debug(f"Returning JSON success: {data}")
    return JsonResponse(data)
