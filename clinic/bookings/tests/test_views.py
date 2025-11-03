"""
Unit tests for bookings views
Tests authentication, CRUD operations, and HTMX endpoints
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, time, timedelta
from decimal import Decimal

from bookings.models import Service, Patient, Booking, Inventory, POSSale


class AuthenticationViewsTest(TestCase):
    """Test authentication views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            is_staff=True
        )
    
    def test_login_page_loads(self):
        """Test login page is accessible"""
        response = self.client.get(reverse('bookings_v2:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bookings_v2/login_v2.html')
    
    def test_login_with_valid_credentials(self):
        """Test login with correct username and password"""
        response = self.client.post(reverse('bookings_v2:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        # Should redirect to dashboard after successful login
        self.assertEqual(response.status_code, 302)
    
    def test_login_with_invalid_credentials(self):
        """Test login with incorrect password"""
        response = self.client.post(reverse('bookings_v2:login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        # Should stay on login page
        self.assertEqual(response.status_code, 200)
    
    def test_logout_redirects_to_login(self):
        """Test logout functionality"""
        self.client.force_login(self.user)
        response = self.client.post(reverse('bookings_v2:logout'))
        self.assertEqual(response.status_code, 302)


class PublicViewsTest(TestCase):
    """Test public-facing views"""
    
    def setUp(self):
        self.client = Client()
        from django.core.files.uploadedfile import SimpleUploadedFile
        image = SimpleUploadedFile(name='test.jpg', content=b'', content_type='image/jpeg')
        self.service = Service.objects.create(
            name='Eye Exam',
            description='Comprehensive eye examination',
            image=image,
            price=Decimal('600.00')
        )
    
    def test_home_page_loads(self):
        """Test public home page is accessible"""
        response = self.client.get(reverse('bookings_v2:home'))
        self.assertEqual(response.status_code, 200)
    
    def test_services_page_loads(self):
        """Test services page displays services"""
        response = self.client.get(reverse('bookings_v2:services'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Eye Exam')
    
    def test_public_booking_form_loads(self):
        """Test public booking form is accessible"""
        response = self.client.get(reverse('bookings_v2:booking'))
        self.assertEqual(response.status_code, 200)


class BookingViewsTest(TestCase):
    """Test booking management views"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff',
            password='staffpass123',
            is_staff=True
        )
        from django.core.files.uploadedfile import SimpleUploadedFile
        image = SimpleUploadedFile(name='test.jpg', content=b'', content_type='image/jpeg')
        self.service = Service.objects.create(
            name='Skin Consultation',
            description='Dermatology consultation',
            image=image,
            price=Decimal('800.00')
        )
        self.booking = Booking.objects.create(
            patient_name='Test Patient',
            patient_email='patient@test.com',
            patient_phone='09123456789',
            service=self.service,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            status='Pending',
            created_by=self.staff_user
        )
    
    def test_admin_dashboard_requires_authentication(self):
        """Test admin dashboard requires login"""
        response = self.client.get(reverse('bookings_v2:admin_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_admin_dashboard_loads_for_authenticated_user(self):
        """Test admin dashboard loads for logged-in staff"""
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('bookings_v2:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_htmx_appointments_list(self):
        """Test HTMX appointments endpoint"""
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('bookings_v2:htmx_appointments_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Patient')


class PatientViewsTest(TestCase):
    """Test patient management views"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff',
            password='staffpass123',
            is_staff=True
        )
        self.patient_user = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='patientpass123',
            first_name='Jane',
            last_name='Doe'
        )
        self.patient = Patient.objects.create(
            user=self.patient_user,
            date_of_birth=date(1995, 3, 15),
            gender='F',
            phone='+639123456789',
            address='123 Test St',
            created_by=self.staff_user
        )
    
    def test_htmx_patients_list_requires_staff_login(self):
        """Test patient list requires staff authentication"""
        response = self.client.get(reverse('bookings_v2:htmx_patients_list'))
        self.assertEqual(response.status_code, 302)
    
    def test_htmx_patients_list_loads_for_staff(self):
        """Test patient list displays for staff users"""
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('bookings_v2:htmx_patients_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jane Doe')
    
    def test_htmx_patient_detail_view(self):
        """Test patient detail view shows patient info"""
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('bookings_v2:htmx_patient_detail', args=[self.patient.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jane Doe')
        self.assertContains(response, '+639123456789')


class InventoryViewsTest(TestCase):
    """Test inventory management views"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff',
            password='staffpass123',
            is_staff=True
        )
        self.inventory_item = Inventory.objects.create(
            name='Test Medicine',
            description='Test Description',
            category='Medicine',
            quantity=50,
            price=Decimal('100.00')
        )
    
    def test_htmx_inventory_list_requires_authentication(self):
        """Test inventory list requires login"""
        response = self.client.get(reverse('bookings_v2:htmx_inventory_list'))
        self.assertEqual(response.status_code, 302)
    
    def test_htmx_inventory_list_loads_for_staff(self):
        """Test inventory list displays items"""
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('bookings_v2:htmx_inventory_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Medicine')


class POSViewsTest(TestCase):
    """Test Point of Sale views"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff',
            password='staffpass123',
            is_staff=True
        )
        self.inventory = Inventory.objects.create(
            name='Product',
            description='Test Product',
            category='Medicine',
            quantity=100,
            price=Decimal('50.00')
        )
    
    def test_htmx_pos_interface_requires_staff_login(self):
        """Test POS page requires staff authentication"""
        response = self.client.get(reverse('bookings_v2:htmx_pos_interface'))
        self.assertEqual(response.status_code, 302)
    
    def test_htmx_pos_interface_loads_for_staff(self):
        """Test POS page loads for staff users"""
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('bookings_v2:htmx_pos_interface'))
        self.assertEqual(response.status_code, 200)


class DashboardViewsTest(TestCase):
    """Test dashboard views"""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff',
            password='staffpass123',
            is_staff=True
        )
    
    def test_admin_dashboard_requires_staff_login(self):
        """Test admin dashboard requires staff authentication"""
        response = self.client.get(reverse('bookings_v2:admin_dashboard'))
        self.assertEqual(response.status_code, 302)
    
    def test_admin_dashboard_loads_for_staff(self):
        """Test admin dashboard displays for staff"""
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('bookings_v2:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
