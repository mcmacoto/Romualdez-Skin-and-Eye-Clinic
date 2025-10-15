/**
 * Inventory Transaction History Modal
 * Opens modal popup to display transaction history for inventory items
 */

(function() {
    'use strict';
    
    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        initializeHistoryModal();
    });
    
    function initializeHistoryModal() {
        // Create modal HTML if it doesn't exist
        if (!document.getElementById('history-modal')) {
            createModalHTML();
        }
        
        // Attach event listeners to all "View History" buttons
        attachHistoryButtonListeners();
    }
    
    function createModalHTML() {
        const modalHTML = `
            <div id="history-modal" class="history-modal">
                <div class="history-modal-content">
                    <div class="history-modal-header">
                        <h2 id="modal-title">Transaction History</h2>
                        <button class="history-modal-close" id="modal-close" aria-label="Close modal">
                            ×
                        </button>
                    </div>
                    <div class="history-modal-body" id="modal-body">
                        <div class="loading-spinner" style="text-align: center; padding: 3rem;">
                            <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #17a2b8;"></i>
                            <p style="margin-top: 1rem; color: #666;">Loading transaction history...</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Attach close button listener
        const closeBtn = document.getElementById('modal-close');
        const modal = document.getElementById('history-modal');
        
        closeBtn.addEventListener('click', closeModal);
        
        // Close modal when clicking outside content
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal();
            }
        });
        
        // Close modal with Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modal.classList.contains('show')) {
                closeModal();
            }
        });
    }
    
    function attachHistoryButtonListeners() {
        // Find all "View History" buttons
        const historyButtons = document.querySelectorAll('.view-history-btn');
        
        historyButtons.forEach(function(button) {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                const itemId = this.getAttribute('data-item-id');
                const itemName = this.getAttribute('data-item-name');
                
                if (itemId) {
                    openHistoryModal(itemId, itemName);
                }
            });
        });
    }
    
    function openHistoryModal(itemId, itemName) {
        const modal = document.getElementById('history-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        
        // Show modal
        modal.classList.add('show');
        
        // Update title
        modalTitle.textContent = `Transaction History - ${itemName}`;
        
        // Show loading spinner
        modalBody.innerHTML = `
            <div class="loading-spinner" style="text-align: center; padding: 3rem;">
                <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #17a2b8;"></i>
                <p style="margin-top: 1rem; color: #666;">Loading transaction history...</p>
            </div>
        `;
        
        // Fetch transaction history
        fetchTransactionHistory(itemId, modalBody);
    }
    
    function fetchTransactionHistory(itemId, modalBody) {
        // Build URL for history endpoint
        const baseUrl = window.location.origin;
        const adminPath = window.location.pathname.split('/').slice(0, 3).join('/'); // e.g., /admin/bookings
        const historyUrl = `${adminPath}/inventory/${itemId}/history/`;
        
        fetch(historyUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch transaction history');
                }
                return response.json();
            })
            .then(data => {
                displayTransactionHistory(data, modalBody);
            })
            .catch(error => {
                console.error('Error fetching transaction history:', error);
                modalBody.innerHTML = `
                    <div style="text-align: center; padding: 3rem; color: #dc3545;">
                        <i class="fas fa-exclamation-circle" style="font-size: 2rem;"></i>
                        <p style="margin-top: 1rem; font-weight: 500;">Failed to load transaction history</p>
                        <p style="font-size: 0.875rem; color: #666;">${error.message}</p>
                    </div>
                `;
            });
    }
    
    function displayTransactionHistory(data, modalBody) {
        if (!data.transactions || data.transactions.length === 0) {
            modalBody.innerHTML = `
                <div style="text-align: center; padding: 3rem; color: #666;">
                    <i class="fas fa-inbox" style="font-size: 2rem;"></i>
                    <p style="margin-top: 1rem; font-weight: 500;">No transaction history found</p>
                    <p style="font-size: 0.875rem;">This item has no recorded transactions yet.</p>
                </div>
            `;
            return;
        }
        
        // Build table HTML
        let tableHTML = `
            <div style="margin-bottom: 1rem;">
                <p style="margin: 0; color: #666;">
                    <strong>${data.item_name}</strong> (${data.item_category})
                </p>
                <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.875rem;">
                    Total transactions: ${data.transactions.length}
                </p>
            </div>
            <table class="history-table">
                <thead>
                    <tr>
                        <th>Date & Time</th>
                        <th>Type</th>
                        <th style="text-align: center;">Quantity</th>
                        <th>Performed By</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        data.transactions.forEach(function(transaction) {
            const typeClass = getTransactionTypeClass(transaction.type);
            const quantitySign = transaction.type === 'Stock In' ? '+' : '-';
            
            tableHTML += `
                <tr>
                    <td style="white-space: nowrap;">${transaction.date}</td>
                    <td>
                        <span class="transaction-type ${typeClass}">
                            ${transaction.type}
                        </span>
                    </td>
                    <td style="text-align: center; font-weight: 600;">
                        ${quantitySign}${transaction.quantity}
                    </td>
                    <td>${transaction.performed_by}</td>
                    <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(transaction.notes)}">
                        ${transaction.notes || '-'}
                    </td>
                </tr>
            `;
        });
        
        tableHTML += `
                </tbody>
            </table>
            <div style="margin-top: 1.5rem; text-align: center;">
                <button onclick="window.print()" class="btn-view-history" style="background: #6c757d;">
                    <i class="fas fa-print"></i> Print History
                </button>
            </div>
        `;
        
        modalBody.innerHTML = tableHTML;
    }
    
    function getTransactionTypeClass(type) {
        switch (type) {
            case 'Stock In':
                return 'transaction-in';
            case 'Stock Out':
                return 'transaction-out';
            case 'Adjustment':
                return 'transaction-adjustment';
            default:
                return '';
        }
    }
    
    function closeModal() {
        const modal = document.getElementById('history-modal');
        modal.classList.remove('show');
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Export for global access
    window.InventoryModal = {
        open: openHistoryModal,
        close: closeModal
    };
})();
