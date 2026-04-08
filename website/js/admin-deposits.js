/**
 * Admin Deposits Tab (Phase 9)
 * Real-time deposit verification and approval
 */

let allDeposits = {};

// Initialize Deposits Tab
export async function initDepositsTab() {
    const container = document.getElementById('deposits-tab-content');
    if (!container) return;
    
    container.innerHTML = `
        <div class="admin-section">
            <h3>💳 DEPOSIT VERIFICATION</h3>
            <div class="filter-bar">
                <select id="deposit-status-filter" class="filter-select">
                    <option value="">All Deposits</option>
                    <option value="pending">Pending Review</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                </select>
                <div class="stats-row">
                    <div class="stat-card">
                        <span class="stat-label">Pending Review</span>
                        <span class="stat-value" id="pending-deposits">0</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-label">Approved Today</span>
                        <span class="stat-value" id="approved-today">0</span>
                    </div>
                </div>
            </div>
            <div id="deposits-list" class="deposits-list"></div>
        </div>
    `;
    
    setupDepositFilters();
    loadDepositsRealtime();
}

// Setup deposit filters
function setupDepositFilters() {
    const statusFilter = document.getElementById('deposit-status-filter');
    statusFilter.addEventListener('change', () => filterAndDisplayDeposits());
}

// Load deposits in real-time
function loadDepositsRealtime() {
    const depositsRef = db.ref('deposits');
    
    depositsRef.on('value', (snapshot) => {
        allDeposits = {};
        snapshot.forEach((userSnapshot) => {
            const userId = userSnapshot.key;
            const userData = userSnapshot.val();
            
            if (userData && typeof userData === 'object') {
                Object.keys(userData).forEach(depositId => {
                    const depositData = userData[depositId];
                    allDeposits[`${userId}_${depositId}`] = {
                        id: depositId,
                        user_id: userId,
                        amount: 50, // Fixed deposit amount
                        status: depositData.status || 'pending',
                        screenshot_url: depositData.screenshot_url,
                        submission_date: depositData.submission_date,
                        approval_date: depositData.approval_date,
                        notes: depositData.notes || ''
                    };
                });
            }
        });
        
        updateDepositStats();
        filterAndDisplayDeposits();
    });
}

// Update deposit statistics
function updateDepositStats() {
    const pending = Object.values(allDeposits).filter(d => d.status === 'pending');
    const approvedToday = Object.values(allDeposits).filter(d => {
        if (d.status !== 'approved') return false;
        const approvalDate = new Date(d.approval_date);
        const today = new Date();
        return approvalDate.toDateString() === today.toDateString();
    });
    
    document.getElementById('pending-deposits').textContent = pending.length;
    document.getElementById('approved-today').textContent = approvedToday.length;
}

// Filter and display deposits
function filterAndDisplayDeposits() {
    const statusFilter = document.getElementById('deposit-status-filter').value;
    const depositsList = document.getElementById('deposits-list');
    
    let filteredDeposits = Object.values(allDeposits);
    
    if (statusFilter) {
        filteredDeposits = filteredDeposits.filter(d => d.status === statusFilter);
    }
    
    // Sort by date (newest first)
    filteredDeposits.sort((a, b) => new Date(b.submission_date) - new Date(a.submission_date));
    
    if (filteredDeposits.length === 0) {
        depositsList.innerHTML = '<div class="empty-state">No deposits to review</div>';
        return;
    }
    
    depositsList.innerHTML = filteredDeposits.map(deposit => `
        <div class="deposit-card status-${deposit.status}">
            <div class="deposit-header">
                <div class="deposit-info">
                    <h4>User ID: ${deposit.user_id}</h4>
                    <p class="deposit-id">Deposit: ${deposit.id}</p>
                </div>
                <div class="deposit-badge ${deposit.status}">
                    ${getDepositStatusBadge(deposit.status)}
                </div>
            </div>
            <div class="deposit-details">
                <div class="detail-row">
                    <span class="label">Amount:</span>
                    <span class="value">₹${deposit.amount}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Submitted:</span>
                    <span class="value">${formatDate(deposit.submission_date)}</span>
                </div>
                ${deposit.screenshot_url ? `
                    <div class="screenshot-container">
                        <label>Screenshot:</label>
                        <img src="${deposit.screenshot_url}" alt="Deposit Screenshot" class="deposit-screenshot">
                        <a href="${deposit.screenshot_url}" target="_blank" class="view-link">View Full Size</a>
                    </div>
                ` : ''}
                ${deposit.status === 'pending' ? `
                    <div class="action-buttons">
                        <button class="btn-approve" onclick="approveDeposit('${deposit.user_id}')">
                            ✅ Approve
                        </button>
                        <button class="btn-reject" onclick="rejectDeposit('${deposit.user_id}')">
                            ❌ Reject
                        </button>
                    </div>
                ` : `
                    <div class="detail-row">
                        <span class="label">Decision Date:</span>
                        <span class="value">${formatDate(deposit.approval_date)}</span>
                    </div>
                    ${deposit.notes ? `
                        <div class="detail-row">
                            <span class="label">Notes:</span>
                            <span class="value">${deposit.notes}</span>
                        </div>
                    ` : ''}
                `}
            </div>
        </div>
    `).join('');
}

function getDepositStatusBadge(status) {
    const badges = {
        'pending': '⏳ Pending Review',
        'approved': '✅ Approved',
        'rejected': '❌ Rejected'
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
window.approveDeposit = async (userId) => {
    const updates = {};
    updates[`users/${userId}/deposit_status`] = true;
    updates[`users/${userId}/balance`] = 20; // Starting bonus
    updates[`users/${userId}/deposit_approval_date`] = new Date().toISOString();
    
    try {
        await db.ref().update(updates);
        alert(`✅ Deposit approved, user balance updated`);
        filterAndDisplayDeposits();
    } catch (error) {
        alert('❌ Error approving deposit: ' + error.message);
    }
};

window.rejectDeposit = async (userId) => {
    const reason = prompt('Enter rejection reason:');
    if (!reason) return;
    
    const updates = {};
    updates[`deposits/${userId}`] = null; // Delete deposit record
    updates[`users/${userId}/deposit_status`] = false;
    
    try {
        await db.ref().update(updates);
        alert(`❌ Deposit rejected`);
        filterAndDisplayDeposits();
    } catch (error) {
        alert('❌ Error rejecting deposit: ' + error.message);
    }
};

export { loadDepositsRealtime, filterAndDisplayDeposits };
