"""
Django Forms for the Bookings Application
Provides validation and clean data handling for models
"""
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, time as datetime_time, datetime
import re

from .models import (
    Booking, Patient, MedicalRecord, MedicalImage,
    Prescription, Inventory, StockTransaction,
    Billing, Payment, POSSale, POSSaleItem, Service
)
from .validators import (
    validate_clinic_hours,
    validate_time_slot_interval,
    validate_phone_format,
)


class BookingForm(forms.ModelForm):
    """Form for creating and updating bookings"""
    
    class Meta:
        model = Booking
        fields = [
            'patient_name', 'patient_email', 'patient_phone',
            'date', 'time', 'service', 'notes'
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': date.today().isoformat()
            }),
            'time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),
            'patient_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name'
            }),
            'patient_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'patient_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+639XXXXXXXXX'
            }),
            'service': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes or requests...'
            }),
        }
    
    def clean_date(self):
        """Validate that booking date is not in the past"""
        booking_date = self.cleaned_data.get('date')
        if booking_date and booking_date < date.today():
            raise ValidationError("Booking date cannot be in the past")
        
        # Cannot book on Sundays (clinic closed)
        if booking_date and booking_date.weekday() == 6:  # Sunday = 6
            raise ValidationError('Clinic is closed on Sundays. Please choose another day.')
        
        return booking_date
    
    def clean_time(self):
        """Validate booking time is within clinic hours and on 30-min intervals"""
        booking_time = self.cleaned_data.get('time')
        
        if booking_time:
            try:
                # Validate clinic hours (8 AM - 5 PM)
                validate_clinic_hours(booking_time)
                
                # Validate 30-minute intervals
                validate_time_slot_interval(booking_time)
            except ValidationError as e:
                raise ValidationError(str(e))
        
        return booking_time
    
    def clean_phone(self):
        """Validate and normalize phone number"""
        phone = self.cleaned_data.get('patient_phone')
        if phone:
            # Remove all non-digit characters
            digits_only = re.sub(r'\D', '', phone)
            
            # Check if it's a valid Philippine mobile number
            if len(digits_only) < 10:
                raise ValidationError("Phone number must be at least 10 digits")
            
            # Normalize to +63 format if starts with 0
            if digits_only.startswith('0'):
                digits_only = '63' + digits_only[1:]
            
            # Ensure it starts with country code
            if not digits_only.startswith('63'):
                digits_only = '63' + digits_only
            
            return '+' + digits_only
        return phone
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        booking_date = cleaned_data.get('date')
        booking_time = cleaned_data.get('time')
        
        # Check if date and time together are in the past
        if booking_date and booking_time:
            booking_datetime = datetime.combine(booking_date, booking_time)
            if booking_datetime < datetime.now():
                raise ValidationError('Booking cannot be scheduled in the past.')
        
        # Check for double booking (excluding cancelled appointments)
        if booking_date and booking_time:
            existing = Booking.objects.filter(
                date=booking_date,
                time=booking_time
            ).exclude(status='Cancelled')
            
            # If updating, exclude current instance
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    f"This time slot is already booked. "
                    f"Please choose a different date or time."
                )
        
        return cleaned_data


class PatientForm(forms.ModelForm):
    """Form for creating and updating patient profiles"""
    
    # User fields
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Patient
        fields = [
            'date_of_birth', 'gender', 'phone', 'address',
            'emergency_contact_name', 'emergency_contact_phone',
            'blood_type', 'allergies', 'current_medications', 'medical_history'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'max': date.today().isoformat()
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+639XXXXXXXXX'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'blood_type': forms.Select(attrs={'class': 'form-select'}),
            'allergies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List any known allergies...'
            }),
            'current_medications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Current medications and dosages...'
            }),
            'medical_history': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Previous medical conditions and surgeries...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-fill user fields if editing existing patient
        if self.instance.pk and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['username'].initial = self.instance.user.username
    
    def clean_date_of_birth(self):
        """Ensure date of birth is not in the future"""
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > date.today():
            raise ValidationError("Date of birth cannot be in the future")
        return dob
    
    def clean_email(self):
        """Ensure email is unique"""
        email = self.cleaned_data.get('email')
        if email:
            # Check if email exists for another user
            existing = User.objects.filter(email=email)
            if self.instance.pk and self.instance.user:
                existing = existing.exclude(pk=self.instance.user.pk)
            
            if existing.exists():
                raise ValidationError("A user with this email already exists")
        return email


class MedicalRecordForm(forms.ModelForm):
    """Form for creating and updating medical records"""
    
    class Meta:
        model = MedicalRecord
        fields = [
            'patient', 'visit_date', 'chief_complaint',
            'symptoms', 'diagnosis', 'treatment_plan',
            'temperature', 'blood_pressure_systolic', 'blood_pressure_diastolic',
            'heart_rate', 'weight', 'height',
            'follow_up_date', 'additional_notes'
        ]
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'visit_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'chief_complaint': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': "Patient's main concern..."
            }),
            'symptoms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'diagnosis': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'treatment_plan': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': '°C'
            }),
            'blood_pressure_systolic': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Systolic'
            }),
            'blood_pressure_diastolic': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Diastolic'
            }),
            'heart_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'BPM'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'kg'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'cm'
            }),
            'follow_up_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'additional_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }


class PrescriptionForm(forms.ModelForm):
    """Form for creating prescriptions"""
    
    class Meta:
        model = Prescription
        fields = [
            'medical_record', 'medicine', 'custom_medicine_name',
            'dosage', 'frequency', 'duration', 'instructions'
        ]
        widgets = {
            'medical_record': forms.Select(attrs={'class': 'form-select'}),
            'medicine': forms.Select(attrs={'class': 'form-select'}),
            'custom_medicine_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter medicine name if not in inventory'
            }),
            'dosage': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 500mg, 1 tablet'
            }),
            'frequency': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 3 times a day, every 8 hours'
            }),
            'duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 7 days, 2 weeks'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Special instructions...'
            }),
        }


class InventoryForm(forms.ModelForm):
    """Form for creating and updating inventory items"""
    
    class Meta:
        model = Inventory
        fields = [
            'name', 'description', 'category', 'price',
            'quantity', 'stock', 'expiry_date'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'help_text': 'Minimum stock level threshold'
            }),
            'expiry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }
    
    def clean_price(self):
        """Ensure price is positive"""
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise ValidationError("Price cannot be negative")
        return price


class ContactForm(forms.Form):
    """Form for contact page submissions"""
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Phone Number'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Your message...'
        })
    )
