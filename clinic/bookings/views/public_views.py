"""
Public-facing views for the booking system
Handles landing pages, booking forms, and informational pages
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from datetime import date, datetime, timedelta

from ..models import Service, Booking


def landing(request):
    """Landing page - redirects to home if authenticated"""
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'bookings/landing.html')


@login_required(login_url='/landing/')
def home(request):
    """Home page for authenticated users"""
    return render(request, 'bookings/home.html')


@login_required(login_url='/landing/')
def about(request):
    """About page"""
    return render(request, 'bookings/about.html')


@login_required(login_url='/landing/')
def services(request):
    """Services page listing all available services"""
    services = Service.objects.all()
    return render(request, 'bookings/services.html', {'services': services})


def contact(request):
    """Contact page with form submission"""
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
