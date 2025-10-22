// Get CSRF token for POST requests
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    
    toastMessage.textContent = message;
    toast.className = `toast ${type} active`;
    
    setTimeout(() => {
        toast.classList.remove('active');
    }, 4000);
}

// Open pending bookings modal
async function openPendingBookingsModal() {
    const modal = document.getElementById('pendingBookingsModal');
    const overlay = document.getElementById('modalOverlay');
    const modalBody = document.getElementById('modalBody');
    
    // Show modal with loading state
    modal.classList.add('active');
    overlay.classList.add('active');
    
    // Fetch pending bookings
    try {
        const response = await fetch('/api/pending-bookings/');
        const data = await response.json();
        
        if (data.success) {
            renderBookings(data.bookings);
            document.getElementById('modal-pending-count').textContent = data.count;
        } else {
            modalBody.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-circle"></i>
                    <h3>Error Loading Bookings</h3>
                    <p>${data.error}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error fetching bookings:', error);
        modalBody.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <h3>Error Loading Bookings</h3>
                <p>Failed to fetch pending bookings. Please try again.</p>
            </div>
        `;
    }
}

// Close modal
function closePendingBookingsModal() {
    document.getElementById('pendingBookingsModal').classList.remove('active');
    document.getElementById('modalOverlay').classList.remove('active');
}

// Render bookings table
function renderBookings(bookings) {
    const modalBody = document.getElementById('modalBody');
    
    if (bookings.length === 0) {
        modalBody.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-check-circle"></i>
                <h3>No Pending Bookings</h3>
                <p>All bookings have been processed.</p>
            </div>
        `;
        return;
    }
    
    const tableHTML = `
        <table class="modal-table">
            <thead>
                <tr>
                    <th>Patient Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Service</th>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Notes</th>
                    <th style="text-align: center;">Actions</th>
                </tr>
            </thead>
            <tbody>
                ${bookings.map(booking => `
                    <tr id="booking-row-${booking.id}">
                        <td><strong>${booking.patient_name}</strong></td>
                        <td>${booking.patient_email}</td>
                        <td>${booking.patient_phone}</td>
                        <td>${booking.service}</td>
                        <td>${formatDate(booking.date)}</td>
                        <td>${booking.time}</td>
                        <td style="max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${booking.notes || 'No notes'}">${booking.notes || '-'}</td>
                        <td style="text-align: center;">
                            <div class="action-buttons" style="justify-content: center;">
                                <button class="btn-accept" onclick="acceptBooking(${booking.id})" id="accept-${booking.id}">
                                    <i class="fas fa-check"></i> Accept
                                </button>
                                <button class="btn-decline" onclick="declineBooking(${booking.id})" id="decline-${booking.id}">
                                    <i class="fas fa-times"></i> Decline
                                </button>
                            </div>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    modalBody.innerHTML = tableHTML;
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

// Accept booking
async function acceptBooking(bookingId) {
    const acceptBtn = document.getElementById(`accept-${bookingId}`);
    const declineBtn = document.getElementById(`decline-${bookingId}`);
    
    // Disable buttons and show loading
    acceptBtn.disabled = true;
    declineBtn.disabled = true;
    acceptBtn.innerHTML = '<span class="loading-spinner"></span> Processing...';
    
    try {
        const response = await fetch(`/api/bookings/${bookingId}/accept/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json',
            },
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            
            // Remove row with animation
            const row = document.getElementById(`booking-row-${bookingId}`);
            row.style.transition = 'all 0.3s ease';
            row.style.opacity = '0';
            row.style.transform = 'translateX(-20px)';
            
            setTimeout(() => {
                row.remove();
                
                // Update dashboard statistics from API response
                if (data.stats) {
                    // Update pending bookings count
                    const pendingEl = document.getElementById('pending-count');
                    if (pendingEl) {
                        pendingEl.textContent = data.stats.pending_bookings;
                    }
                    
                    // Update total appointments count
                    const totalAppointmentsEls = document.querySelectorAll('.stat-card .stat-number');
                    if (totalAppointmentsEls[0] && data.stats.total_appointments !== undefined) {
                        totalAppointmentsEls[0].textContent = data.stats.total_appointments;
                    }
                    
                    // Update confirmed appointments count (if exists)
                    const confirmedEl = document.querySelectorAll('.stat-card .stat-number')[2];
                    if (confirmedEl && data.stats.confirmed_appointments !== undefined) {
                        confirmedEl.textContent = data.stats.confirmed_appointments;
                    }
                }
                
                // Update pending count
                updatePendingCount();
                
                // Check if table is empty
                const tbody = document.querySelector('.modal-table tbody');
                if (tbody && tbody.children.length === 0) {
                    document.getElementById('modalBody').innerHTML = `
                        <div class="empty-state">
                            <i class="fas fa-check-circle"></i>
                            <h3>No Pending Bookings</h3>
                            <p>All bookings have been processed.</p>
                        </div>
                    `;
                    document.getElementById('modal-pending-count').textContent = '0';
                }
            }, 300);
            
        } else {
            showToast(data.error, 'error');
            acceptBtn.disabled = false;
            declineBtn.disabled = false;
            acceptBtn.innerHTML = '<i class="fas fa-check"></i> Accept';
        }
    } catch (error) {
        console.error('Error accepting booking:', error);
        showToast('Failed to accept booking. Please try again.', 'error');
        acceptBtn.disabled = false;
        declineBtn.disabled = false;
        acceptBtn.innerHTML = '<i class="fas fa-check"></i> Accept';
    }
}

// Decline booking
async function declineBooking(bookingId) {
    if (!confirm('Are you sure you want to decline this booking?')) {
        return;
    }
    
    const acceptBtn = document.getElementById(`accept-${bookingId}`);
    const declineBtn = document.getElementById(`decline-${bookingId}`);
    
    // Disable buttons and show loading
    acceptBtn.disabled = true;
    declineBtn.disabled = true;
    declineBtn.innerHTML = '<span class="loading-spinner"></span> Processing...';
    
    try {
        const response = await fetch(`/api/bookings/${bookingId}/decline/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json',
            },
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            
            // Remove row with animation
            const row = document.getElementById(`booking-row-${bookingId}`);
            row.style.transition = 'all 0.3s ease';
            row.style.opacity = '0';
            row.style.transform = 'translateX(20px)';
            
            setTimeout(() => {
                row.remove();
                
                // Update pending count
                updatePendingCount();
                
                // Check if table is empty
                const tbody = document.querySelector('.modal-table tbody');
                if (tbody && tbody.children.length === 0) {
                    document.getElementById('modalBody').innerHTML = `
                        <div class="empty-state">
                            <i class="fas fa-check-circle"></i>
                            <h3>No Pending Bookings</h3>
                            <p>All bookings have been processed.</p>
                        </div>
                    `;
                    document.getElementById('modal-pending-count').textContent = '0';
                }
            }, 300);
            
        } else {
            showToast(data.error, 'error');
            acceptBtn.disabled = false;
            declineBtn.disabled = false;
            declineBtn.innerHTML = '<i class="fas fa-times"></i> Decline';
        }
    } catch (error) {
        console.error('Error declining booking:', error);
        showToast('Failed to decline booking. Please try again.', 'error');
        acceptBtn.disabled = false;
        declineBtn.disabled = false;
        declineBtn.innerHTML = '<i class="fas fa-times"></i> Decline';
    }
}

// Update pending count on dashboard
async function updatePendingCount() {
    try {
        const response = await fetch('/api/pending-bookings/');
        const data = await response.json();
        
        if (data.success) {
            const pendingCountElement = document.getElementById('pending-count');
            if (pendingCountElement) {
                pendingCountElement.textContent = data.count;
            }
            
            // Update modal count
            document.getElementById('modal-pending-count').textContent = data.count;
        }
    } catch (error) {
        console.error('Error updating pending count:', error);
    }
}

// Close modal on Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closePendingBookingsModal();
        closePatientsModal();
        closeMedicalRecordsModal();
        closeInventoryModal();
    }
});

// ===== PATIENTS MODAL =====
async function openPatientsModal() {
    const modal = document.getElementById('patientsModal');
    const overlay = document.getElementById('modalOverlay');
    const modalBody = document.getElementById('patientsModalBody');
    
    modal.classList.add('active');
    overlay.classList.add('active');
    
    try {
        const response = await fetch('/api/patients/');
        const data = await response.json();
        
        if (data.success) {
            renderPatients(data.patients);
            document.getElementById('patients-modal-count').textContent = data.count;
        } else {
            modalBody.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-circle"></i>
                    <h3>Error Loading Patients</h3>
                    <p>${data.error}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error fetching patients:', error);
        modalBody.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <h3>Error Loading Patients</h3>
                <p>Failed to fetch patient data. Please try again.</p>
            </div>
        `;
    }
}

function closePatientsModal() {
    document.getElementById('patientsModal').classList.remove('active');
    document.getElementById('modalOverlay').classList.remove('active');
}

function renderPatients(patients) {
    const modalBody = document.getElementById('patientsModalBody');
    
    if (patients.length === 0) {
        modalBody.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-user-slash"></i>
                <h3>No Patients Found</h3>
                <p>No patient profiles have been created yet.</p>
            </div>
        `;
        return;
    }
    
    const tableHTML = `
        <div style="margin-bottom: 1rem;">
            <input type="text" id="patientSearchInput" placeholder="🔍 Search patients by name, email, or phone..." 
                   style="width: 100%; padding: 0.75rem; border: 2px solid #dee2e6; border-radius: 8px; font-size: 0.95rem;"
                   onkeyup="filterPatientsTable()">
        </div>
        <table class="modal-table" id="patientsTable">
            <thead>
                <tr>
                    <th>Patient Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Gender</th>
                    <th>Date of Birth</th>
                    <th>Medical Records</th>
                    <th>Address</th>
                    <th>Emergency Contact</th>
                    <th>Created At</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${patients.map(patient => `
                    <tr data-search="${patient.name.toLowerCase()} ${patient.email.toLowerCase()} ${patient.phone}">
                        <td><strong>${patient.name}</strong></td>
                        <td>${patient.email}</td>
                        <td>${patient.phone}</td>
                        <td>${patient.gender}</td>
                        <td>${patient.date_of_birth}</td>
                        <td style="text-align: center;">
                            <span class="badge badge-info clickable" onclick="viewPatientRecords(${patient.id}, '${patient.name}')" style="cursor: pointer;" title="Click to view medical records">${patient.medical_records_count} record(s)</span>
                        </td>
                        <td style="max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${patient.address}">${patient.address}</td>
                        <td>${patient.emergency_contact}</td>
                        <td>${patient.created_at}</td>
                        <td style="text-align: center;">
                            <button class="action-btn view-btn" onclick="viewPatientProfile(${patient.id})" title="View Profile">
                                <i class="fas fa-eye"></i>
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    modalBody.innerHTML = tableHTML;
}

// ===== MEDICAL RECORDS MODAL =====
async function openMedicalRecordsModal() {
    const modal = document.getElementById('medicalRecordsModal');
    const overlay = document.getElementById('modalOverlay');
    const modalBody = document.getElementById('medicalRecordsModalBody');
    
    modal.classList.add('active');
    overlay.classList.add('active');
    
    try {
        const response = await fetch('/api/medical-records/');
        const data = await response.json();
        
        if (data.success) {
            renderMedicalRecords(data.records);
            document.getElementById('records-modal-count').textContent = data.count;
        } else {
            modalBody.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-circle"></i>
                    <h3>Error Loading Records</h3>
                    <p>${data.error}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error fetching medical records:', error);
        modalBody.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <h3>Error Loading Records</h3>
                <p>Failed to fetch medical records. Please try again.</p>
            </div>
        `;
    }
}

function closeMedicalRecordsModal() {
    document.getElementById('medicalRecordsModal').classList.remove('active');
    document.getElementById('modalOverlay').classList.remove('active');
}

function renderMedicalRecords(records) {
    const modalBody = document.getElementById('medicalRecordsModalBody');
    
    if (records.length === 0) {
        modalBody.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-file-medical"></i>
                <h3>No Medical Records Found</h3>
                <p>No medical records have been created yet.</p>
            </div>
        `;
        return;
    }
    
    const tableHTML = `
        <div style="margin-bottom: 1rem;">
            <input type="text" id="medicalRecordsSearchInput" placeholder="🔍 Search medical records by patient name or diagnosis..." 
                   style="width: 100%; padding: 0.75rem; border: 2px solid #dee2e6; border-radius: 8px; font-size: 0.95rem;"
                   onkeyup="filterMedicalRecordsTable()">
        </div>
        <table class="modal-table" id="medicalRecordsTable">
            <thead>
                <tr>
                    <th>Patient Name</th>
                    <th>Visit Date</th>
                    <th>Chief Complaint</th>
                    <th>Symptoms</th>
                    <th>Diagnosis</th>
                    <th>Treatment Plan</th>
                    <th>Prescriptions</th>
                    <th>Images</th>
                    <th>Notes</th>
                    <th>Created By</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${records.map(record => `
                    <tr data-search="${record.patient_name.toLowerCase()} ${record.diagnosis.toLowerCase()} ${record.chief_complaint.toLowerCase()}">
                        <td><strong>${record.patient_name}</strong><br><small>${record.patient_email}</small></td>
                        <td>${record.visit_date}</td>
                        <td style="max-width: 150px;" title="${record.chief_complaint}">${truncate(record.chief_complaint, 30)}</td>
                        <td style="max-width: 150px;" title="${record.symptoms}">${truncate(record.symptoms, 30)}</td>
                        <td>${record.diagnosis}</td>
                        <td style="max-width: 150px;" title="${record.treatment_plan}">${truncate(record.treatment_plan, 30)}</td>
                        <td style="text-align: center;">
                            <span class="badge badge-success">${record.prescriptions_count} item(s)</span>
                        </td>
                        <td style="text-align: center;">
                            ${record.images_count > 0 ? 
                                `<span class="badge badge-info" style="cursor: pointer;" onclick="showMedicalImages(${record.id}, '${record.patient_name}', ${JSON.stringify(record.images).replace(/"/g, '&quot;')})">
                                    <i class="fas fa-images"></i> ${record.images_count} image(s)
                                </span>` 
                                : '<span style="color: #999;">No images</span>'
                            }
                        </td>
                        <td style="max-width: 150px;" title="${record.notes}">${truncate(record.notes, 30)}</td>
                        <td>${record.created_by}</td>
                        <td>
                            <a href="/admin/bookings/medicalrecord/${record.id}/change/" class="btn-action" title="View Details">
                                <i class="fas fa-eye"></i>
                            </a>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    modalBody.innerHTML = tableHTML;
}

// Show medical images in a lightbox
function showMedicalImages(recordId, patientName, images) {
    const modal = document.createElement('div');
    modal.className = 'image-lightbox';
    modal.innerHTML = `
        <div class="lightbox-content">
            <div class="lightbox-header">
                <h3><i class="fas fa-images"></i> Medical Images - ${patientName}</h3>
                <button onclick="this.closest('.image-lightbox').remove()" class="lightbox-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="lightbox-body">
                <div class="images-grid">
                    ${images.map(img => `
                        <div class="image-card">
                            <img src="${img.url}" alt="${img.title}" onclick="window.open('${img.url}', '_blank')">
                            <div class="image-info">
                                <strong>${img.title}</strong>
                                <small>${img.image_type} - ${img.uploaded_at}</small>
                                ${img.description ? `<p>${img.description}</p>` : ''}
                                <small>Uploaded by: ${img.uploaded_by}</small>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    setTimeout(() => modal.classList.add('active'), 10);
}

// ===== INVENTORY MODAL =====
async function openInventoryModal() {
    const modal = document.getElementById('inventoryModal');
    const overlay = document.getElementById('modalOverlay');
    const modalBody = document.getElementById('inventoryModalBody');
    
    modal.classList.add('active');
    overlay.classList.add('active');
    
    try {
        const response = await fetch('/api/inventory/');
        const data = await response.json();
        
        if (data.success) {
            renderInventory(data.inventory);
            document.getElementById('inventory-modal-count').textContent = data.count;
        } else {
            modalBody.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-circle"></i>
                    <h3>Error Loading Inventory</h3>
                    <p>${data.error}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error fetching inventory:', error);
        modalBody.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <h3>Error Loading Inventory</h3>
                <p>Failed to fetch inventory data. Please try again.</p>
            </div>
        `;
    }
}

function closeInventoryModal() {
    document.getElementById('inventoryModal').classList.remove('active');
    document.getElementById('modalOverlay').classList.remove('active');
}

function renderInventory(inventory) {
    const modalBody = document.getElementById('inventoryModalBody');
    
    if (inventory.length === 0) {
        modalBody.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-box-open"></i>
                <h3>No Inventory Items</h3>
                <p>No inventory items have been added yet.</p>
            </div>
        `;
        return;
    }
    
    const tableHTML = `
        <div style="margin-bottom: 1rem;">
            <input type="text" id="inventorySearchInput" placeholder="🔍 Search inventory by name, category, or status..." 
                   style="width: 100%; padding: 0.75rem; border: 2px solid #dee2e6; border-radius: 8px; font-size: 0.95rem;"
                   onkeyup="filterInventoryTable()">
        </div>
        <table class="modal-table" id="inventoryTable">
            <thead>
                <tr>
                    <th>Item Name</th>
                    <th>Category</th>
                    <th>Quantity</th>
                    <th>Unit Price</th>
                    <th>Status</th>
                    <th>Supplier</th>
                    <th>Expiry Date</th>
                    <th>Last Updated</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${inventory.map(item => `
                    <tr data-search="${item.name.toLowerCase()} ${item.category.toLowerCase()} ${item.status.toLowerCase()}">
                        <td><strong>${item.name}</strong></td>
                        <td>${item.category}</td>
                        <td style="text-align: center;">${item.quantity}</td>
                        <td>₱${item.unit_price}</td>
                        <td>
                            <span class="status-badge status-${item.status.toLowerCase().replace(' ', '-')}">${item.status}</span>
                        </td>
                        <td>${item.supplier}</td>
                        <td>${item.expiry_date}</td>
                        <td>${item.last_updated}</td>
                        <td style="text-align: center;">
                            <a href="/admin/bookings/inventory/${item.id}/change/" class="btn-action" title="View Details">
                                <i class="fas fa-eye"></i>
                            </a>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    modalBody.innerHTML = tableHTML;
}

// ===== POS REVENUE MODAL =====
async function openPOSRevenueModal() {
    const modal = document.getElementById('posRevenueModal');
    const overlay = document.getElementById('modalOverlay');
    const modalBody = document.getElementById('posRevenueModalBody');
    
    modal.classList.add('active');
    overlay.classList.add('active');
    
    try {
        const response = await fetch('/api/pos-sales/');
        const data = await response.json();
        
        if (data.success) {
            renderPOSSales(data.sales);
            document.getElementById('pos-modal-count').textContent = data.count;
        } else {
            modalBody.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-circle"></i>
                    <h3>Error Loading POS Sales</h3>
                    <p>${data.error}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error fetching POS sales:', error);
        modalBody.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <h3>Error Loading POS Sales</h3>
                <p>Failed to fetch POS sales data. Please try again.</p>
            </div>
        `;
    }
}

function closePOSRevenueModal() {
    document.getElementById('posRevenueModal').classList.remove('active');
    document.getElementById('modalOverlay').classList.remove('active');
}

function renderPOSSales(sales) {
    const modalBody = document.getElementById('posRevenueModalBody');
    
    if (sales.length === 0) {
        modalBody.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-receipt"></i>
                <h3>No POS Sales Found</h3>
                <p>No point-of-sale transactions have been recorded yet.</p>
            </div>
        `;
        return;
    }
    
    const tableHTML = `
        <div style="margin-bottom: 1rem;">
            <input type="text" id="posSearchInput" placeholder="🔍 Search sales by customer, status, or payment method..." 
                   style="width: 100%; padding: 0.75rem; border: 2px solid #dee2e6; border-radius: 8px; font-size: 0.95rem;"
                   onkeyup="filterPOSTable()">
        </div>
        <table class="modal-table" id="posTable">
            <thead>
                <tr>
                    <th>Sale ID</th>
                    <th>Customer</th>
                    <th>Total Amount</th>
                    <th>Payment Method</th>
                    <th>Status</th>
                    <th>Sale Date</th>
                    <th>Items</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${sales.map(sale => `
                    <tr data-search="${sale.customer_name.toLowerCase()} ${sale.status.toLowerCase()} ${sale.payment_method.toLowerCase()}">
                        <td><strong>#${sale.id}</strong></td>
                        <td>${sale.customer_name}</td>
                        <td>₱${sale.total_amount}</td>
                        <td>${sale.payment_method}</td>
                        <td>
                            <span class="status-badge status-${sale.status.toLowerCase()}">${sale.status}</span>
                        </td>
                        <td>${sale.sale_date}</td>
                        <td style="text-align: center;">
                            <span class="badge badge-secondary">${sale.items_count} item(s)</span>
                        </td>
                        <td style="text-align: center;">
                            <a href="/admin/bookings/possale/${sale.id}/change/" class="btn-action" title="View Details">
                                <i class="fas fa-eye"></i>
                            </a>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    modalBody.innerHTML = tableHTML;
}

// ===== TABLE FILTERING =====
function filterTable(tableId, inputId) {
    const input = document.getElementById(inputId);
    const filter = input.value.toLowerCase();
    const table = document.getElementById(tableId);
    const tr = table.getElementsByTagName("tr");

    for (let i = 1; i < tr.length; i++) {
        const row = tr[i];
        const searchData = row.getAttribute('data-search');
        if (searchData) {
            if (searchData.includes(filter)) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        }
    }
}

function filterPatientsTable() {
    filterTable('patientsTable', 'patientSearchInput');
}

function filterMedicalRecordsTable() {
    filterTable('medicalRecordsTable', 'medicalRecordsSearchInput');
}

function filterInventoryTable() {
    filterTable('inventoryTable', 'inventorySearchInput');
}

function filterPOSTable() {
    filterTable('posTable', 'posSearchInput');
}

// Truncate text utility
function truncate(text, length) {
    if (!text) return '-';
    return text.length > length ? text.substring(0, length) + '...' : text;
}
