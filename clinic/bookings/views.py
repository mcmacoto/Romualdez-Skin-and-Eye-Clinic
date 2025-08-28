from django.shortcuts import render, redirect
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

def landing(request):
    return render(request, 'bookings/landing.html')

def home(request):
    return render(request, 'bookings/home.html')

def booking(request):  # Remove @login_required
    if request.method == "POST":
        # TODO: Save booking database logic here
        messages.success(request, "Your appointment request has been submitted successfully!")
        return redirect('booking')
        
    return render(request, 'bookings/booking.html')


def about(request):  # Remove @login_required
    return render(request, 'bookings/about.html')

def services(request):  # Remove @login_required
    services = Service.objects.all()
    return render(request, 'bookings/services.html', {'services': services})