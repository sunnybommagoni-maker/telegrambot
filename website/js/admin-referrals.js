// Referrals Core
const db = window.db;
const auth = window.auth;

// Initialize Referrals Tab
let allReferrals = {};

// Initialize Referrals Tab
export async function initReferralsTab() {
    const container = document.getElementById('referrals-tab-content');
    if (!container) return;
    
    container.innerHTML = `
        <div class="admin-section">
            <h3>🤝 REFERRAL NETWORK</h3>
            <div class="filter-bar">
                <input type="text" id="referral-search" placeholder="Search by referrer ID or code..." class="search-input">
                <div class="stats-row">
                    <div class="stat-card">
                        <span class="stat-label">Active Referrers</span>
                        <span class="stat-value" id="active-referrers">0</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-label">Total Referrals</span>
                        <span class="stat-value" id="total-referrals">0</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-label">Bonus Awarded</span>
                        <span class="stat-value" id="bonus-awarded">₹0</span>
                    </div>
                </div>
            </div>
            <div id="referrals-list" class="referrals-list"></div>
        </div>
    `;
    
    setupReferralSearch();
    loadReferralsRealtime();
}

// Seup referral search
function setupReferralSearch() {
    const searchInput = document.getElementById('referral-search');
    searchInput.addEventListener('input', () => filterAndDisplayReferrals());
}

// Load referrals in real-time
function loadReferralsRealtime() {
    const usersRef = db.ref('users');
    
    usersRef.on('value', (snapshot) => {
        allReferrals = {};
        snapshot.forEach((childSnapshot) => {
            const userId = childSnapshot.key;
            const userData = childSnapshot.val();
            
            if (userData.referrals) {
                allReferrals[userId] = {
                    user_id: userId,
                    username: userData.profile?.username || 'Unknown',
                    referral_code: userData.referrals?.referral_code || 'N/A',
                    referred_by: userData.referrals?.referred_by || null,
                    referred_count: userData.referrals?.referred_count || 0,
                    bonus_awarded: userData.referrals?.bonus_awarded || false,
                    referrals_list: userData.referrals?.referrals_list || {},
                    total_earned_from_referrals: calculateReferralEarnings(userData)
                };
            }
        });
        
        updateReferralStats();
        filterAndDisplayReferrals();
    });
}

// Calculate total earnings from referrals
function calculateReferralEarnings(userData) {
    const referralBonus = userData.earnings?.referral_bonus || 0;
    return referralBonus;
}

// Update referral statistics
function updateReferralStats() {
    const referrersWithActive = Object.values(allReferrals).filter(r => r.referred_count > 0);
    const totalReferralCount = Object.values(allReferrals).reduce((sum, r) => sum + r.referred_count, 0);
    const bonusAwarded = Object.values(allReferrals)
        .filter(r => r.bonus_awarded)
        .reduce((sum, r) => sum + 100, 0); // ₹100 per bonus
    
    document.getElementById('active-referrers').textContent = referrersWithActive.length;
    document.getElementById('total-referrals').textContent = totalReferralCount;
    document.getElementById('bonus-awarded').textContent = `₹${bonusAwarded}`;
}

// Filter and display referrals
function filterAndDisplayReferrals() {
    const searchTerm = document.getElementById('referral-search').value.toLowerCase();
    const referralsList = document.getElementById('referrals-list');
    
    let filteredReferrals = Object.values(allReferrals)
        .filter(r => r.referred_count > 0); // Only show referrers with active referrals
    
    if (searchTerm) {
        filteredReferrals = filteredReferrals.filter(r =>
            r.user_id.toString().includes(searchTerm) ||
            r.referral_code.toLowerCase().includes(searchTerm) ||
            r.username.toLowerCase().includes(searchTerm)
        );
    }
    
    // Sort by referral count (highest first)
    filteredReferrals.sort((a, b) => b.referred_count - a.referred_count);
    
    if (filteredReferrals.length === 0) {
        referralsList.innerHTML = '<div class="empty-state">No referrers found</div>';
        return;
    }
    
    referralsList.innerHTML = filteredReferrals.map((referrer, index) => {
        const referredUsers = Object.entries(referrer.referrals_list)
            .slice(0, 5)
            .map(([refId, refData]) => `
                <div class="referral-item">
                    <span class="ref-user">${refId}</span>
                    <span class="ref-status ${refData.tasks_completed >= 25 ? 'qualified' : 'pending'}">
                        ${refData.tasks_completed || 0}/25 tasks
                    </span>
                </div>
            `)
            .join('');
        
        return `
            <div class="referral-card ${referrer.bonus_awarded ? 'bonus-awarded' : ''}">
                <div class="referral-header">
                    <div class="referrer-rank">#${index + 1}</div>
                    <div class="referrer-info">
                        <h4>${referrer.username}</h4>
                        <p class="code-badge">${referrer.referral_code}</p>
                    </div>
                    <div class="referral-status">
                        ${referrer.bonus_awarded ? '💰 Bonus Awarded' : '⏳ Active'}
                    </div>
                </div>
                <div class="referral-stats">
                    <div class="stat">
                        <span class="label">Referred Users</span>
                        <span class="value">${referrer.referred_count}</span>
                    </div>
                    <div class="stat">
                        <span class="label">Earnings</span>
                        <span class="value">₹${referrer.total_earned_from_referrals.toFixed(2)}</span>
                    </div>
                </div>
                <div class="referred-users">
                    <p>Recent Referrals:</p>
                    ${referredUsers || '<p class="none">None</p>'}
                </div>
            </div>
        `;
    }).join('');
}

export { loadReferralsRealtime, filterAndDisplayReferrals };
