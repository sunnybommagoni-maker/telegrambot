// Dashboard Core
const db = window.db;
const auth = window.auth;

// Initialize Dashboard Tab
export async function initDashboardTab() {
    const container = document.getElementById('dashboard-tab-content');
    if (!container) return;
    
    container.innerHTML = `
        <div class="admin-dashboard">
            <h3>📊 ADMIN DASHBOARD</h3>
            
            <div class="dashboard-grid">
                <div class="dashboard-card">
                    <div class="card-header">
                        <h4>👥 Total Users</h4>
                    </div>
                    <div class="card-content">
                        <div class="metric-large" id="total-users">0</div>
                        <div class="metric-small">Active: <span id="active-users">0</span></div>
                    </div>
                </div>
                
                <div class="dashboard-card">
                    <div class="card-header">
                        <h4>💰 Total Earnings</h4>
                    </div>
                    <div class="card-content">
                        <div class="metric-large" id="total-earnings">₹0</div>
                        <div class="metric-small">Distributed: <span id="total-distributed">₹0</span></div>
                    </div>
                </div>
                
                <div class="dashboard-card">
                    <div class="card-header">
                        <h4>📊 Tasks Completed</h4>
                    </div>
                    <div class="card-content">
                        <div class="metric-large" id="total-tasks">0</div>
                        <div class="metric-small">Avg per user: <span id="avg-tasks">0</span></div>
                    </div>
                </div>
                
                <div class="dashboard-card">
                    <div class="card-header">
                        <h4>🤝 Referral Network</h4>
                    </div>
                    <div class="card-content">
                        <div class="metric-large" id="total-referrals">0</div>
                        <div class="metric-small">Bonus Awarded: <span id="referral-bonus">₹0</span></div>
                    </div>
                </div>
                
                <div class="dashboard-card">
                    <div class="card-header">
                        <h4>💳 Deposits</h4>
                    </div>
                    <div class="card-content">
                        <div class="metric-large" id="deposits-approved">0</div>
                        <div class="metric-small">Pending: <span id="deposits-pending">0</span></div>
                    </div>
                </div>
                
                <div class="dashboard-card">
                    <div class="card-header">
                        <h4>💸 Withdrawals</h4>
                    </div>
                    <div class="card-content">
                        <div class="metric-large" id="withdrawals-approved">0</div>
                        <div class="metric-small">Amount: <span id="withdrawal-amount">₹0</span></div>
                    </div>
                </div>
            </div>
            
            <div class="recent-activity">
                <h4>📌 Recent Activity</h4>
                <div id="activity-feed" class="activity-feed"></div>
            </div>
        </div>
    `;
    
    loadDashboardData();
}

// Load dashboard data in real-time
function loadDashboardData() {
    // Load users
    db.ref('users').on('value', (snapshot) => {
        const users = [];
        const activeUsers = [];
        let totalEarnings = 0;
        let totalTasks = 0;
        let totalReferrals = 0;
        let referralBonusTotal = 0;
        
        // Wipe old user activity
        window.dashboardActivities = window.dashboardActivities.filter(a => a.type !== 'user');

        snapshot.forEach((userSnapshot) => {
            const user = userSnapshot.val();
            if (!user) return;
            users.push(user);
            
            // Generate Activity Feed Log if user joined recently
            if (user.joined_date) {
                // Approximate timestamp if joined_date is ISO. E.g., "2026-04-10T..."
                const ts = new Date(user.joined_date).getTime();
                if (!isNaN(ts)) {
                    window.dashboardActivities.push({
                        type: 'user',
                        timestamp: ts,
                        text: `👤 New user joined: User ${userSnapshot.key}`
                    });
                }
            }

            // Check for verification/activation status
            if (user.deposit_status === 'approved' || user.activated) {
                activeUsers.push(user);
            }
            
            const earnings = user.earnings || {};
            const userTotal = earnings.total_earned || user.balance || 0;
            totalEarnings += userTotal;
            totalTasks += (earnings.tasks_completed || 0);
            totalReferrals += (user.referrals?.referred_count || 0);
            
            if (user.referrals?.bonus_awarded) {
                referralBonusTotal += (user.referrals.bonus_amount || 100);
            }
        });
        
        document.getElementById('total-users').textContent = users.length;
        document.getElementById('active-users').textContent = activeUsers.length;
        document.getElementById('total-earnings').textContent = `₹${totalEarnings.toFixed(2)}`;
        document.getElementById('total-distributed').textContent = `₹${(totalEarnings * 0.8).toFixed(2)}`;
        document.getElementById('total-tasks').textContent = totalTasks;
        document.getElementById('avg-tasks').textContent = (users.length > 0 ? (totalTasks / users.length).toFixed(1) : 0);
        document.getElementById('total-referrals').textContent = totalReferrals;
        document.getElementById('referral-bonus').textContent = `₹${referralBonusTotal}`;

        window.refreshFeed();
    });
    
    // Load deposits
    db.ref('deposits').on('value', (snapshot) => {
        let approved = 0;
        let pending = 0;
        
        window.dashboardActivities = window.dashboardActivities.filter(a => a.type !== 'deposit');

        snapshot.forEach((userSnapshot) => {
            const deposits = userSnapshot.val();
            if (deposits) {
                Object.values(deposits).forEach(deposit => {
                    if (deposit.status === 'approved') approved++;
                    if (deposit.status === 'pending') pending++;
                    
                    if (deposit.timestamp) {
                        const ts = typeof deposit.timestamp === 'string' ? new Date(deposit.timestamp).getTime() : deposit.timestamp;
                        if (!isNaN(ts)) {
                            window.dashboardActivities.push({
                                type: 'deposit',
                                timestamp: ts,
                                text: `🏦 Deposit ${deposit.status.toUpperCase()} - ₹${deposit.amount}`
                            });
                        }
                    }
                });
            }
        });
        
        document.getElementById('deposits-approved').textContent = approved;
        document.getElementById('deposits-pending').textContent = pending;
        window.refreshFeed();
    });
    
    // Load withdrawals
    db.ref('withdrawal_requests').on('value', (snapshot) => {
        let approved = 0;
        let totalAmount = 0;
        
        window.dashboardActivities = window.dashboardActivities.filter(a => a.type !== 'withdrawal');

        snapshot.forEach((withdrawalSnapshot) => {
            const withdrawal = withdrawalSnapshot.val();
            if (withdrawal.status === 'approved' || withdrawal.status === 'processed') {
                approved++;
                totalAmount += withdrawal.amount;
            }
            
            if (withdrawal.timestamp) {
                const ts = typeof withdrawal.timestamp === 'string' ? new Date(withdrawal.timestamp).getTime() : withdrawal.timestamp * 1000;
                if (!isNaN(ts)) {
                    window.dashboardActivities.push({
                        type: 'withdrawal',
                        timestamp: ts,
                        text: `💸 Withdrawal ${withdrawal.status.toUpperCase()} - ₹${withdrawal.amount}`
                    });
                }
            }
        });
        
        document.getElementById('withdrawals-approved').textContent = approved;
        document.getElementById('withdrawal-amount').textContent = `₹${totalAmount.toFixed(2)}`;
        window.refreshFeed();
    });
    
    // Load recent activity
    updateActivityFeed();
}

// Global activities array populated by live listeners
window.dashboardActivities = [];

// Update recent activity feed
function updateActivityFeed() {
    const feedEl = document.getElementById('activity-feed');
    if (!feedEl) return;

    if (window.dashboardActivities.length === 0) {
        feedEl.innerHTML = '<div class="activity-item"><span class="action">No recent activity detected.</span></div>';
        return;
    }

    // Sort descending (newest first) and take top 10
    const sorted = window.dashboardActivities.sort((a, b) => b.timestamp - a.timestamp).slice(0, 10);
    
    feedEl.innerHTML = sorted.map(activity => `
        <div class="activity-item">
            <span class="timestamp">${new Date(activity.timestamp).toLocaleTimeString('en-IN', {hour: '2-digit', minute:'2-digit'})}</span>
            <span class="action">${activity.text}</span>
        </div>
    `).join('');
}

// Debounce helper to prevent feed flashing
let feedTimeout;
window.refreshFeed = function() {
    clearTimeout(feedTimeout);
    feedTimeout = setTimeout(updateActivityFeed, 500);
};

export { loadDashboardData };
