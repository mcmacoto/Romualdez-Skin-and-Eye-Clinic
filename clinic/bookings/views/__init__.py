"""
Views package for bookings app
Organized into public views and booking views
"""
from .public_views import (
    landing,
    home,
    about,
    services,
    contact,
)
from .booking_views import (
    booking,
    booking_success,
)

__all__ = [
    # Public views
    'landing',
    'home',
    'about',
    'services',
    'contact',
    
    # Booking views
    'booking',
    'booking_success',
]
