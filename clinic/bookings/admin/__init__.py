"""
Admin package for bookings app
Imports and registers all admin classes with custom admin site
"""
from django.contrib import admin
from django.contrib.auth.models import User, Group

# Import base components
from .base import (
    ClinicAdminSite, 
    CustomModelAdmin, 
    RestrictedUserAdmin,
    GroupAdmin
)

# Import appointment admin classes
from .appointments import (
    AppointmentAdmin,
    ServiceAdmin,
    BookingAdmin
)

# Import patient admin classes
from .patients import (
    PatientAdmin,
    MedicalRecordAdmin,
    MedicalImageAdmin,
    MedicalImageInline,
    PrescriptionInline
)

# Import billing admin classes
from .billing import (
    BillingAdmin,
    PaymentAdmin,
    PaymentInline
)

# Import inventory admin classes
from .inventory import (
    InventoryAdmin,
    InventoryAdminForm,
    StockTransactionAdmin,
    PrescriptionAdmin
)

# Import POS admin classes
from .pos import (
    POSSaleAdmin,
    POSSaleItemAdmin,
    POSSaleItemInline
)

# Import models
from ..models import (
    Appointment, Service, Patient, MedicalRecord, MedicalImage, 
    Inventory, StockTransaction, Booking, Billing, Payment, Prescription,
    POSSale, POSSaleItem
)


# Create custom admin site instance
clinic_admin_site = ClinicAdminSite(name='clinic_admin')

# Register models with custom admin site
clinic_admin_site.register(User, RestrictedUserAdmin)
clinic_admin_site.register(Group, GroupAdmin)
clinic_admin_site.register(Appointment, AppointmentAdmin)
clinic_admin_site.register(Service, ServiceAdmin)
clinic_admin_site.register(Patient, PatientAdmin)
clinic_admin_site.register(MedicalRecord, MedicalRecordAdmin)
clinic_admin_site.register(MedicalImage, MedicalImageAdmin)
clinic_admin_site.register(Inventory, InventoryAdmin)
clinic_admin_site.register(StockTransaction, StockTransactionAdmin)
clinic_admin_site.register(Booking, BookingAdmin)
clinic_admin_site.register(Billing, BillingAdmin)
clinic_admin_site.register(Payment, PaymentAdmin)
clinic_admin_site.register(Prescription, PrescriptionAdmin)
clinic_admin_site.register(POSSale, POSSaleAdmin)
clinic_admin_site.register(POSSaleItem, POSSaleItemAdmin)

# Also register with default admin for compatibility
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Service)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Billing, BillingAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Prescription, PrescriptionAdmin)
admin.site.register(POSSale, POSSaleAdmin)
admin.site.register(POSSaleItem, POSSaleItemAdmin)


# Export everything for easy access
__all__ = [
    'clinic_admin_site',
    'CustomModelAdmin',
    'RestrictedUserAdmin',
    'GroupAdmin',
    'AppointmentAdmin',
    'ServiceAdmin',
    'BookingAdmin',
    'PatientAdmin',
    'MedicalRecordAdmin',
    'MedicalImageAdmin',
    'MedicalImageInline',
    'PrescriptionInline',
    'BillingAdmin',
    'PaymentAdmin',
    'PaymentInline',
    'InventoryAdmin',
    'InventoryAdminForm',
    'StockTransactionAdmin',
    'PrescriptionAdmin',
    'POSSaleAdmin',
    'POSSaleItemAdmin',
    'POSSaleItemInline',
]
