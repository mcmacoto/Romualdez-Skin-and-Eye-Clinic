"""
Test Patient Dashboard Visibility Fixes
Tests to verify that:
1. Patients without profiles can still access dashboard
2. Patients with profiles see their data correctly
3. Bookings are displayed based on email, not just profile
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, time, timedelta
from bookings.models import Booking, Patient, Service, MedicalRecord, Billing


class PatientDashboardVisibilityTest(TestCase):
    """Test patient dashboard visibility for users with and without profiles"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create a service
        self.service = Service.objects.create(
            name='Eye Checkup',
            description='Comprehensive eye examination',
            price=500.00
        )
        
        # Create test user WITHOUT patient profile
        self.user_no_profile = User.objects.create_user(
            username='newpatient',
            email='newpatient@example.com',
            password='testpass123',
            first_name='New',
            last_name='Patient'
        )
        
        # Create test user WITH patient profile
        self.user_with_profile = User.objects.create_user(
            username='existingpatient',
            email='existingpatient@example.com',
            password='testpass123',
            first_name='Existing',
            last_name='Patient'
        )
        
        # Create patient profile for second user
        self.patient_profile = Patient.objects.create(
            user=self.user_with_profile,
            phone='09171234567',
            date_of_birth=date(1990, 5, 15),
            gender='M',
            blood_type='O+'
        )
        
        # Create bookings for both users (by email)
        self.booking_no_profile = Booking.objects.create(
            patient_name='New Patient',
            patient_email='newpatient@example.com',
            patient_phone='09181234567',
            service=self.service,
            date=date.today() + timedelta(days=7),
            time=time(10, 0),
            notes='First visit',
            status='Pending'
        )
        
        self.booking_with_profile = Booking.objects.create(
            patient_name='Existing Patient',
            patient_email='existingpatient@example.com',
            patient_phone='09171234567',
            service=self.service,
            date=date.today() + timedelta(days=5),
            time=time(14, 0),
            notes='Follow-up visit',
            status='Confirmed'
        )
        
        # Create medical record for user with profile
        self.medical_record = MedicalRecord.objects.create(
            patient=self.patient_profile,
            visit_date=date.today() - timedelta(days=30),
            chief_complaint='Eye strain',
            symptoms='Difficulty focusing',
            diagnosis='Astigmatism',
            treatment_plan='Prescription glasses'
        )
        
        # Create billing for user with profile
        self.billing = Billing.objects.create(
            booking=self.booking_with_profile,
            service_fee=500.00,
            medicine_fee=0.00,
            additional_fee=0.00,
            discount=0.00,
            is_paid=False
        )
    
    def test_dashboard_accessible_without_profile(self):
        """Test that user without profile can access dashboard"""
        # Log in as user without profile
        self.client.force_login(self.user_no_profile)
        
        # Access dashboard
        response = self.client.get(reverse('bookings_v2:patient_dashboard'))
        
        # Should return 200 OK (not redirect or error)
        self.assertEqual(response.status_code, 200)
        
        # Context should indicate no profile
        self.assertFalse(response.context['has_profile'])
        self.assertIsNone(response.context['patient'])
    
    def test_dashboard_shows_bookings_without_profile(self):
        """Test that bookings are displayed even without patient profile"""
        # Log in as user without profile
        self.client.force_login(self.user_no_profile)
        
        # Access dashboard
        response = self.client.get(reverse('bookings_v2:patient_dashboard'))
        
        # Should show bookings (queried by email)
        self.assertEqual(response.context['total_bookings'], 1)
        self.assertIn(self.booking_no_profile, response.context['upcoming_bookings'])
    
    def test_dashboard_accessible_with_profile(self):
        """Test that user with profile can access dashboard"""
        # Log in as user with profile
        self.client.force_login(self.user_with_profile)
        
        # Access dashboard
        response = self.client.get(reverse('bookings_v2:patient_dashboard'))
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Context should indicate profile exists
        self.assertTrue(response.context['has_profile'])
        self.assertEqual(response.context['patient'], self.patient_profile)
    
    def test_dashboard_shows_all_data_with_profile(self):
        """Test that all data is displayed when profile exists"""
        # Log in as user with profile
        self.client.force_login(self.user_with_profile)
        
        # Access dashboard
        response = self.client.get(reverse('bookings_v2:patient_dashboard'))
        
        # Should show bookings
        self.assertEqual(response.context['total_bookings'], 1)
        self.assertIn(self.booking_with_profile, response.context['upcoming_bookings'])
        
        # Should show medical records
        self.assertEqual(response.context['total_records'], 1)
        self.assertIn(self.medical_record, response.context['medical_records'])
        
        # Should show billing
        self.assertIn(self.billing, response.context['billings'])
        self.assertIn(self.billing, response.context['unpaid_bills'])
        self.assertEqual(response.context['total_outstanding'], self.billing.balance)
    
    def test_dashboard_no_medical_records_without_profile(self):
        """Test that medical records are empty when no profile exists"""
        # Log in as user without profile
        self.client.force_login(self.user_no_profile)
        
        # Access dashboard
        response = self.client.get(reverse('bookings_v2:patient_dashboard'))
        
        # Medical records should be empty
        self.assertEqual(response.context['total_records'], 0)
        self.assertEqual(len(response.context['medical_records']), 0)
    
    def test_dashboard_no_billing_without_profile(self):
        """Test that billing is empty when no profile exists"""
        # Log in as user without profile
        self.client.force_login(self.user_no_profile)
        
        # Access dashboard
        response = self.client.get(reverse('bookings_v2:patient_dashboard'))
        
        # Billing should be empty
        self.assertEqual(len(response.context['billings']), 0)
        self.assertEqual(response.context['total_outstanding'], 0)
    
    def test_template_renders_without_profile(self):
        """Test that template renders correctly without profile"""
        # Log in as user without profile
        self.client.force_login(self.user_no_profile)
        
        # Access dashboard
        response = self.client.get(reverse('bookings_v2:patient_dashboard'))
        
        # Check response content
        content = response.content.decode('utf-8')
        
        # Should show welcome message
        self.assertIn('Welcome to Your Patient Dashboard', content)
        
        # Should show booking information
        self.assertIn('New Patient', content)
        self.assertIn('Eye Checkup', content)
        
        # Should NOT crash or show profile-specific errors
        self.assertNotIn('Error', content)
        self.assertNotIn('Exception', content)
    
    def test_template_renders_with_profile(self):
        """Test that template renders correctly with profile"""
        # Log in as user with profile
        self.client.force_login(self.user_with_profile)
        
        # Access dashboard
        response = self.client.get(reverse('bookings_v2:patient_dashboard'))
        
        # Check response content
        content = response.content.decode('utf-8')
        
        # Should show personal information section
        self.assertIn('Personal Information', content)
        self.assertIn('Existing Patient', content)
        self.assertIn('09171234567', content)
        
        # Should show medical records
        self.assertIn('Medical Records', content)
        self.assertIn('Eye strain', content)
        
        # Should show billing
        self.assertIn('Billing', content)
        self.assertIn('Payments', content)
    
    def test_staff_redirected_from_patient_dashboard(self):
        """Test that staff users are redirected to admin dashboard"""
        # Create staff user
        staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@clinic.com',
            password='testpass123',
            is_staff=True
        )
        
        # Log in as staff
        self.client.force_login(staff_user)
        
        # Try to access patient dashboard
        response = self.client.get(reverse('bookings_v2:patient_dashboard'))
        
        # Should redirect to admin dashboard
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('bookings_v2:admin_dashboard')))


class PatientProfileCreationTest(TestCase):
    """Test that patient profiles are created correctly via signals"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create staff user for booking approval
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@clinic.com',
            password='testpass123',
            is_staff=True
        )
        
        # Create service
        self.service = Service.objects.create(
            name='General Checkup',
            description='General health examination',
            price=400.00
        )
    
    def test_profile_not_created_on_booking_confirmation(self):
        """Test that profile is NOT created when booking is confirmed"""
        # Create a booking
        booking = Booking.objects.create(
            patient_name='Test Patient',
            patient_email='testpatient@example.com',
            patient_phone='09181234567',
            service=self.service,
            date=date.today() + timedelta(days=5),
            time=time(10, 0),
            notes='Test booking',
            status='Pending',
            created_by=self.staff_user
        )
        
        # Verify no User or Patient exists yet
        self.assertFalse(User.objects.filter(email='testpatient@example.com').exists())
        
        # Confirm the booking
        booking.status = 'Confirmed'
        booking.save()
        
        # User and Patient should still NOT exist (profile created only on consultation Done)
        self.assertFalse(User.objects.filter(email='testpatient@example.com').exists())
    
    def test_profile_created_on_consultation_done(self):
        """Test that profile IS created when consultation is marked Done"""
        # Create a confirmed booking
        booking = Booking.objects.create(
            patient_name='Jane Smith',
            patient_email='jane.smith@example.com',
            patient_phone='09181234567',
            service=self.service,
            date=date.today(),
            time=time(10, 0),
            notes='Test booking',
            status='Confirmed',
            consultation_status='Not Yet',
            created_by=self.staff_user
        )
        
        # Verify no User or Patient exists yet
        self.assertFalse(User.objects.filter(email='jane.smith@example.com').exists())
        
        # Mark consultation as Done
        booking.consultation_status = 'Done'
        booking.save()
        
        # User should be created
        self.assertTrue(User.objects.filter(email='jane.smith@example.com').exists())
        
        # Patient profile should be created
        user = User.objects.get(email='jane.smith@example.com')
        self.assertTrue(hasattr(user, 'patient_profile'))
        
        # Medical record should be created
        patient = user.patient_profile
        self.assertTrue(MedicalRecord.objects.filter(patient=patient).exists())
        
        # Billing should be created
        self.assertTrue(Billing.objects.filter(booking=booking).exists())


if __name__ == '__main__':
    import unittest
    unittest.main()
