// Billing Inline Edit for Service Fee and Medicine Fee
(function() {
    'use strict';
    
    document.addEventListener('DOMContentLoaded', function() {
        // Add event listeners to all billing fee inputs
        const feeInputs = document.querySelectorAll('.billing-fee-input');
        
        feeInputs.forEach(input => {
            // Store original value
            input.dataset.originalValue = input.value;
            
            // Add change event listener
            input.addEventListener('change', function() {
                updateBillingFee(this);
            });
            
            // Add blur event to save on focus loss
            input.addEventListener('blur', function() {
                if (this.value !== this.dataset.originalValue) {
                    updateBillingFee(this);
                }
            });
            
            // Prevent form submission on Enter key
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.blur();
                }
            });
        });
    });
    
    function updateBillingFee(input) {
        const billingId = input.dataset.billingId;
        const feeType = input.dataset.feeType;
        const newValue = parseFloat(input.value);
        
        // Validation
        if (isNaN(newValue) || newValue < 0) {
            alert('Please enter a valid positive number');
            input.value = input.dataset.originalValue;
            return;
        }
        
        // Get both service fee and medicine fee from the row
        const row = input.closest('tr');
        const serviceFeeInput = row.querySelector('[data-fee-type="service"]');
        const medicineFeeInput = row.querySelector('[data-fee-type="medicine"]');
        
        const serviceFee = parseFloat(serviceFeeInput.value);
        const medicineFee = parseFloat(medicineFeeInput.value);
        
        // Visual feedback
        input.style.borderColor = '#ffc107';
        input.style.backgroundColor = '#fff3cd';
        input.disabled = true;
        
        // Send AJAX request
        fetch(`/api/billing/${billingId}/update-fees/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                service_fee: serviceFee,
                medicine_fee: medicineFee
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Success feedback
                input.style.borderColor = '#28a745';
                input.style.backgroundColor = '#d4edda';
                input.dataset.originalValue = input.value;
                
                // Update the total amount and balance in the row
                updateRowTotals(row, data.new_balance);
                
                // Show success notification
                showNotification('Billing fees updated successfully!', 'success');
                
                // Reset styling after 2 seconds
                setTimeout(() => {
                    input.style.borderColor = '#ddd';
                    input.style.backgroundColor = '#fff';
                }, 2000);
                
                // Reload the page to reflect all changes
                setTimeout(() => {
                    location.reload();
                }, 1500);
            } else {
                throw new Error(data.error || 'Failed to update fees');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            input.style.borderColor = '#dc3545';
            input.style.backgroundColor = '#f8d7da';
            alert('Error updating fees: ' + error.message);
            input.value = input.dataset.originalValue;
            setTimeout(() => {
                input.style.borderColor = '#ddd';
                input.style.backgroundColor = '#fff';
            }, 2000);
        })
        .finally(() => {
            input.disabled = false;
        });
    }
    
    function updateRowTotals(row, newBalance) {
        // Find and update the balance cell in the row
        const cells = row.querySelectorAll('td');
        // Balance is typically after service fee, medicine fee, total amount
        // You may need to adjust the index based on your table structure
        cells.forEach(cell => {
            if (cell.textContent.includes('₱') && !cell.querySelector('input')) {
                // This might be the balance cell - update it
                const balanceMatch = cell.textContent.match(/₱[\d,]+\.\d{2}/);
                if (balanceMatch) {
                    cell.textContent = cell.textContent.replace(
                        balanceMatch[0],
                        `₱${newBalance.toFixed(2)}`
                    );
                }
            }
        });
    }
    
    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `billing-notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
            z-index: 9999;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            animation: slideIn 0.3s ease;
        `;
        
        if (type === 'success') {
            notification.style.backgroundColor = '#28a745';
        } else {
            notification.style.backgroundColor = '#dc3545';
        }
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
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
})();
