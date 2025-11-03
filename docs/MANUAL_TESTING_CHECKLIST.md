# Manual Testing Checklist
## Romualdez Skin and Eye Clinic Management System

**Version:** 1.0.0  
**Date:** November 3, 2025  
**Project Type:** College-level Django Web Application  
**Technologies:** Django 5.2.7, Bootstrap 5, HTMX, Alpine.js, SQLite3

---

## 📋 Testing Overview

This comprehensive checklist covers all modules and features—both original and newly implemented. Each section includes:
- **Test Steps**: Detailed actions to perform
- **Expected Outcomes**: What should happen
- **Edge Cases**: Boundary conditions and error scenarios

### Testing Prerequisites
- [ ] Development server running (`python manage.py test`)
- [ ] Database migrations applied
- [ ] Test data available (or create during testing)
- [ ] Browser DevTools open (Console tab for errors)
- [ ] Test in both Chrome and Firefox (if possible)

---

## 🔐 Module 1: Authentication & Authorization

### 1.1 Patient Login
**Test Steps:**
1. Navigate to `/` (Landing Page)
2. Click "Patient Portal"
3. Enter valid patient credentials
4. Click "Login"

**Expected Outcomes:**
- ✅ Redirects to `/home/` (Patient Dashboard)
- ✅ Welcome message displays patient name
- ✅ Navigation shows patient-specific menu items

**Edge Cases to Test:**
- ❌ Invalid credentials → Error message displayed
- ❌ Staff account on patient login → Redirects to staff portal
- ❌ Empty username/password → Form validation error
- ✅ Already logged in → Direct redirect to dashboard
- ❌ SQL injection attempt in username → Safely handled

**Test Data:**
```
Valid Patient: username=testpatient, password=testpass123
Invalid: username=invalid, password=wrong
```

---

### 1.2 Staff Login
**Test Steps:**
1. Navigate to `/staff-login/`
2. Enter valid staff credentials
3. Click "Login"

**Expected Outcomes:**
- ✅ Redirects to `/admin-dashboard/`
- ✅ Dashboard displays key statistics
- ✅ All management sections accessible

**Edge Cases to Test:**
- ❌ Patient account on staff login → Access denied
- ❌ django-axes rate limiting → After 5 failed attempts, account locked
- ✅ Superuser login → Shows "Full Administrator Access" badge
- ✅ Regular staff login → Shows "Staff Access" badge

**Test Data:**
```
Superuser: username=admin, password=admin123
Staff: username=staff1, password=staff123
```

---

### 1.3 Logout Functionality
**Test Steps:**
1. While logged in (any role)
2. Click "Logout" in navigation
3. Confirm logout

**Expected Outcomes:**
- ✅ Session cleared
- ✅ Redirects to landing page
- ✅ Accessing protected pages redirects to login

**Edge Cases to Test:**
- ✅ Logout from patient account
- ✅ Logout from staff account
- ✅ Double logout (click logout twice) → No errors

---

## 🏠 Module 2: Public Pages (No Login Required)

### 2.1 Landing Page (`/`)
**Test Steps:**
1. Navigate to `/`
2. Check page layout and buttons

**Expected Outcomes:**
- ✅ Clean, professional landing page
- ✅ "Patient Portal" button → `/login/`
- ✅ "Staff Portal" button → `/staff-login/`
- ✅ "Main Website" button → `/home/`

---

### 2.2 Home Page (`/home/`)
**Test Steps:**
1. Navigate to `/home/`
2. Scroll through sections

**Expected Outcomes:**
- ✅ Hero section with clinic info
- ✅ Services section displays all services
- ✅ About section visible
- ✅ Contact information displayed
- ✅ "Book Now" button → `/booking/`

---

### 2.3 Booking Page (Public)
**Test Steps:**
1. Navigate to `/booking/`
2. Fill out booking form:
   - Select service
   - Choose date (future date)
   - Select time (8:00 AM - 5:00 PM)
   - Fill patient information
3. Submit booking

**Expected Outcomes:**
- ✅ Form submits successfully
- ✅ Success message displayed
- ✅ Booking status = 'Pending'
- ✅ Email confirmation sent (if configured)

**Edge Cases to Test:**
- ❌ Past date selection → Validation error
- ❌ Sunday selection → "Clinic closed on Sundays"
- ❌ Time outside clinic hours (before 8 AM or after 5 PM) → Validation error
- ❌ Time not in 30-minute intervals (e.g., 9:15) → Error "Use 30-minute intervals"
- ❌ Double booking (same service, date, time) → Prevented by model validation
- ❌ Invalid phone format → Validation error
- ❌ Missing required fields → Form validation errors
- ✅ Valid booking with notes → Notes saved

**Test Data:**
```
Valid Booking:
- Service: Eye Consultation
- Date: Tomorrow's date
- Time: 09:00
- Name: John Doe
- Email: john@example.com
- Phone: 09171234567
- Notes: First time patient

Invalid Cases:
- Date: Yesterday
- Time: 7:30 AM (before clinic hours)
- Time: 9:15 AM (not 30-min interval)
- Day: Next Sunday
```

---

### 2.4 Services Page
**Test Steps:**
1. Navigate to `/services/`
2. View all services

**Expected Outcomes:**
- ✅ All services displayed with images
- ✅ Service names, descriptions, prices visible
- ✅ "Book Now" buttons functional

---

### 2.5 About Page
**Test Steps:**
1. Navigate to `/about/`

**Expected Outcomes:**
- ✅ Clinic information displayed
- ✅ Mission/vision statements visible
- ✅ Team information (if applicable)

---

### 2.6 Contact Page
**Test Steps:**
1. Navigate to `/contact/`
2. Fill contact form
3. Submit

**Expected Outcomes:**
- ✅ Contact form submits
- ✅ Success message displayed
- ✅ Form data saved/emailed

---

## 📊 Module 3: Staff Dashboard

### 3.1 Dashboard Overview
**Test Steps:**
1. Login as staff
2. Navigate to `/admin-dashboard/`
3. Observe all sections

**Expected Outcomes:**
- ✅ Permission badge displayed (Superuser or Staff)
- ✅ "Key Statistics" grid shows 8-9 stat cards
- ✅ All stat numbers are accurate
- ✅ Stat cards are clickable (open modals)
- ✅ Charts section displays 2 charts (Monthly Appointments, Services Distribution)
- ✅ Quick Actions section visible (right sidebar)

**Key Statistics to Verify:**
- ✅ Total Appointments (matches database count)
- ✅ Pending Bookings (status='Pending' count)
- ✅ Today's Appointments (today's date count)
- ✅ Total Bookings (all bookings)
- ✅ Unpaid Bills (is_paid=False count)
- ✅ Patient Profiles (total patients)
- ✅ Medical Records (total records)
- ✅ Inventory Items (total inventory)
- ✅ Low Stock Items (quantity ≤ reorder_level) - Shows only if > 0

---

### 3.2 Dashboard Auto-Refresh ⚡ (NEW FEATURE)
**Test Steps:**
1. Open dashboard in one browser window
2. Perform actions that affect statistics:
   - Accept a pending booking
   - Create a new appointment
   - Record a payment
   - Update inventory
   - Add a patient
3. Observe "Key Statistics" grid

**Expected Outcomes:**
- ✅ **Statistics automatically refresh** after HTMX actions
- ✅ Numbers update without page reload
- ✅ Smooth transition (no flicker)
- ✅ Refresh happens within 1-2 seconds of action

**Specific Actions to Test:**
| Action | Stat That Should Update |
|--------|------------------------|
| Accept pending booking | Pending Bookings ↓, Total Appointments ↑, Patient Profiles ↑ |
| Create appointment | Total Appointments ↑ |
| Record payment | Unpaid Bills ↓ |
| Add inventory item | Inventory Items ↑ |
| Patient reaches low stock | Low Stock Items ↑ |
| Delete appointment | Total Appointments ↓ |
| Update consultation status | (No change) |

---

### 3.3 Dashboard Charts
**Test Steps:**
1. Scroll to "Analytics & Insights" section
2. View both charts

**Expected Outcomes:**
- ✅ **Monthly Appointments Bar Chart** displays last 6 months
- ✅ Chart shows month labels (e.g., "November 2025")
- ✅ Bar heights correspond to appointment counts
- ✅ Hover shows exact count
- ✅ **Services Distribution Doughnut Chart** shows top 6 services
- ✅ Service names in legend
- ✅ Percentages/counts visible
- ✅ Charts are responsive (resize window to test)

**Edge Cases:**
- ✅ No data → Charts show "No data available"
- ✅ Only 1 service → Doughnut shows 100%
- ✅ More than 6 services → Only top 6 displayed

---

## 📅 Module 4: Appointments Management

### 4.1 View All Appointments
**Test Steps:**
1. Click "Total Appointments" stat card
2. Modal opens with appointments list

**Expected Outcomes:**
- ✅ Modal displays all appointments
- ✅ Pagination works (25 per page)
- ✅ Search box filters by name, email, phone, service
- ✅ Columns: Date, Time, Patient, Service, Status, Actions

---

### 4.2 Search & Filter Appointments (PHASE 8 - Advanced Search)
**Test Steps:**
1. Open appointments modal
2. Use search box: Enter patient name
3. Use date range filters: Select start and end dates
4. Use service filter: Select specific service
5. Use status filters: Click "Pending", "Confirmed", "Completed", "Today"

**Expected Outcomes:**
- ✅ **Multi-field search** works (name, email, phone, service name)
- ✅ **Date range filtering** shows only appointments in range
- ✅ **Service filter** shows only appointments for that service
- ✅ **Status filters** correctly filter appointments
- ✅ **"Today" filter** shows only today's appointments
- ✅ Filters can be combined (e.g., service + date range)
- ✅ Clear filters button resets all filters

**Edge Cases:**
- ✅ No results → "No appointments found" message
- ✅ Invalid date range (end before start) → Handled gracefully
- ✅ Empty search → Shows all appointments

---

### 4.3 Update Consultation Status
**Test Steps:**
1. Open appointments list
2. Find an appointment
3. Change consultation status dropdown (Not Yet → Ongoing → Done)
4. Click "Update Status"

**Expected Outcomes:**
- ✅ Status updates in database
- ✅ Success message displayed
- ✅ Row updates without page reload (HTMX)
- ✅ Statistics DO NOT auto-refresh (no stat change)

---

### 4.4 Mark Consultation as Done
**Test Steps:**
1. Open appointments list
2. Click "Mark as Done" button

**Expected Outcomes:**
- ✅ Consultation status → "Done"
- ✅ Success notification
- ✅ Button changes to disabled state

---

### 4.5 Delete Appointment
**Test Steps:**
1. Open appointments list
2. Click "Delete" button (trash icon)
3. Confirm deletion

**Expected Outcomes:**
- ✅ Confirmation prompt appears
- ✅ Appointment deleted from database
- ✅ Row removed from table (HTMX)
- ✅ **Statistics auto-refresh** (Total Appointments ↓)

---

### 4.6 Create New Appointment (Staff)
**Test Steps:**
1. Click "Create Appointment" in Quick Actions
2. Fill form with valid data
3. Submit

**Expected Outcomes:**
- ✅ Form validation works
- ✅ Appointment created with status='Confirmed'
- ✅ Success message displayed
- ✅ **Statistics auto-refresh** (Total Appointments ↑)
- ✅ Email sent if configured

**Edge Cases:**
- ❌ Same validation as public booking (Sunday, clinic hours, intervals)

---

## 🕒 Module 5: Pending Bookings Management

### 5.1 View Pending Bookings
**Test Steps:**
1. Click "Pending Bookings" stat card
2. Modal opens

**Expected Outcomes:**
- ✅ All pending bookings displayed
- ✅ Shows: Date, Time, Patient Info, Service, Actions
- ✅ "Accept" and "Decline" buttons visible

---

### 5.2 Accept Booking
**Test Steps:**
1. Open pending bookings modal
2. Click "Accept" on a booking
3. Observe results

**Expected Outcomes:**
- ✅ Booking status → 'Confirmed'
- ✅ **Signal triggers:** Patient, MedicalRecord, Billing auto-created
- ✅ Success message: "Patient records created automatically"
- ✅ **Email sent:** Booking confirmation (if SMTP configured)
- ✅ Row fades out and removes after 2 seconds
- ✅ **Statistics auto-refresh** (Pending ↓, Total Appointments ↑, Patients ↑)

**Verification:**
- ✅ Check Patients list → New patient created
- ✅ Check Medical Records → New record exists
- ✅ Check Billing → New bill created

---

### 5.3 Decline Booking
**Test Steps:**
1. Open pending bookings modal
2. Click "Decline" on a booking

**Expected Outcomes:**
- ✅ Booking status → 'Cancelled'
- ✅ Row removed from list
- ✅ **Statistics auto-refresh** (Pending ↓)
- ✅ Booking still exists in database (not deleted)

---

## 👥 Module 6: Patient Management

### 6.1 View All Patients
**Test Steps:**
1. Click "Patient Profiles" stat card
2. Modal opens

**Expected Outcomes:**
- ✅ All patients listed
- ✅ Pagination works
- ✅ Search box functional
- ✅ Columns: Name, Email, Phone, Gender, Blood Type, Actions

---

### 6.2 Advanced Patient Search (PHASE 8)
**Test Steps:**
1. Open patients modal
2. Test each filter:
   - **Multi-field search:** Enter name, email, phone, or address
   - **Gender filter:** Select M, F, or O
   - **Blood type filter:** Select A+, O-, etc.
   - **Age range:** Enter min age (e.g., 18) and max age (e.g., 65)
3. Combine multiple filters

**Expected Outcomes:**
- ✅ **Multi-field search** filters across name, email, phone, address
- ✅ **Gender filter** shows only selected gender
- ✅ **Blood type filter** shows only matching blood types
- ✅ **Age range** calculates age from date_of_birth and filters correctly
- ✅ **Combined filters** work together (AND logic)
- ✅ Clear filters resets all

**Edge Cases:**
- ✅ Age min only → Shows patients older than X
- ✅ Age max only → Shows patients younger than X
- ✅ Age min > max → No results (valid)
- ❌ Non-numeric age → Handled gracefully
- ✅ No results → "No patients found"

---

### 6.3 View Patient Details
**Test Steps:**
1. Click "View" icon on a patient
2. Details panel loads

**Expected Outcomes:**
- ✅ Full patient information displayed
- ✅ Contact details, DOB, gender, blood type visible
- ✅ Medical history summary (if applicable)
- ✅ Recent appointments listed

---

### 6.4 Edit Patient
**Test Steps:**
1. Click "Edit" icon on a patient
2. Modify patient information
3. Save changes

**Expected Outcomes:**
- ✅ Form pre-filled with current data
- ✅ Validation works (phone format, DOB, etc.)
- ✅ Changes saved to database
- ✅ List updates without page reload

**Edge Cases:**
- ❌ Invalid phone format → Validation error
- ❌ Future date of birth → Validation error
- ❌ Age > 150 years → Validation error

---

### 6.5 Create New Patient
**Test Steps:**
1. Click "Add Patient" button
2. Fill all required fields
3. Submit

**Expected Outcomes:**
- ✅ Form validation works
- ✅ Patient created (creates User account too)
- ✅ **Statistics auto-refresh** (Patient Profiles ↑)
- ✅ Success message displayed

**Required Fields:**
- Username, Email, Password, First Name, Last Name, Phone, Date of Birth, Gender

---

## 🏥 Module 7: Medical Records

### 7.1 View Medical Records
**Test Steps:**
1. Click "Medical Records" stat card
2. Modal opens

**Expected Outcomes:**
- ✅ All records listed
- ✅ Shows: Patient Name, Date, Diagnosis, Doctor, Actions
- ✅ Search and filter functional

---

### 7.2 View Medical Record Details
**Test Steps:**
1. Click "View" on a record
2. Details panel loads

**Expected Outcomes:**
- ✅ Full record displayed: Chief complaint, symptoms, diagnosis, treatment, vitals
- ✅ Medical images (if uploaded)
- ✅ Prescriptions (if created)
- ✅ Follow-up date (if set)

---

### 7.3 Edit Medical Record
**Test Steps:**
1. Click "Edit" on a record
2. Update fields (diagnosis, treatment, notes)
3. Upload medical image
4. Save

**Expected Outcomes:**
- ✅ Changes saved
- ✅ Image uploaded successfully
- ✅ Record updated in list

---

### 7.4 Create Prescription
**Test Steps:**
1. Open a medical record
2. Click "Add Prescription"
3. Fill prescription details:
   - Medicine name
   - Dosage
   - Frequency
   - Duration
   - Instructions
4. Save

**Expected Outcomes:**
- ✅ Prescription created
- ✅ Linked to medical record
- ✅ Displays in record details

**Edge Cases:**
- ✅ Custom medicine name (not in inventory)
- ✅ Multiple prescriptions per record

---

## 💰 Module 8: Billing & Payments

### 8.1 View All Billings
**Test Steps:**
1. Navigate to Billing section
2. View billing list

**Expected Outcomes:**
- ✅ All billings displayed
- ✅ Shows: Patient, Service, Amount, Paid, Balance, Status
- ✅ Filter by paid/unpaid status

---

### 8.2 View Unpaid Bills
**Test Steps:**
1. Click "Unpaid Bills" stat card
2. Modal opens

**Expected Outcomes:**
- ✅ Only unpaid bills displayed (is_paid=False)
- ✅ Shows outstanding balances
- ✅ "Record Payment" button available

---

### 8.3 Record Payment
**Test Steps:**
1. Open unpaid bills
2. Click "Record Payment" on a bill
3. Enter payment amount
4. Submit

**Expected Outcomes:**
- ✅ Payment created in Payment model
- ✅ Billing.amount_paid increases
- ✅ Billing.balance decreases
- ✅ If balance = 0, is_paid = True
- ✅ **Statistics auto-refresh** (Unpaid Bills ↓ if fully paid)
- ✅ Success message displayed

**Edge Cases:**
- ❌ Payment amount > balance → Validation error
- ❌ Negative payment → Validation error
- ✅ Partial payment → is_paid remains False
- ✅ Full payment → is_paid becomes True
- ✅ Overpayment prevention

**Test Data:**
```
Bill Amount: ₱1,500.00
Payment 1: ₱500.00 → Balance: ₱1,000.00 (Unpaid)
Payment 2: ₱1,000.00 → Balance: ₱0.00 (Paid)
```

---

### 8.4 View Payment History
**Test Steps:**
1. Open a billing record
2. View payments tab

**Expected Outcomes:**
- ✅ All payments for this bill listed
- ✅ Shows: Date, Amount, Method, Received By
- ✅ Total paid calculated correctly

---

## 📦 Module 9: Inventory Management

### 9.1 View Inventory
**Test Steps:**
1. Click "Inventory Items" stat card
2. Modal opens

**Expected Outcomes:**
- ✅ All inventory items listed
- ✅ Shows: Name, Category, Quantity, Price, Reorder Level, Actions
- ✅ Search and filter functional
- ✅ Low stock items highlighted (quantity ≤ reorder_level)

---

### 9.2 Filter Low Stock Items
**Test Steps:**
1. Click "Low Stock Items" stat card
2. Modal opens

**Expected Outcomes:**
- ✅ Only items with quantity ≤ reorder_level displayed
- ✅ Items highlighted in yellow/orange
- ✅ Action required message

---

### 9.3 Add Inventory Item
**Test Steps:**
1. Click "Add Inventory" button
2. Fill form:
   - Name: "Contact Lens Solution"
   - Category: "Eye Care"
   - Quantity: 50
   - Price: ₱350.00
   - Reorder Level: 10
3. Submit

**Expected Outcomes:**
- ✅ Item created
- ✅ **Statistics auto-refresh** (Inventory Items ↑)
- ✅ Success message
- ✅ List updates

**Validation:**
- ❌ Negative quantity → Error
- ❌ Negative price → Error
- ❌ Empty required fields → Validation errors

---

### 9.4 Update Inventory (Add Stock)
**Test Steps:**
1. Click "Adjust Stock" on an item
2. Select "Add Stock"
3. Enter quantity: 20
4. Add notes: "Restocking"
5. Submit

**Expected Outcomes:**
- ✅ Inventory quantity increases by 20
- ✅ StockTransaction created (transaction_type='IN')
- ✅ Notes saved
- ✅ List updates
- ✅ If item was low stock and now above reorder level, **Low Stock Items ↓**

---

### 9.5 Update Inventory (Remove Stock)
**Test Steps:**
1. Click "Adjust Stock" on an item
2. Select "Remove Stock"
3. Enter quantity: 5
4. Add notes: "Damaged items"
5. Submit

**Expected Outcomes:**
- ✅ Inventory quantity decreases by 5
- ✅ StockTransaction created (transaction_type='OUT')
- ✅ Notes saved
- ✅ If quantity drops to ≤ reorder_level, **Low Stock Items ↑**

**Edge Cases:**
- ❌ Remove more than available → Error "Insufficient stock"
- ❌ Remove from 0 quantity → Error

---

### 9.6 Delete Inventory Item
**Test Steps:**
1. Click "Delete" on an item
2. Confirm deletion

**Expected Outcomes:**
- ✅ Item deleted
- ✅ **Statistics auto-refresh** (Inventory Items ↓)
- ✅ Associated StockTransactions remain (audit trail)

---

## 🛒 Module 10: Point of Sale (POS)

### 10.1 Create POS Sale
**Test Steps:**
1. Navigate to POS section
2. Click "New Sale"
3. Add items:
   - Select inventory item
   - Enter quantity
   - Click "Add to Cart"
4. Repeat for multiple items
5. Select payment method
6. Click "Complete Sale"

**Expected Outcomes:**
- ✅ Cart displays all items with subtotals
- ✅ Total amount calculated correctly
- ✅ POSSale created
- ✅ POSSaleItem records created for each item
- ✅ **Inventory auto-decremented** for each item
- ✅ Receipt displayed
- ✅ Success message

**Calculation Test:**
```
Item 1: Eye Drops (₱250.00) x 2 = ₱500.00
Item 2: Contact Lens (₱1,200.00) x 1 = ₱1,200.00
Total: ₱1,700.00
```

**Edge Cases:**
- ❌ Quantity > available stock → Error
- ❌ Empty cart → Cannot complete sale
- ✅ Item becomes low stock after sale → **Low Stock Items ↑**

---

### 10.2 View POS Sales History
**Test Steps:**
1. Navigate to POS History
2. View past sales

**Expected Outcomes:**
- ✅ All sales listed
- ✅ Shows: Date, Items Count, Total, Payment Method
- ✅ Filter by date range
- ✅ Search by item name

---

### 10.3 View POS Sale Receipt
**Test Steps:**
1. Click "View" on a sale
2. Receipt modal opens

**Expected Outcomes:**
- ✅ Professional receipt layout
- ✅ Clinic header
- ✅ Sale date and ID
- ✅ Itemized list with quantities and prices
- ✅ Subtotal, tax (if applicable), total
- ✅ Payment method
- ✅ Print button functional

---

## 🔧 Module 11: Admin Management

### 11.1 User Management
**Test Steps:**
1. Navigate to Users section (superuser only)
2. View users list

**Expected Outcomes:**
- ✅ All users listed (staff and patients)
- ✅ Shows: Username, Name, Email, Role, Status, Actions
- ✅ Filter by role (Staff, Patient)
- ✅ Search by username or email

---

### 11.2 Create User
**Test Steps:**
1. Click "Add User"
2. Fill form:
   - Username: "newstaff"
   - Email: "newstaff@clinic.com"
   - Password: "SecurePass123"
   - First/Last Name
   - Check "Is Staff"
3. Submit

**Expected Outcomes:**
- ✅ User created
- ✅ **Statistics auto-refresh** (if creates patient profile)
- ✅ Success message with custom HTMX trigger
- ✅ List refreshes (HTMX)

**Edge Cases:**
- ❌ Duplicate username → Error
- ❌ Weak password → Validation error
- ❌ Invalid email → Validation error

---

### 11.3 Edit User
**Test Steps:**
1. Click "Edit" on a user
2. Modify details (email, name, role)
3. Save

**Expected Outcomes:**
- ✅ Changes saved
- ✅ List updates
- ✅ Custom HTMX trigger fired

---

### 11.4 Delete User
**Test Steps:**
1. Click "Delete" on a user (non-admin)
2. Confirm deletion

**Expected Outcomes:**
- ✅ User deleted (soft delete preferred)
- ✅ List updates
- ✅ Cannot delete superuser
- ✅ Warning if user has related records

---

### 11.5 Service Management
**Test Steps:**
1. Navigate to Services section
2. View services list

**Expected Outcomes:**
- ✅ All services displayed
- ✅ Shows: Name, Description, Price, Booking Count, Actions
- ✅ Search by service name

---

### 11.6 Create Service
**Test Steps:**
1. Click "Add Service"
2. Fill form:
   - Name: "Laser Eye Treatment"
   - Description: "Advanced laser correction"
   - Price: ₱5,000.00
   - Upload image
3. Submit

**Expected Outcomes:**
- ✅ Service created
- ✅ Image uploaded
- ✅ Success message
- ✅ Appears in services list

---

### 11.7 Edit Service
**Test Steps:**
1. Click "Edit" on a service
2. Update price and description
3. Save

**Expected Outcomes:**
- ✅ Changes saved
- ✅ Image can be replaced
- ✅ List updates

---

### 11.8 Delete Service
**Test Steps:**
1. Click "Delete" on a service
2. Confirm

**Expected Outcomes:**
- ✅ Service deleted (or soft deleted)
- ✅ Warning if service has bookings
- ✅ List updates

---

## 📧 Module 12: Email Notifications (PHASE 2)

### 12.1 Booking Confirmation Email
**Test Steps:**
1. Create a new booking (public form)
2. Check email inbox (if SMTP configured)

**Expected Outcomes:**
- ✅ Email sent to patient email
- ✅ Subject: "Booking Confirmation - Romualdez Clinic"
- ✅ HTML email with:
  - Clinic header/logo
  - Booking details (service, date, time)
  - Status badge ("Pending")
  - Next steps instructions
  - Contact information
- ✅ Plain text fallback included

**Test with Console Backend:**
If using `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`:
- ✅ Email output visible in terminal/console
- ✅ All details present

---

### 12.2 Booking Status Update Email
**Test Steps:**
1. Accept a pending booking (staff action)
2. Check email inbox

**Expected Outcomes:**
- ✅ Email sent to patient
- ✅ Subject: "Booking Status Update - Romualdez Clinic"
- ✅ Shows old status → new status
- ✅ "Pending" → "Confirmed" transition highlighted
- ✅ Updated appointment details
- ✅ Confirmation message

**Edge Cases:**
- ✅ Email failure handled gracefully (logs error, continues operation)
- ✅ Invalid email address → Email not sent but booking still processed

---

## 📄 Module 13: Reports (PHASE 3)

### 13.1 Appointments PDF Report
**Test Steps:**
1. Navigate to `/reports/appointments-pdf/`
2. Optionally add query parameters: `?start_date=2025-11-01&end_date=2025-11-30&status=Confirmed`
3. Click "Download"

**Expected Outcomes:**
- ✅ PDF file downloads
- ✅ Professional formatting with ReportLab
- ✅ Header: Clinic name, report title, date range
- ✅ Table with columns: Date, Time, Patient, Service, Status
- ✅ Summary section: Total appointments, status breakdown
- ✅ Date filtering works
- ✅ Status filtering works

**Edge Cases:**
- ✅ No appointments → PDF shows "No records found"
- ✅ Large dataset (>100 appointments) → Multiple pages
- ✅ No filters → Shows all appointments

---

### 13.2 Patients CSV Export
**Test Steps:**
1. Navigate to `/reports/patients-csv/`
2. Click "Download"

**Expected Outcomes:**
- ✅ CSV file downloads
- ✅ Filename: `patients_export_YYYY-MM-DD.csv`
- ✅ Columns: Name, Email, Phone, Gender, Blood Type, Date of Birth, Visit Count
- ✅ Visit count annotation correct
- ✅ Opens in Excel/Google Sheets correctly

**Edge Cases:**
- ✅ Special characters in names → Properly escaped
- ✅ Empty fields → Shows blank cells

---

### 13.3 Billing CSV Export
**Test Steps:**
1. Navigate to `/reports/billing-csv/`
2. Add date filter: `?start_date=2025-11-01`
3. Download

**Expected Outcomes:**
- ✅ CSV file downloads
- ✅ Columns: Date, Patient, Service, Total Amount, Amount Paid, Balance, Status
- ✅ Date filtering works
- ✅ Currency formatted correctly (₱1,500.00)

---

### 13.4 Services PDF Report
**Test Steps:**
1. Navigate to `/reports/services-pdf/`
2. Download

**Expected Outcomes:**
- ✅ PDF file downloads
- ✅ Lists all services
- ✅ Shows: Name, Description, Price, Booking Count
- ✅ Summary: Total services, total revenue potential
- ✅ Professional layout

---

## 📊 Module 14: Dashboard Charts (PHASE 4)

### 14.1 Monthly Appointments Bar Chart
**Test Steps:**
1. Open staff dashboard
2. Scroll to "Analytics & Insights"
3. View bar chart

**Expected Outcomes:**
- ✅ Chart displays last 6 months
- ✅ X-axis: Month labels (e.g., "November 2025")
- ✅ Y-axis: Appointment count
- ✅ Bars colored with clinic theme
- ✅ Hover tooltip shows exact count
- ✅ Chart responsive (resize browser)

**Data Verification:**
- ✅ Chart data matches database query
- ✅ Empty months show 0 (no bar)

---

### 14.2 Services Distribution Doughnut Chart
**Test Steps:**
1. View services doughnut chart
2. Hover over segments

**Expected Outcomes:**
- ✅ Shows top 6 services by booking count
- ✅ Legend displays service names
- ✅ Segments proportional to booking counts
- ✅ Hover shows service name and count
- ✅ Colors distinct and professional

**Edge Cases:**
- ✅ Fewer than 6 services → Shows all available
- ✅ No bookings → Shows "No data"

---

## 📝 Module 15: Activity Logging (PHASE 5)

### 15.1 Activity Log Model
**Test Steps:**
1. Open Django admin or database
2. View ActivityLog table
3. Perform actions (create appointment, update patient, etc.)
4. Check ActivityLog records

**Expected Outcomes:**
- ✅ ActivityLog table exists
- ✅ Records created for actions (when utility functions called)
- ✅ Fields populated: user, action, model_name, object_id, description, ip_address, timestamp
- ✅ Indexed fields improve query performance

**Note:** Activity logging utilities are implemented but may not be integrated into all views yet. This is intentional for college-level scope.

---

### 15.2 Activity Logger Utilities
**Test Steps:**
1. In Django shell: `python manage.py shell`
2. Test utility functions:
```python
from bookings.utils.activity_logger import log_create, log_update
from django.contrib.auth.models import User

user = User.objects.first()
log_create(user, 'Booking', 1, 'Test booking created', None)
log_update(user, 'Patient', 2, 'Updated patient info', None)
```

**Expected Outcomes:**
- ✅ ActivityLog records created
- ✅ All fields populated correctly
- ✅ No errors

---

## ✅ Module 16: Enhanced Validation (PHASE 6)

### 16.1 Custom Validators
**Test Steps:**
Test each validator by attempting invalid data:

1. **validate_future_date:**
   - Try booking with past date
   - Expected: ValidationError "Date must be in the future"

2. **validate_clinic_hours:**
   - Try time 7:00 AM or 6:00 PM
   - Expected: ValidationError "Time must be between 8:00 AM and 5:00 PM"

3. **validate_phone_format:**
   - Try phone: "12345" or "invalid"
   - Expected: ValidationError "Enter a valid Philippine phone number"

4. **validate_time_slot_interval:**
   - Try time: 9:15 AM or 10:45 AM
   - Expected: ValidationError "Time must be in 30-minute intervals"

5. **validate_age_range:**
   - Try DOB: 200 years ago or tomorrow
   - Expected: ValidationError

**Expected Outcomes:**
- ✅ All validators trigger correctly
- ✅ Error messages user-friendly
- ✅ Form submission prevented

---

### 16.2 BookingForm Enhanced Validation
**Test Steps:**
1. Try to book on Sunday
2. Try past date
3. Try time 7:30 AM (before clinic hours)
4. Try time 9:15 AM (not 30-min interval)
5. Try valid booking

**Expected Outcomes:**
- ❌ Sunday → "The clinic is closed on Sundays"
- ❌ Past date → "Cannot book in the past"
- ❌ Before hours → "Must be between 8:00 AM and 5:00 PM"
- ❌ Wrong interval → "Use 30-minute intervals"
- ✅ Valid booking → Accepted

---

### 16.3 Double Booking Prevention
**Test Steps:**
1. Create booking: Service A, Date: Tomorrow, Time: 10:00 AM
2. Try to create another: Service A, Date: Tomorrow, Time: 10:00 AM

**Expected Outcomes:**
- ❌ Second booking rejected
- ✅ Error: "This time slot is already booked for this service"
- ✅ Validation happens at model level (Booking.clean())

---

## 🚫 Module 17: Custom Error Pages (PHASE 7)

### 17.1 404 Page Not Found
**Test Steps:**
1. Set `DEBUG = False` in settings.py (IMPORTANT)
2. Navigate to non-existent URL: `/nonexistent-page/`

**Expected Outcomes:**
- ✅ Custom 404 page displays (not Django default)
- ✅ Animated gradient background
- ✅ Pulsing "404" animation
- ✅ Navigation suggestions (Home, Services, Booking, About, Contact)
- ✅ Links functional
- ✅ Branded with clinic theme

**Note:** When `DEBUG = True`, Django shows default debug page. Must set `DEBUG = False` for testing.

---

### 17.2 500 Internal Server Error
**Test Steps:**
1. Set `DEBUG = False`
2. Intentionally cause server error (e.g., divide by zero in a view)
3. Navigate to that URL

**Expected Outcomes:**
- ✅ Custom 500 page displays
- ✅ Animated gradient background (red theme)
- ✅ Shaking error icon animation
- ✅ Troubleshooting steps displayed
- ✅ Support contact information
- ✅ "Go Back" and "Homepage" buttons

**Recovery:**
- ✅ Set `DEBUG = True` after testing
- ✅ Fix intentional error

---

## 🔍 Module 18: Advanced Search (PHASE 8)

### 18.1 Appointment Advanced Search
**Tested in Module 4.2** - See Appointments Management

**Summary:**
- ✅ Multi-field text search (name, email, phone, service)
- ✅ Date range filtering
- ✅ Service filter dropdown
- ✅ Status filters (Pending, Confirmed, Completed, Today)
- ✅ Combined filters

---

### 18.2 Patient Advanced Search
**Tested in Module 6.2** - See Patient Management

**Summary:**
- ✅ Multi-field text search (name, email, phone, address)
- ✅ Gender filter (M, F, O)
- ✅ Blood type filter (A+, A-, B+, B-, AB+, AB-, O+, O-, UK)
- ✅ Age range (min/max)
- ✅ Combined filters

---

## 🔒 Module 19: Security & Edge Cases

### 19.1 CSRF Protection
**Test Steps:**
1. Open browser DevTools → Network tab
2. Submit any form
3. Check request headers

**Expected Outcomes:**
- ✅ CSRF token present in form
- ✅ CSRF token validated on submission
- ✅ Missing token → 403 Forbidden

---

### 19.2 XSS Prevention
**Test Steps:**
1. Try to input: `<script>alert('XSS')</script>` in text fields
2. Submit form
3. View rendered page

**Expected Outcomes:**
- ✅ Script tags escaped/sanitized
- ✅ No alert popup
- ✅ Text displayed as plain text

---

### 19.3 SQL Injection Prevention
**Test Steps:**
1. Try to input: `' OR '1'='1` in search/login fields
2. Submit

**Expected Outcomes:**
- ✅ Django ORM prevents SQL injection
- ✅ No database breach
- ✅ Treated as literal string

---

### 19.4 Rate Limiting (django-axes)
**Test Steps:**
1. Attempt login with wrong password 5 times
2. Try to login again

**Expected Outcomes:**
- ✅ After 5 failed attempts, account locked
- ✅ Error message: "Account locked due to too many failed attempts"
- ✅ Lockout expires after configured time (default: 30 minutes)

**Recovery:**
- ✅ Admin can unlock via Django admin

---

### 19.5 Permission Enforcement
**Test Steps:**
1. Logout staff account
2. Try to access `/admin-dashboard/` directly

**Expected Outcomes:**
- ✅ Redirects to login page
- ✅ @login_required and @staff_required decorators working

---

## 🌐 Module 20: Cross-Browser & Responsive Testing

### 20.1 Desktop Browsers
**Test in:**
- ✅ Chrome (latest)
- ✅ Firefox (latest)
- ✅ Edge (latest)
- ✅ Safari (if available)

**Expected Outcomes:**
- ✅ All features work consistently
- ✅ Styling consistent
- ✅ HTMX requests work
- ✅ Charts render correctly

---

### 20.2 Mobile Responsive
**Test Steps:**
1. Open DevTools → Toggle device toolbar
2. Test on different screen sizes:
   - Mobile (375px width)
   - Tablet (768px width)
   - Desktop (1920px width)

**Expected Outcomes:**
- ✅ Bootstrap grid responsive
- ✅ Navigation collapses to hamburger menu
- ✅ Tables scroll horizontally on mobile
- ✅ Forms stack vertically on mobile
- ✅ Stat cards rearrange (grid → single column)
- ✅ Charts resize proportionally

---

## 📱 Module 21: Performance Testing

### 21.1 Page Load Speed
**Test Steps:**
1. Open DevTools → Network tab
2. Reload dashboard
3. Check load time

**Expected Outcomes:**
- ✅ Dashboard loads in < 3 seconds (local development)
- ✅ HTMX requests complete in < 1 second
- ✅ No console errors

---

### 21.2 Database Query Optimization
**Test Steps:**
1. Enable Django Debug Toolbar (if installed)
2. View dashboard
3. Check number of queries

**Expected Outcomes:**
- ✅ Using `select_related()` and `prefetch_related()` to reduce queries
- ✅ No N+1 query problems
- ✅ Indexed fields used in filters

---

## ⚡ Module 22: Auto-Refresh Verification (CRITICAL)

### 22.1 Statistics Auto-Refresh Test
**Test Steps:**
1. Open dashboard in Browser Window 1
2. Note current statistics (e.g., Pending Bookings: 5)
3. In Browser Window 2 (or same window, different tab):
   - Accept a pending booking
4. Return to Browser Window 1
5. Observe "Key Statistics" grid

**Expected Outcomes:**
- ✅ **Statistics refresh automatically within 1-2 seconds**
- ✅ Pending Bookings count decreases
- ✅ Total Appointments increases
- ✅ Patient Profiles increases
- ✅ No page reload required
- ✅ Smooth transition (no flicker)

**Technical Verification:**
- ✅ HTMX response includes `HX-Trigger: refreshStats`
- ✅ Dashboard listens for `refreshStats` event
- ✅ Event triggers HTMX request to refresh stats grid
- ✅ Server returns updated statistics HTML
- ✅ HTMX swaps content in `.stats-grid` container

---

### 22.2 Which Actions Should Trigger Refresh?
**Test each action and verify refresh:**

| Action | Should Refresh? | Stats Affected |
|--------|----------------|----------------|
| ✅ Accept pending booking | YES | Pending ↓, Total ↑, Patients ↑ |
| ✅ Decline pending booking | YES | Pending ↓ |
| ✅ Create new appointment | YES | Total ↑ |
| ✅ Delete appointment | YES | Total ↓ |
| ❌ Update consultation status | NO | (No stat change) |
| ✅ Record payment (full) | YES | Unpaid ↓ |
| ✅ Record payment (partial) | NO | (Still unpaid) |
| ✅ Add patient | YES | Patients ↑ |
| ✅ Delete patient | YES | Patients ↓ |
| ✅ Add inventory | YES | Inventory ↑ |
| ✅ Delete inventory | YES | Inventory ↓ |
| ✅ Adjust stock (to low) | YES | Low Stock ↑ |
| ✅ Adjust stock (above reorder) | YES | Low Stock ↓ |
| ✅ POS sale (creates low stock) | YES | Low Stock ↑ |
| ✅ Create user (patient) | YES | Patients ↑ |
| ✅ Create service | NO | (No stat tracking) |

---

## 🧪 Module 23: Final Integration Test

### 23.1 Complete User Journey
**Test Steps:**
1. **Patient books appointment:**
   - Navigate to `/booking/`
   - Fill form and submit
   - Check email confirmation

2. **Staff accepts booking:**
   - Login as staff
   - View pending bookings
   - Accept the booking
   - Verify patient/records created
   - Check stats refresh

3. **Staff manages appointment:**
   - View appointments list
   - Update consultation status
   - Mark as done

4. **Staff records payment:**
   - View unpaid bills
   - Record payment
   - Verify billing updated
   - Check stats refresh

5. **Staff generates report:**
   - Download appointments PDF
   - Verify data accuracy

**Expected Outcomes:**
- ✅ All steps complete without errors
- ✅ Data flows correctly through system
- ✅ Auto-refresh works at each step
- ✅ Emails sent (if configured)
- ✅ Reports accurate

---

## 📋 Testing Summary Checklist

After completing all tests, verify:

### Core Functionality
- [ ] All forms validate correctly
- [ ] CRUD operations work (Create, Read, Update, Delete)
- [ ] Search and filtering functional
- [ ] Pagination works
- [ ] HTMX requests succeed

### New Features (Phases 2-8)
- [ ] Email notifications send successfully
- [ ] PDF/CSV reports download correctly
- [ ] Dashboard charts display accurate data
- [ ] Activity logging records created
- [ ] Custom validators prevent invalid data
- [ ] Error pages display when DEBUG=False
- [ ] Advanced search filters work

### Auto-Refresh (CRITICAL)
- [ ] **Statistics auto-refresh after relevant actions**
- [ ] Refresh triggers fire correctly
- [ ] HTMX swap updates stats without page reload
- [ ] No JavaScript errors in console

### Security
- [ ] CSRF protection active
- [ ] XSS prevention working
- [ ] SQL injection prevented
- [ ] Rate limiting functional
- [ ] Permissions enforced

### Performance
- [ ] Pages load quickly
- [ ] No excessive database queries
- [ ] Responsive on all devices
- [ ] No console errors

### Browser Compatibility
- [ ] Works in Chrome
- [ ] Works in Firefox
- [ ] Works in Edge
- [ ] Mobile responsive

---

## 🐛 Bug Reporting Template

If you find issues during testing, document them using this template:

```markdown
### Bug Report #[NUMBER]

**Module:** [e.g., Appointments Management]
**Severity:** [Critical / High / Medium / Low]
**Browser:** [Chrome 119 / Firefox 120 / etc.]

**Steps to Reproduce:**
1. Navigate to...
2. Click on...
3. Enter...
4. Observe...

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happened]

**Console Errors:**
[Paste any console errors]

**Screenshots:**
[Attach if applicable]

**Suggested Fix:**
[If you have ideas]
```

---

## ✅ Final Testing Certification

Once all tests pass, sign off:

```
✅ All modules tested: [Date]
✅ All features functional: [Date]
✅ Auto-refresh verified: [Date]
✅ No critical bugs: [Date]
✅ Ready for demonstration: [Date]

Tested by: ___________________
Date: ___________________
Signature: ___________________
```

---

## 📚 Additional Resources

- **Test Data:** Use `python manage.py loaddata` if fixtures available
- **Django Admin:** `/admin/` for direct database verification
- **Logs:** Check console output for errors
- **Database Browser:** Use DB Browser for SQLite to inspect data

---

**Project:** Romualdez Skin and Eye Clinic  
**Checklist Version:** 1.0.0  
**Last Updated:** November 3, 2025  
**Created by:** GitHub Copilot
