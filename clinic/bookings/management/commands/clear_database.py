"""
Management command to clear all database tables except users and groups
Usage: python manage.py clear_database
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from bookings.models import (
    Appointment, Service, Patient, MedicalRecord, MedicalImage,
    Inventory, StockTransaction, Booking, Billing, Payment, 
    Prescription, POSSale, POSSaleItem
)


class Command(BaseCommand):
    help = 'Clear all database tables except users and groups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete all data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  WARNING: This will delete ALL data except users and groups!\n'
                    'To proceed, run: python manage.py clear_database --confirm\n'
                )
            )
            return

        self.stdout.write(self.style.WARNING('\n🗑️  Starting database cleanup...\n'))

        try:
            with transaction.atomic():
                # Delete in order to respect foreign key constraints
                deleted_counts = {}

                # POS System
                deleted_counts['POS Sale Items'] = POSSaleItem.objects.all().delete()[0]
                deleted_counts['POS Sales'] = POSSale.objects.all().delete()[0]

                # Billing & Payments
                deleted_counts['Payments'] = Payment.objects.all().delete()[0]
                deleted_counts['Billings'] = Billing.objects.all().delete()[0]

                # Medical Records
                deleted_counts['Prescriptions'] = Prescription.objects.all().delete()[0]
                deleted_counts['Medical Images'] = MedicalImage.objects.all().delete()[0]
                deleted_counts['Medical Records'] = MedicalRecord.objects.all().delete()[0]

                # Bookings & Appointments
                deleted_counts['Bookings'] = Booking.objects.all().delete()[0]
                deleted_counts['Appointments'] = Appointment.objects.all().delete()[0]

                # Inventory
                deleted_counts['Stock Transactions'] = StockTransaction.objects.all().delete()[0]
                deleted_counts['Inventory Items'] = Inventory.objects.all().delete()[0]

                # Patients
                deleted_counts['Patients'] = Patient.objects.all().delete()[0]

                # Services
                deleted_counts['Services'] = Service.objects.all().delete()[0]

                # Display results
                self.stdout.write(self.style.SUCCESS('\n✅ Database cleaned successfully!\n'))
                self.stdout.write(self.style.SUCCESS('Deleted records:'))
                for model, count in deleted_counts.items():
                    if count > 0:
                        self.stdout.write(f'  • {model}: {count}')

                total_deleted = sum(deleted_counts.values())
                self.stdout.write(
                    self.style.SUCCESS(f'\n📊 Total records deleted: {total_deleted}')
                )
                self.stdout.write(
                    self.style.SUCCESS('✅ Users and Groups were preserved.\n')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error clearing database: {str(e)}\n')
            )
            raise
