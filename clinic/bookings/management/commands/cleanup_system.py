"""
System Cleanup Management Command
Removes redundant files, cache, and unused data
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
import shutil
from pathlib import Path


class Command(BaseCommand):
    help = 'Clean up redundant files, cache, and optimize the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cache-only',
            action='store_true',
            help='Only clear Python cache files',
        )
        parser.add_argument(
            '--deep',
            action='store_true',
            help='Perform deep cleanup including staticfiles',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('🧹 SYSTEM CLEANUP STARTED'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        # Get project root
        base_dir = Path(__file__).resolve().parent.parent.parent.parent

        # 1. Clear Python cache
        self.stdout.write(self.style.WARNING('📦 Clearing Python cache files...'))
        cache_count = self.clear_pycache(base_dir)
        self.stdout.write(self.style.SUCCESS(f'   ✅ Removed {cache_count} cache directories\n'))

        if options['cache_only']:
            self.stdout.write(self.style.SUCCESS('✅ Cache cleanup complete!\n'))
            return

        # 2. Clear Django sessions
        self.stdout.write(self.style.WARNING('🗄️  Clearing expired sessions...'))
        call_command('clearsessions')
        self.stdout.write(self.style.SUCCESS('   ✅ Expired sessions cleared\n'))

        # 3. Clear staticfiles if deep cleanup
        if options['deep']:
            self.stdout.write(self.style.WARNING('📁 Clearing staticfiles...'))
            staticfiles_dir = base_dir / 'staticfiles'
            if staticfiles_dir.exists():
                shutil.rmtree(staticfiles_dir, ignore_errors=True)
                self.stdout.write(self.style.SUCCESS('   ✅ Staticfiles cleared'))
                
                # Regenerate staticfiles
                self.stdout.write(self.style.WARNING('   📦 Collecting static files...'))
                call_command('collectstatic', '--noinput')
                self.stdout.write(self.style.SUCCESS('   ✅ Static files collected\n'))
            else:
                self.stdout.write(self.style.SUCCESS('   ℹ️  No staticfiles directory found\n'))

        # 4. Optimize database
        self.stdout.write(self.style.WARNING('💾 Optimizing database...'))
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('VACUUM;')
        self.stdout.write(self.style.SUCCESS('   ✅ Database optimized\n'))

        # Summary
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('✅ SYSTEM CLEANUP COMPLETE'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('\n📊 Summary:'))
        self.stdout.write(self.style.SUCCESS(f'   • Python cache directories removed: {cache_count}'))
        self.stdout.write(self.style.SUCCESS('   • Expired sessions cleared'))
        if options['deep']:
            self.stdout.write(self.style.SUCCESS('   • Static files regenerated'))
        self.stdout.write(self.style.SUCCESS('   • Database optimized'))
        self.stdout.write(self.style.SUCCESS('\n🎉 System is now clean and optimized!\n'))

    def clear_pycache(self, base_dir):
        """Recursively remove __pycache__ directories"""
        count = 0
        for root, dirs, files in os.walk(base_dir):
            # Skip virtual environment directories
            if '.venv' in root or 'venv' in root or 'env' in root:
                continue
                
            if '__pycache__' in dirs:
                pycache_path = Path(root) / '__pycache__'
                try:
                    shutil.rmtree(pycache_path)
                    count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  Could not remove {pycache_path}: {e}')
                    )
        return count
