from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Appointment, Service
from django.contrib import messages

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
        # TODO: Save booking database logic here
        messages.success(request, "Your appointment request has been submitted successfully!")
        return redirect('booking')
        
    return render(request, 'bookings/booking.html')


@login_required(login_url='/landing/')
def about(request):  # Remove @login_required
    return render(request, 'bookings/about.html')

@login_required(login_url='/landing/')
def services(request):  # Remove @login_required
    services = Service.objects.all()
    return render(request, 'bookings/services.html', {'services': services})