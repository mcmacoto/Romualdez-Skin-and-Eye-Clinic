"""
Activity logging utility functions.
"""
from ..models import ActivityLog
import logging

logger = logging.getLogger(__name__)


def log_activity(user, action, model_name, object_id=None, description='', request=None):
    """
    Log a user activity.
    
    Args:
        user: User instance or None
        action: Action type (CREATE, UPDATE, DELETE, etc.)
        model_name: Name of the model (e.g., 'Booking', 'Patient')
        object_id: ID of the affected object
        description: Human-readable description
        request: Django request object (for IP address)
    """
    try:
        ip_address = None
        if request:
            # Get IP address from request
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
        
        ActivityLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            description=description,
            ip_address=ip_address
        )
        
        logger.info(f"Activity logged: {user} - {action} {model_name} #{object_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to log activity: {str(e)}", exc_info=True)
        return False


# Convenience functions for common actions
def log_create(user, model_name, object_id, description='', request=None):
    """Log a CREATE action"""
    return log_activity(user, 'CREATE', model_name, object_id, description, request)


def log_update(user, model_name, object_id, description='', request=None):
    """Log an UPDATE action"""
    return log_activity(user, 'UPDATE', model_name, object_id, description, request)


def log_delete(user, model_name, object_id, description='', request=None):
    """Log a DELETE action"""
    return log_activity(user, 'DELETE', model_name, object_id, description, request)


def log_payment(user, model_name, object_id, description='', request=None):
    """Log a PAYMENT action"""
    return log_activity(user, 'PAYMENT', model_name, object_id, description, request)


def log_login(user, description='User logged in', request=None):
    """Log a LOGIN action"""
    return log_activity(user, 'LOGIN', 'User', user.id if user else None, description, request)


def log_logout(user, description='User logged out', request=None):
    """Log a LOGOUT action"""
    return log_activity(user, 'LOGOUT', 'User', user.id if user else None, description, request)
