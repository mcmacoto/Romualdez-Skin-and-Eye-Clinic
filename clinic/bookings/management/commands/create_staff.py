from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create staff user and assign to Clinic Staff group'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the staff user')
        parser.add_argument('email', type=str, help='Email for the staff user')
        parser.add_argument('--password', type=str, help='Password for the staff user', default='staffpass123')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        
        # Create or get the Clinic Staff group
        staff_group, created = Group.objects.get_or_create(name='Clinic Staff')
        if created:
            self.stdout.write(self.style.SUCCESS('Created "Clinic Staff" group'))
        
        # Create or get the Customer group
        customer_group, created = Group.objects.get_or_create(name='Customer')
        if created:
            self.stdout.write(self.style.SUCCESS('Created "Customer" group'))
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'User "{username}" already exists')
            )
            return
        
        # Create the staff user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,
            is_active=True
        )
        
        # Add user to Clinic Staff group
        user.groups.add(staff_group)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created staff user "{username}" with email "{email}"\n'
                f'Password: {password}\n'
                f'User has been added to "Clinic Staff" group'
            )
        )