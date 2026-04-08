/**
 * User Dashboard - Phase 10
 * Real-time earnings, tasks, and referral tracking
 */

const firebaseConfig = {
    projectId: "chatting-app-ae637",
    appId: "1:715270614018:web:1e41bf63bbae736efd0b1b",
    databaseURL: "https://chatting-app-ae637-default-rtdb.firebaseio.com",
    storageBucket: "chatting-app-ae637.appspot.com",
    apiKey: "AIzaSyBolwpdLxlR5KYcc-Ga6KRuIS5WvWdES7I",
    authDomain: "chatting-app-ae637.firebaseapp.com",
    messagingSenderId: "715270614018"
};

if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
}

const db = firebase.database();
const auth = firebase.auth();

/**
 * User Dashboard Controller
 */
const UserDashboard = {
    userId: null,
    userData: null,
    statsListeners: [],

    /**
     * Initialize dashboard
     */
    init() {
        console.log('🎯 User Dashboard Initializing...');
        
        // Check if user is logged in via Telegram ID
        const userId = localStorage.getItem('telegram_user_id');
        if (!userId) {
            window.location.href = '/index.html';
            return;
        }

        this.userId = userId;
        this.loadUserData();
    },

    /**
     * Load user data from Firebase
     */
    loadUserData() {
        const userRef = db.ref(`users/${this.userId}`);
        
        userRef.on('value', (snapshot) => {
            this.userData = snapshot.val() || {};
            this.renderDashboard();
        });

        this.statsListeners.push(userRef);
    },

    /**
     * Render complete dashboard
     */
    renderDashboard() {
        this.renderMetrics();
        this.renderTaskProgress();
        this.renderEarningsBreakdown();
        this.renderReferrals();
        this.renderWithdrawalStatus();
    },

    /**
     * Render main metric cards
     */
    renderMetrics() {
        const balance = this.userData.balance || 0;
        const deposited = this.userData.deposit_status ? '✅ Yes' : '❌ No';
        const totalEarned = (this.userData.earnings?.tasks_earnings || 0) + 
                           (this.userData.earnings?.referral_bonus || 0);
        const referralCount = this.userData.referrals?.referred_count || 0;

        const html = `
            <div class="metric-card">
                <div class="metric-label">💰 Current Balance</div>
                <div class="metric-value">₹${balance.toFixed(2)}</div>
                <div class="metric-sub">Available for withdrawal</div>
            </div>

            <div class="metric-card">
                <div class="metric-label">💎 Total Earned</div>
                <div class="metric-value">₹${totalEarned.toFixed(2)}</div>
                <div class="metric-sub">All-time earnings</div>
            </div>

            <div class="metric-card">
                <div class="metric-label">✅ Account Status</div>
                <div class="metric-value">${this.userData.deposit_status ? '✓' : '✗'}</div>
                <div class="metric-sub">${deposited}</div>
            </div>

            <div class="metric-card">
                <div class="metric-label">🤝 Referrals</div>
                <div class="metric-value">${referralCount}</div>
                <div class="metric-sub">Friends invited</div>
            </div>
        `;

        document.getElementById('metrics-grid').innerHTML = html;
    },

    /**
     * Render task progress
     */
    renderTaskProgress() {
        const tasksCompleted = this.userData.earnings?.tasks_completed || 0;
        const taskThreshold = 25; // Referral bonus triggers at 25 tasks
        const progress = Math.min(tasksCompleted, taskThreshold);
        const progressPercent = (progress / taskThreshold) * 100;
        const progressColor = tasksCompleted >= taskThreshold ? '#10b981' : '#0076ff';

        const bonusStatus = tasksCompleted >= taskThreshold ? 
            '✅ Bonus Unlocked!' : 
            `${taskThreshold - tasksCompleted} tasks to unlock referral bonus`;

        const html = `
            <div class="metric-card" style="margin-bottom: 1.5rem;">
                <div class="metric-label">📈 Task Completion Progress</div>
                <div class="metric-value">${tasksCompleted}/25</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${progressPercent}%; background: ${progressColor};"></div>
                </div>
                <div class="metric-sub" style="margin-top: 10px; ${tasksCompleted >= taskThreshold ? 'color: #10b981;' : ''}">${bonusStatus}</div>
            </div>
            <div style="background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 1rem; margin-top: 1rem;">
                <h4>📊 Earnings Per Task</h4>
                <p>Earn ₹10 per completed task</p>
                <p style="font-size: 0.9rem; color: var(--text-muted); margin-top: 10px;">💡 Tip: Complete 25 tasks to unlock referral bonuses</p>
            </div>
        `;

        document.getElementById('task-progress').innerHTML = html;
    },

    /**
     * Render earnings breakdown
     */
    renderEarningsBreakdown() {
        const taskEarnings = this.userData.earnings?.tasks_earnings || 0;
        const referralBonus = this.userData.earnings?.referral_bonus || 0;
        const totalEarned = taskEarnings + referralBonus;

        const html = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 1rem;">
                    <div style="font-size: 0.9rem; color: #10b981; font-weight: 600; margin-bottom: 5px;">📝 Task Earnings</div>
                    <div style="font-size: 2rem; font-weight: 900;">₹${taskEarnings.toFixed(2)}</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 5px;">${Math.floor(taskEarnings / 10)} tasks completed</div>
                </div>

                <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 1rem;">
                    <div style="font-size: 0.9rem; color: #f59e0b; font-weight: 600; margin-bottom: 5px;">🤝 Referral Bonus</div>
                    <div style="font-size: 2rem; font-weight: 900;">₹${referralBonus.toFixed(2)}</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 5px;">Friends who reached 25 tasks</div>
                </div>

                <div style="background: rgba(0, 118, 255, 0.1); border: 1px solid rgba(0, 118, 255, 0.3); border-radius: 12px; padding: 1rem;">
                    <div style="font-size: 0.9rem; color: #0076ff; font-weight: 600; margin-bottom: 5px;">💵 Total Earned</div>
                    <div style="font-size: 2rem; font-weight: 900;">₹${totalEarned.toFixed(2)}</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 5px;">All-time earnings</div>
                </div>
            </div>
        `;

        document.getElementById('earnings-breakdown').innerHTML = html;
    },

    /**
     * Render referral network
     */
    renderReferrals() {
        const referralCode = this.userData.referrals?.referral_code || 'N/A';
        const referredUsers = this.userData.referrals?.referrals_list || {};
        const referralCount = this.userData.referrals?.referred_count || 0;
        const bonusAwarded = this.userData.referrals?.bonus_awarded || false;

        let referralItems = '';
        Object.entries(referredUsers).slice(0, 6).forEach(([userId, data]) => {
            const taskProgress = data.tasks_completed || 0;
            const isQualified = taskProgress >= 25;
            const status = isQualified ? '✅ Qualified' : `${taskProgress}/25 tasks`;

            referralItems += `
                <div class="referral-item">
                    <div class="referral-user">${userId}</div>
                    <div class="referral-progress">${status}</div>
                    <div class="progress-bar" style="margin-top: 8px;">
                        <div class="progress-fill" style="width: ${Math.min(taskProgress, 25) * 4}%;"></div>
                    </div>
                </div>
            `;
        });

        const html = `
            <div style="margin-bottom: 1.5rem; background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 1rem;">
                <h4 style="margin-bottom: 10px;">🎁 Your Referral Code</h4>
                <div style="background: rgba(0, 118, 255, 0.1); border: 1px solid rgba(0, 118, 255, 0.3); border-radius: 10px; padding: 12px; font-family: monospace; font-size: 1.2rem; font-weight: 900; word-break: break-all;">
                    ${referralCode}
                </div>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 10px;">
                    💡 Share this code with friends: /start ${referralCode}
                </p>
                ${bonusAwarded ? '<div class="status-badge badge-active" style="margin-top: 10px;">💰 Referral Bonus Awarded</div>' : ''}
            </div>

            <h4 style="margin-bottom: 1rem;">👥 Referred Users (${referralCount})</h4>
            ${referralItems ? `<div class="referral-list">${referralItems}</div>` : 
              '<div style="text-align: center; padding: 2rem; color: var(--text-muted);">No referrals yet. Share your code to earn bonuses!</div>'}
        `;

        document.getElementById('referrals-section').innerHTML = html;
    },

    /**
     * Render withdrawal status
     */
    renderWithdrawalStatus() {
        const balance = this.userData.balance || 0;
        const minWithdraw = 500;
        const canWithdraw = balance >= minWithdraw;

        let html = `
            <div class="metric-card" style="margin-bottom: 1.5rem;">
                <div class="metric-label">💸 Withdrawal Limit</div>
                <div class="metric-value">₹${minWithdraw}</div>
                <div class="metric-sub">Minimum to withdraw</div>
            </div>

            <div style="background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 1rem;">
                <h4 style="margin-bottom: 10px;">📊 Withdrawal Status</h4>
        `;

        if (canWithdraw) {
            html += `
                <div class="status-badge badge-active">✅ Ready to Withdraw</div>
                <p style="margin-top: 10px;">Your balance is sufficient for withdrawal.</p>
                <p style="font-size: 0.9rem; color: var(--text-muted); margin-top: 10px;">Processing time: 24-48 hours</p>
            `;
        } else {
            const remaining = minWithdraw - balance;
            html += `
                <div class="status-badge badge-pending">⏳ Need More Balance</div>
                <p style="margin-top: 10px;">You need ₹${remaining.toFixed(2)} more to withdraw.</p>
                <div class="progress-bar" style="margin-top: 10px; height: 10px;">
                    <div class="progress-fill" style="width: ${(balance / minWithdraw) * 100}%;"></div>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 10px;">Keep completing tasks to reach the minimum!</p>
            `;
        }

        html += `</div>`;

        document.getElementById('withdrawal-status').innerHTML = html;
    },

    /**
     * Refresh dashboard
     */
    refresh() {
        console.log('🔄 Refreshing dashboard...');
        this.renderDashboard();
    },

    /**
     * Cleanup listeners
     */
    cleanup() {
        this.statsListeners.forEach(ref => ref.off());
        this.statsListeners = [];
    }
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    UserDashboard.init();
});

// Cleanup on unload
window.addEventListener('beforeunload', () => {
    UserDashboard.cleanup();
});
