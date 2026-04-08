/**
 * Admin Withdrawals Tab (Phase 9)
 * Real-time withdrawal request management and approval workflow
 */

let allWithdrawals = {};

// Initialize Withdrawals Tab
export async function initWithdrawalsTab() {
    const container = document.getElementById('withdrawals-tab-content');
    if (!container) return;
    
    container.innerHTML = `
        <div class="admin-section">
            <h3>💸 WITHDRAWAL MANAGEMENT</h3>
            <div class="filter-bar">
                <select id="withdrawal-status-filter" class="filter-select">
                    <option value="">All Requests</option>
                    <option value="pending">Pending</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                    <option value="processed">Processed</option>
                </select>
                <div class="stats-row">
                    <div class="stat-card">
                        <span class="stat-label">Total Pending</span>
                        <span class="stat-value" id="total-pending">0</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-label">Total Amount</span>
                        <span class="stat-value" id="total-amount">₹0</span>
                    </div>
                </div>
            </div>
            <div id="withdrawals-list" class="withdrawals-list"></div>
        </div>
    `;
    
    setupWithdrawalFilters();
    loadWithdrawalsRealtime();
}

// Setup withdrawal status filter
function setupWithdrawalFilters() {
    const statusFilter = document.getElementById('withdrawal-status-filter');
    statusFilter.addEventListener('change', () => filterAndDisplayWithdrawals());
}

// Load withdrawals in real-time
function loadWithdrawalsRealtime() {
    const withdrawalsRef = db.ref('withdrawal_requests');
    
    withdrawalsRef.on('value', (snapshot) => {
        allWithdrawals = {};
        snapshot.forEach((childSnapshot) => {
            const withdrawalId = childSnapshot.key;
            const withdrawalData = childSnapshot.val();
            allWithdrawals[withdrawalId] = {
                id: withdrawalId,
                user_id: withdrawalData.user_id,
                amount: withdrawalData.amount,
                upi: withdrawalData.upi,
                status: withdrawalData.status || 'pending',
                request_date: withdrawalData.request_date,
                approved_date: withdrawalData.approved_date,
                processed_date: withdrawalData.processed_date,
                notes: withdrawalData.notes || ''
            };
        });
        
        updateWithdrawalStats();
        filterAndDisplayWithdrawals();
    });
}

// Update withdrawal statistics
function updateWithdrawalStats() {
    const pending = Object.values(allWithdrawals).filter(w => w.status === 'pending');
    const totalAmount = pending.reduce((sum, w) => sum + w.amount, 0);
    
    document.getElementById('total-pending').textContent = pending.length;
    document.getElementById('total-amount').textContent = `₹${totalAmount.toFixed(2)}`;
}

// Filter and display withdrawals
function filterAndDisplayWithdrawals() {
    const statusFilter = document.getElementById('withdrawal-status-filter').value;
    const withdrawalsList = document.getElementById('withdrawals-list');
    
    let filteredWithdrawals = Object.values(allWithdrawals);
    
    if (statusFilter) {
        filteredWithdrawals = filteredWithdrawals.filter(w => w.status === statusFilter);
    }
    
    // Sort by date (newest first)
    filteredWithdrawals.sort((a, b) => new Date(b.request_date) - new Date(a.request_date));
    
    if (filteredWithdrawals.length === 0) {
        withdrawalsList.innerHTML = '<div class="empty-state">No withdrawal requests</div>';
        return;
    }
    
    withdrawalsList.innerHTML = filteredWithdrawals.map(withdrawal => `
        <div class="withdrawal-card status-${withdrawal.status}">
            <div class="withdrawal-header">
                <div class="withdrawal-info">
                    <h4>User ID: ${withdrawal.user_id}</h4>
                    <p class="withdrawal-id">Request: ${withdrawal.id}</p>
                </div>
                <div class="withdrawal-badge ${withdrawal.status}">
                    ${getStatusBadge(withdrawal.status)}
                </div>
            </div>
            <div class="withdrawal-details">
                <div class="detail-row">
                    <span class="label">Amount:</span>
                    <span class="value">₹${withdrawal.amount.toFixed(2)}</span>
                </div>
                <div class="detail-row">
                    <span class="label">UPI:</span>
                    <span class="value mono">${withdrawal.upi}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Requested:</span>
                    <span class="value">${formatDate(withdrawal.request_date)}</span>
                </div>
                ${withdrawal.status === 'pending' ? `
                    <div class="action-buttons">
                        <button class="btn-approve" onclick="approveWithdrawal('${withdrawal.id}', '${withdrawal.user_id}')">
                            ✅ Approve
                        </button>
                        <button class="btn-reject" onclick="rejectWithdrawal('${withdrawal.id}', '${withdrawal.user_id}')">
                            ❌ Reject
                        </button>
                    </div>
                ` : `
                    <div class="detail-row">
                        <span class="label">Decision Date:</span>
                        <span class="value">${formatDate(withdrawal.approved_date || withdrawal.processed_date)}</span>
                    </div>
                `}
            </div>
        </div>
    `).join('');
}

function getStatusBadge(status) {
    const badges = {
        'pending': '⏳ Pending',
        'approved': '✅ Approved',
        'rejected': '❌ Rejected',
        'processed': '💰 Processed'
    };
    return badges[status] || status;
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    try {
        return new Date(dateStr).toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return dateStr;
    }
}

// Global functions for button handlers
window.approveWithdrawal = async (withdrawalId, userId) => {
    const updates = {};
    updates[`withdrawal_requests/${withdrawalId}/status`] = 'approved';
    updates[`withdrawal_requests/${withdrawalId}/approved_date`] = new Date().toISOString();
    
    try {
        await db.ref().update(updates);
        alert(`✅ Withdrawal approved`);
        filterAndDisplayWithdrawals();
    } catch (error) {
        alert('❌ Error approving withdrawal: ' + error.message);
    }
};

window.rejectWithdrawal = async (withdrawalId, userId) => {
    const reason = prompt('Enter rejection reason:');
    if (!reason) return;
    
    const updates = {};
    updates[`withdrawal_requests/${withdrawalId}/status`] = 'rejected';
    updates[`withdrawal_requests/${withdrawalId}/processed_date`] = new Date().toISOString();
    updates[`withdrawal_requests/${withdrawalId}/notes`] = reason;
    
    try {
        await db.ref().update(updates);
        alert(`❌ Withdrawal rejected`);
        filterAndDisplayWithdrawals();
    } catch (error) {
        alert('❌ Error rejecting withdrawal: ' + error.message);
    }
};

export { loadWithdrawalsRealtime, filterAndDisplayWithdrawals };
