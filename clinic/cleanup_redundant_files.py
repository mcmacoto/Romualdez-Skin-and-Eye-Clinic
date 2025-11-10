"""
System Cleanup Script
Removes redundant, unused, and duplicate files
Run this script to clean up your Django project
"""
import os
import shutil
from pathlib import Path

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent

# Files and directories to remove
FILES_TO_REMOVE = [
    # Legacy test files in bookings/ (moved to tests/ directory)
    'bookings/test_dashboard_issues.py',
    'bookings/test_dashboard_data_accuracy.py',
    'bookings/test_patient_dashboard_fixes.py',
    'bookings/test_payment_creation.py',
    
    # Temporary verification script (migration already verified)
    'verify_calendar_migration.py',
    
    # Empty views directory (using views_v2/)
    'bookings/views/',
]

DIRS_TO_REMOVE = [
    # Python cache directories
    '__pycache__',
]

def remove_pycache():
    """Remove all __pycache__ directories"""
    print("\n🗑️  Removing Python cache files...")
    count = 0
    for root, dirs, files in os.walk(BASE_DIR):
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(cache_dir)
                count += 1
                print(f"   ✅ Removed: {cache_dir}")
            except Exception as e:
                print(f"   ❌ Failed to remove {cache_dir}: {e}")
    print(f"   Total __pycache__ directories removed: {count}")

def remove_files():
    """Remove specified files"""
    print("\n🗑️  Removing redundant files...")
    for file_path in FILES_TO_REMOVE:
        full_path = BASE_DIR / file_path
        if full_path.exists():
            if full_path.is_dir():
                try:
                    shutil.rmtree(full_path)
                    print(f"   ✅ Removed directory: {file_path}")
                except Exception as e:
                    print(f"   ❌ Failed to remove {file_path}: {e}")
            else:
                try:
                    full_path.unlink()
                    print(f"   ✅ Removed file: {file_path}")
                except Exception as e:
                    print(f"   ❌ Failed to remove {file_path}: {e}")
        else:
            print(f"   ⚠️  Not found (already removed?): {file_path}")

def list_duplicate_migrations():
    """Check for duplicate migration files"""
    print("\n🔍  Checking for duplicate migrations...")
    migrations_dir = BASE_DIR / 'bookings' / 'migrations'
    
    if migrations_dir.exists():
        migrations = [f for f in migrations_dir.iterdir() if f.name.startswith('0027')]
        if len(migrations) > 1:
            print("   ⚠️  Found duplicate migration 0027:")
            for mig in migrations:
                print(f"      - {mig.name}")
            print("   Note: Migration 0027_calendar.py can be safely removed (superseded by 0028)")
        else:
            print("   ✅ No duplicate migrations found")

def show_unused_files():
    """Show potentially unused files"""
    print("\n📋  Potentially unused files (review before deleting):")
    print("   - bookings/models/blocked_dates.py (replaced by calendar.py)")
    print("   - bookings/forms.py (check if still used)")
    print("   - seed_minimal.py (development only)")

def main():
    print("=" * 60)
    print("🧹 ROMUALDEZ CLINIC SYSTEM CLEANUP")
    print("=" * 60)
    
    # Remove cache files
    remove_pycache()
    
    # Remove redundant files
    remove_files()
    
    # Check for duplicate migrations
    list_duplicate_migrations()
    
    # Show files that need manual review
    show_unused_files()
    
    print("\n" + "=" * 60)
    print("✅ CLEANUP COMPLETE!")
    print("=" * 60)
    print("\n📝 Next Steps:")
    print("1. Review the files listed above")
    print("2. Manually remove bookings/models/blocked_dates.py if not needed")
    print("3. Remove migration 0027_calendar.py (superseded by 0028)")
    print("4. Run: python manage.py check")
    print("5. Test your application")
    print("\n")

if __name__ == "__main__":
    main()
