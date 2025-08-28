from django.db import models

# Create your models here.

class Appointment(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    date = models.DateField()
    time = models.TimeField()
    message =  models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    
    def __str__(self):
        return f"{self.name} - {self.date} {self.time}"

class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.CharField(max_length=100)  # Changed to CharField for static files
    
    def image_url(self):
        return f'/static/images/{self.image}'
    
    def __str__(self):
        return self.name
