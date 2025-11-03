"""
Test to verify that marking a bill as paid creates a Payment record
This test specifically validates Issue #3 fix
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from bookings.models import Service, Booking, Billing, Payment
from datetime import date, time
from decimal import Decimal


class BillingMarkAsPaidTest(TestCase):
    """Test that htmx_mark_paid creates Payment records"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@clinic.com',
            password='admin123',
            first_name='Admin',
            last_name='User',
            is_staff=True,
            is_superuser=True
        )
        
        # Create patient user
        self.patient = User.objects.create_user(
            username='patient1',
            email='patient@example.com',
            password='pass123',
            first_name='John',
            last_name='Doe'
        )
        
        # Create service
        self.service = Service.objects.create(
            name='Eye Consultation',
            description='Basic eye check',
            price=Decimal('500.00')
        )
        
        # Create booking
        self.booking = Booking.objects.create(
            service=self.service,
            date=date.today(),
            time=time(10, 0),
            patient_name='John Doe',
            patient_email='patient@example.com',
            patient_phone='09123456789',
            status='Confirmed'
        )
        
        # Create billing for the booking
        self.billing = Billing.objects.create(
            booking=self.booking,
            total_amount=Decimal('500.00'),
            amount_paid=Decimal('0.00'),
            balance=Decimal('500.00'),
            is_paid=False,
            service_fee=Decimal('500.00')
        )
        
        self.client = Client()
        
    def test_mark_as_paid_creates_payment_record(self):
        """Test that marking bill as paid creates a Payment record"""
        # Login as admin
        self.client.force_login(self.admin)
        
        # Before marking as paid - verify no payments exist
        self.assertEqual(Payment.objects.filter(billing=self.billing).count(), 0)
        
        # Mark bill as paid via HTMX endpoint
        response = self.client.post(f'/admin/htmx/mark-paid/{self.billing.id}/')
        
        # Should be successful
        self.assertEqual(response.status_code, 200)
        
        # After marking as paid - verify Payment record was created
        payments = Payment.objects.filter(billing=self.billing)
        self.assertEqual(payments.count(), 1, "A Payment record should have been created")
        
        payment = payments.first()
        
        # Verify payment details
        self.assertEqual(payment.amount_paid, Decimal('500.00'), "Payment amount should equal the balance")
        self.assertEqual(payment.payment_method, 'Cash', "Default payment method should be Cash")
        self.assertEqual(payment.recorded_by, self.admin, "Payment should be recorded by the admin user")
        self.assertIn('Admin User', payment.notes, "Notes should mention who marked it paid")
        
        # Verify billing was updated by signal
        self.billing.refresh_from_db()
        self.assertTrue(self.billing.is_paid, "Billing should be marked as paid")
        self.assertEqual(self.billing.amount_paid, Decimal('500.00'), "Billing amount_paid should be updated")
        self.assertEqual(self.billing.balance, Decimal('0.00'), "Billing balance should be zero")
        
    def test_mark_as_paid_with_partial_payment_already_made(self):
        """Test marking as paid when patient already made a partial payment"""
        # Patient already paid 200
        Payment.objects.create(
            billing=self.billing,
            amount_paid=Decimal('200.00'),
            payment_method='Cash',
            notes='Partial payment',
            recorded_by=self.patient
        )
        
        # Billing should be updated by signal
        self.billing.refresh_from_db()
        self.assertEqual(self.billing.amount_paid, Decimal('200.00'))
        self.assertEqual(self.billing.balance, Decimal('300.00'))
        self.assertFalse(self.billing.is_paid)
        
        # Login as admin
        self.client.force_login(self.admin)
        
        # Mark as paid (should create payment for remaining 300)
        response = self.client.post(f'/admin/htmx/mark-paid/{self.billing.id}/')
        self.assertEqual(response.status_code, 200)
        
        # Should have 2 payments now
        payments = Payment.objects.filter(billing=self.billing)
        self.assertEqual(payments.count(), 2)
        
        # Latest payment should be for remaining balance
        latest_payment = payments.order_by('-id').first()
        self.assertEqual(latest_payment.amount_paid, Decimal('300.00'))
        self.assertEqual(latest_payment.recorded_by, self.admin)
        
        # Billing should now be fully paid
        self.billing.refresh_from_db()
        self.assertTrue(self.billing.is_paid)
        self.assertEqual(self.billing.amount_paid, Decimal('500.00'))
        self.assertEqual(self.billing.balance, Decimal('0.00'))
        
    def test_payment_history_visible(self):
        """Test that payments are visible in payment list"""
        # Create a payment by marking as paid
        self.client.force_login(self.admin)
        self.client.post(f'/admin/htmx/mark-paid/{self.billing.id}/')
        
        # Verify payment appears in payment history
        payments = Payment.objects.all()
        self.assertEqual(payments.count(), 1)
        
        payment = payments.first()
        self.assertEqual(payment.billing, self.billing)
        self.assertEqual(payment.amount_paid, Decimal('500.00'))
