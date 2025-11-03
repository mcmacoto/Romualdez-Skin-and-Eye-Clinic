"""
Test suite for patient dashboard totals and upcoming appointments
Tests the three new reported issues
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, time, timedelta
from decimal import Decimal

from bookings.models import (
    Booking, Service, Patient, MedicalRecord, 
    Billing, Payment
)


class PatientDashboardTotalsTest(TestCase):
    """Test that patient dashboard totals are correctly displayed"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create patient user with profile
        self.user = User.objects.create_user(
            username='testpatient2',
            email='testpatient2@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Patient2'
        )
        
        # Create patient profile
        self.patient = Patient.objects.create(
            user=self.user,
            phone='09123456789',
            address='123 Test St',
            date_of_birth=date(1990, 1, 1),
            gender='Male'
        )
        
        # Create test service
        self.service = Service.objects.create(
            name='Test Consultation',
            description='Test service',
            price=Decimal('500.00')
        )
        
        # Dashboard URL
        self.dashboard_url = reverse('bookings_v2:patient_dashboard')
    
    def test_dashboard_totals_with_complete_data(self):
        """Test that all totals (appointments, records, balance) display correctly"""
        # Create 3 bookings
        for i in range(3):
            Booking.objects.create(
                patient_name=self.user.get_full_name(),
                patient_email=self.user.email,
                patient_phone='09123456789',
                date=date.today() + timedelta(days=i+1),
                time=time(10, 0),
                service=self.service,
                status='Confirmed',
                consultation_status='Not Yet'
            )
        
        # Create 2 medical records
        from datetime import datetime
        for i in range(2):
            MedicalRecord.objects.create(
                patient=self.patient,
                visit_date=datetime.combine(date.today() - timedelta(days=i+1), time(10, 0)),
                chief_complaint=f'Test complaint {i}',
                diagnosis=f'Test diagnosis {i}',
                treatment_plan=f'Test treatment {i}'
            )
        
        # Create 1 unpaid billing
        booking = Booking.objects.create(
            patient_name=self.user.get_full_name(),
            patient_email=self.user.email,
            patient_phone='09123456789',
            date=date.today() - timedelta(days=5),
            time=time(14, 0),
            service=self.service,
            status='Completed',
            consultation_status='Done'
        )
        
        billing = Billing.objects.create(
            booking=booking,
            service_fee=Decimal('500.00')
        )
        
        # Create partial payment
        Payment.objects.create(
            billing=billing,
            amount_paid=Decimal('200.00'),
            payment_method='Cash'
        )
        
        # Login and get dashboard
        self.client.force_login(self.user)
        response = self.client.get(self.dashboard_url)
        
        # Verify totals in context
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_bookings'], 4)  # 3 upcoming + 1 past
        self.assertEqual(response.context['total_records'], 2)
        self.assertEqual(response.context['total_outstanding'], Decimal('300.00'))  # 500 - 200
        
        # Verify they appear in rendered HTML
        content = response.content.decode()
        self.assertIn('4', content)  # Total appointments
        self.assertIn('2', content)  # Total records
        self.assertIn('300', content)  # Outstanding balance


class UpcomingAppointmentsVisibilityTest(TestCase):
    """Test that confirmed appointments appear in Upcoming Appointments section"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create patient user
        self.user = User.objects.create_user(
            username='testpatient3',
            email='testpatient3@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Patient3'
        )
        
        # Create test service
        self.service = Service.objects.create(
            name='Eye Consultation',
            description='Eye check',
            price=Decimal('600.00')
        )
        
        self.dashboard_url = reverse('bookings_v2:patient_dashboard')
    
    def test_confirmed_future_appointment_appears_in_upcoming(self):
        """Test that a confirmed appointment with future date shows in Upcoming Appointments"""
        # Create a confirmed booking for tomorrow
        tomorrow = date.today() + timedelta(days=1)
        booking = Booking.objects.create(
            patient_name=self.user.get_full_name(),
            patient_email=self.user.email,
            patient_phone='09123456789',
            date=tomorrow,
            time=time(14, 0),
            service=self.service,
            status='Confirmed',
            consultation_status='Not Yet'
        )
        
        # Login and get dashboard
        self.client.force_login(self.user)
        response = self.client.get(self.dashboard_url)
        
        # Verify appointment is in upcoming_bookings
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['upcoming_bookings'].count(), 1)
        self.assertIn(booking, response.context['upcoming_bookings'])
        
        # Verify it appears in the rendered HTML
        content = response.content.decode()
        self.assertIn('Upcoming Appointments', content)
        self.assertIn('Eye Consultation', content)
        self.assertIn('Confirmed', content)
    
    def test_pending_future_appointment_appears_in_upcoming(self):
        """Test that a pending appointment also shows in Upcoming Appointments"""
        # Create a pending booking for next week
        next_week = date.today() + timedelta(days=7)
        booking = Booking.objects.create(
            patient_name=self.user.get_full_name(),
            patient_email=self.user.email,
            patient_phone='09123456789',
            date=next_week,
            time=time(10, 0),
            service=self.service,
            status='Pending',  # Pending status
            consultation_status='Not Yet'
        )
        
        # Login and get dashboard
        self.client.force_login(self.user)
        response = self.client.get(self.dashboard_url)
        
        # Verify appointment is in upcoming_bookings
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['upcoming_bookings'].count(), 1)
        self.assertIn(booking, response.context['upcoming_bookings'])
    
    def test_past_appointment_not_in_upcoming(self):
        """Test that past appointments don't appear in Upcoming Appointments"""
        # Create a confirmed booking in the past
        yesterday = date.today() - timedelta(days=1)
        booking = Booking.objects.create(
            patient_name=self.user.get_full_name(),
            patient_email=self.user.email,
            patient_phone='09123456789',
            date=yesterday,
            time=time(14, 0),
            service=self.service,
            status='Confirmed',
            consultation_status='Not Yet'
        )
        
        # Login and get dashboard
        self.client.force_login(self.user)
        response = self.client.get(self.dashboard_url)
        
        # Verify appointment is NOT in upcoming_bookings
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['upcoming_bookings'].count(), 0)
        self.assertNotIn(booking, response.context['upcoming_bookings'])
        
        # Should be in past_bookings instead
        self.assertEqual(response.context['past_bookings'].count(), 1)
        self.assertIn(booking, response.context['past_bookings'])
    
    def test_completed_appointment_not_in_upcoming(self):
        """Test that completed appointments don't appear in Upcoming Appointments"""
        # Create a completed booking (even if future date)
        tomorrow = date.today() + timedelta(days=1)
        booking = Booking.objects.create(
            patient_name=self.user.get_full_name(),
            patient_email=self.user.email,
            patient_phone='09123456789',
            date=tomorrow,
            time=time(14, 0),
            service=self.service,
            status='Completed',  # Completed status
            consultation_status='Done'
        )
        
        # Login and get dashboard
        self.client.force_login(self.user)
        response = self.client.get(self.dashboard_url)
        
        # Verify appointment is NOT in upcoming_bookings
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['upcoming_bookings'].count(), 0)
        
        # Should be in past_bookings instead
        self.assertIn(booking, response.context['past_bookings'])
