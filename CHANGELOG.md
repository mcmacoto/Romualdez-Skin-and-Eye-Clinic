# Changelog

All notable changes to the Romualdez Skin and Eye Clinic Management System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-11-04

### Added

#### Dashboard Auto-Refresh System
- Implemented real-time dashboard statistics auto-refresh across all data-modifying operations
- Added `HX-Trigger: refreshStats` header to 13 view functions for seamless updates
- Enhanced patient management views (create, update, delete) to trigger stats refresh
- Enhanced medical record views (create, update) to trigger stats refresh
- Enhanced billing views (mark_paid) to trigger stats refresh for all billing metrics
- Enhanced inventory views (create, update, delete) to trigger stats refresh
- Enhanced appointment views (create, update, status changes) to trigger stats refresh
- Dashboard now shows real-time updates for all 18 statistics without page reload

#### Statistics Coverage
Auto-refresh now applies to:
- Booking statistics (total, pending, confirmed, completed, today's appointments)
- Patient & medical records counts
- Inventory metrics (total items, low stock, out of stock)
- Financial metrics (total billings, paid, unpaid, partially paid, revenue, outstanding balance)

### Changed

#### User Experience Improvements
- Eliminated need for manual page refresh to see updated dashboard statistics
- Dashboard metrics now update immediately after any create/update/delete action
- Improved feedback loop between user actions and dashboard display
- Enhanced professional feel with modern real-time updates

### Technical Details
- Leveraged existing HTMX infrastructure (no new dependencies)
- Utilized pre-existing `htmx_dashboard_stats` endpoint
- Modified 4 view files: `patient_views.py`, `billing_views.py`, `inventory_views.py`, `appointment_views.py`
- All changes backward-compatible with existing functionality
- Zero impact on server performance (stats only refresh on user actions)

---

## [2.0.0] - 2025-11-03

### Added

#### Global Image Cropper System
- Implemented reusable global image cropper module (`global_cropper.js`)
- Added centralized crop modal in admin dashboard to prevent nested modal issues
- Created Promise-based API with multiple aspect ratio controls (Free, 1:1, 16:9, 4:3)
- Added rotation, flip, and reset functionality with 1200x1200 max resolution
- Integrated image cropper into service creation/editing workflow

#### Template Tag System
- Created `description_filters.py` for service description formatting
- Implemented `format_service_description` filter with bullet point parsing
- Added support for line breaks and proper HTML formatting

#### UI/UX Enhancements
- Added visible close buttons to all modals with red circular design
- Implemented "Back" buttons in user detail and medical images views
- Fixed close button visibility with proper CSS contrast (white X on red background)
- Added yellow close button variant for green-themed modal headers
- Improved modal navigation and user flow consistency
- Enhanced admin dashboard interface with better visual hierarchy

### Changed

#### Performance Optimizations
- Added `prefetch_related('groups')` to user list queries (3 locations)
- Reduced N+1 query problem in admin management views (~90% query reduction)
- Optimized user management endpoints for faster page loads
- Added `-webkit-backdrop-filter` prefix for Safari/iOS browser support
- Removed debug `console.log` statements from production JavaScript

#### Code Structure
- Refactored service form to use global cropper instead of nested modal
- Removed 280+ lines of duplicate JavaScript from service_form.html
- Consolidated admin functionality into v2 dashboard
- Improved code organization and maintainability

### Removed

#### Documentation Cleanup
- Removed obsolete documentation files:
  - `BOOTSTRAP_PRIMARY_COLOR_FIX.md`
  - `CLEANUP_REPORT.md`
  - `OPTIMIZATION_COMPLETE.md`
  - `V2_DESIGN_ENHANCEMENT_REPORT.md`
  - `V2_QUICK_REFERENCE.md`
  - `docs/V2_FEATURE_PARITY_AUDIT.md`
  - `docs/V2_GO_LIVE_SUMMARY.md`
  - `docs/V2_LAUNCH_CHECKLIST.md`

#### Legacy Code
- Deleted deprecated admin module files:
  - `clinic/bookings/admin/__init__.py`
  - `clinic/bookings/admin/appointments.py`
  - `clinic/bookings/admin/base.py`
  - `clinic/bookings/admin/billing.py`
  - `clinic/bookings/admin/inventory.py`
  - `clinic/bookings/admin/patients.py`
  - `clinic/bookings/admin/pos.py`
- Removed `clinic/urls.py` (functionality moved to main configuration)

### Fixed
- Fixed modal z-index conflicts and Bootstrap 5 compatibility issues
- Fixed backdrop-filter blur effects on Safari browsers
- Fixed cross-browser visual consistency issues
- Fixed service description formatting in templates

### Technical Details
- **Files Changed**: 32 files
- **Lines Added**: +1,003
- **Lines Removed**: -4,423
- **Net Change**: -3,420 lines (cleaner codebase)
- **Testing**: All modal interactions, image cropper, and cross-browser compatibility verified
- **Breaking Changes**: None - all changes are backward compatible
- **Migration**: No database migrations required

---

## [1.0.0] - 2025-10-15

### Initial Release

#### Core Features
- Patient management system with comprehensive medical records
- Appointment scheduling with status tracking
- Medical records with image upload support
- Inventory management for medicines and equipment
- Billing and payment processing
- Point-of-sale (POS) system
- Staff portal with admin interface
- User authentication and authorization
- Role-based access control

#### Database Models
- Patient profiles with demographics and medical history
- Appointment and booking management
- Medical records with vital signs tracking
- Prescription management
- Inventory and stock transaction tracking
- Billing and payment records
- Service catalog

#### User Interface
- Django admin interface
- Bootstrap-based frontend
- Responsive design for mobile and desktop
- Custom CSS styling with clinic branding

#### Security
- User authentication system
- Staff permission middleware
- CSRF protection
- Secure password storage

#### Development Tools
- Custom management commands for:
  - Sample data generation
  - Staff account creation
  - Database cleanup
  - System setup
- Database verification scripts
- Automated setup scripts for multiple platforms

---

## Version History

- **2.0.0** (2025-11-03): Global image cropper, performance optimizations, UI/UX enhancements
- **1.0.0** (2025-10-15): Initial release with core clinic management features

---

## Upgrade Notes

### From 1.0.0 to 2.0.0

No database migrations or data migrations required. The upgrade includes:

1. **New Static Files**: Run `python manage.py collectstatic` to collect new JavaScript files
2. **Backward Compatible**: All existing functionality continues to work
3. **Optional**: Update templates to use new image cropper and template tags
4. **Performance**: Automatic performance improvements in user management

### Deployment Checklist

- [ ] Pull latest changes from repository
- [ ] Activate virtual environment
- [ ] Install updated dependencies: `pip install -r requirements.txt`
- [ ] Collect static files: `python manage.py collectstatic --noinput`
- [ ] Restart application server
- [ ] Clear browser cache for CSS/JS updates
- [ ] Verify image cropper functionality
- [ ] Test modal interactions

---

**Maintained by**: Development Team  
**Repository**: https://github.com/mcmacoto/Romualdez-Skin-and-Eye-Clinic
