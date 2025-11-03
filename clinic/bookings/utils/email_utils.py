"""
Email utility functions for sending notifications.
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_booking_confirmation_email(booking):
    """
    Send booking confirmation email to patient.
    
    Args:
        booking: Booking instance
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f'Booking Confirmation - {booking.service.name}'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = booking.patient.email
        
        # Render HTML email template
        html_content = render_to_string('emails/booking_confirmation.html', {
            'booking': booking,
            'patient': booking.patient,
            'service': booking.service,
        })
        
        # Create plain text version
        text_content = strip_tags(html_content)
        
        # Create email with both HTML and plain text versions
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[to_email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send(fail_silently=False)
        
        logger.info(f"Booking confirmation email sent to {to_email} for booking #{booking.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send booking confirmation email: {str(e)}")
        return False


def send_booking_status_update_email(booking, old_status, new_status):
    """
    Send email notification when booking status changes.
    
    Args:
        booking: Booking instance
        old_status: Previous status
        new_status: New status
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f'Booking Status Update - {booking.service.name}'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = booking.patient.email
        
        # Render HTML email template
        html_content = render_to_string('emails/booking_status_update.html', {
            'booking': booking,
            'patient': booking.patient,
            'service': booking.service,
            'old_status': old_status,
            'new_status': new_status,
        })
        
        # Create plain text version
        text_content = strip_tags(html_content)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[to_email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send(fail_silently=False)
        
        logger.info(f"Booking status update email sent to {to_email} for booking #{booking.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send booking status update email: {str(e)}")
        return False
