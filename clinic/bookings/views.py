from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Appointment, Service
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from datetime import date

# Create your views here.
def booking_form(request):
    if request.method == "POST":
        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']
        date = request.POST['date']
        time = request.POST['time']
        message = request.POST.get('message', '')

        Appointment.objects.create(
            name=name, email=email, phone=phone, date=date, time=time, message=message
        )

        messages.success(request, "Your appointment request has been sent!")
        return redirect('success')

    return render(request, 'bookings/form.html')

def booking_success(request):
    return render(request, 'bookings/success.html')

def is_authenticated(user):
    return user.is_authenticated

def landing(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'bookings/landing.html')

@login_required(login_url='/landing/')
def home(request):  # Remove @login_required
    return render(request, 'bookings/home.html')

@login_required(login_url='/landing/')
def booking(request):  # Remove @login_required
    if request.method == "POST":
        # Extract form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        message = request.POST.get('message', '')
        appointment_type = request.POST.get('appointment_type', 'general')
        
        # Create and save the appointment
        appointment = Appointment.objects.create(
            name=name,
            email=email,
            phone=phone,
            date=date_str,
            time=time_str,
            message=message
        )
        
        messages.success(request, f"Thank you {name}! Your {appointment_type} appointment request has been submitted successfully. We'll contact you within 24 hours to confirm.")
        return redirect('booking')
        
    context = {
        'today': date.today()
    }
    return render(request, 'bookings/booking.html', context)


@login_required(login_url='/landing/')
def about(request):  # Remove @login_required
    return render(request, 'bookings/about.html')

@login_required(login_url='/landing/')
def services(request):  # Remove @login_required
    services = Service.objects.all()
    return render(request, 'bookings/services.html', {'services': services})

def contact(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you could save the contact message to a model or send an email
        # For now, we'll just show a success message
        messages.success(request, f"Thank you {name}! Your message has been sent. We'll get back to you soon.")
        return redirect('contact')
        
    return render(request, 'bookings/contact.html')