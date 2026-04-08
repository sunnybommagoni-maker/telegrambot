/**
 * Admin Users Tab (Phase 9)
 * Real-time user earnings and referral statistics
 */

// Store users data for filtering
let allUsers = {};

// Initialize Users Tab
export async function initUsersTab() {
    const container = document.getElementById('users-tab-content');
    if (!container) return;
    
    container.innerHTML = `
        <div class="admin-section">
            <h3>👥 USER MANAGEMENT</h3>
            <div class="filter-bar">
                <input type="text" id="user-search" placeholder="Search by ID, name, or email..." class="search-input">
                <select id="filter-status" class="filter-select">
                    <option value="">All Users</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                    <option value="no-deposit">No Deposit Yet</option>
                </select>
            </div>
            <div id="users-list" class="users-list"></div>
        </div>
    `;
    
    setupUserFilters();
    loadUsersRealtime();
}

// Setup search and filter functionality
function setupUserFilters() {
    const searchInput = document.getElementById('user-search');
    const statusFilter = document.getElementById('filter-status');
    
    searchInput.addEventListener('input', () => filterAndDisplayUsers());
    statusFilter.addEventListener('change', () => filterAndDisplayUsers());
}

// Load and listen to users in real-time
function loadUsersRealtime() {
    const usersRef = db.ref('users');
    
    usersRef.on('value', (snapshot) => {
        allUsers = {};
        snapshot.forEach((childSnapshot) => {
            const userId = childSnapshot.key;
            const userData = childSnapshot.val();
            allUsers[userId] = {
                id: userId,
                username: userData.profile?.username || 'Unknown',
                email: userData.profile?.email || 'N/A',
                balance: userData.balance || 0,
                deposit_status: userData.deposit_status || false,
                join_date: userData.profile?.join_date || 'Unknown',
                earnings: userData.earnings || {},
                referrals: userData.referrals || {},
                last_active: userData.last_active || 'Never'
            };
        });
        
        filterAndDisplayUsers();
    });
}

// Filter and display users
function filterAndDisplayUsers() {
    const searchTerm = document.getElementById('user-search').value.toLowerCase();
    const statusFilter = document.getElementById('filter-status').value;
    const usersList = document.getElementById('users-list');
    
    let filteredUsers = Object.values(allUsers).filter(user => {
        // Search filter
        const matchesSearch = 
            user.id.includes(searchTerm) || 
            user.username.toLowerCase().includes(searchTerm) || 
            user.email.toLowerCase().includes(searchTerm);
        
        if (!matchesSearch) return false;
        
        // Status filter
        if (statusFilter === 'active') return user.deposit_status && user.balance > 0;
        if (statusFilter === 'inactive') return !user.deposit_status || user.balance === 0;
        if (statusFilter === 'no-deposit') return !user.deposit_status;
        
        return true;
    });
    
    if (filteredUsers.length === 0) {
        usersList.innerHTML = '<div class="empty-state">No users found</div>';
        return;
    }
    
    usersList.innerHTML = filteredUsers.map(user => `
        <div class="user-card">
            <div class="user-header">
                <div class="user-info">
                    <h4>${user.username}</h4>
                    <p class="user-id">ID: ${user.id}</p>
                    <p class="user-email">${user.email}</p>
                </div>
                <div class="user-badge ${user.deposit_status ? 'verified' : 'unverified'}">
                    ${user.deposit_status ? '✅ Verified' : '⚠️ Not Verified'}
                </div>
            </div>
            <div class="user-stats">
                <div class="stat">
                    <span class="label">Balance</span>
                    <span class="value">₹${user.balance.toFixed(2)}</span>
                </div>
                <div class="stat">
                    <span class="label">Earned</span>
                    <span class="value">₹${((user.earnings?.tasks_earnings || 0) + (user.earnings?.referral_bonus || 0)).toFixed(2)}</span>
                </div>
                <div class="stat">
                    <span class="label">Tasks</span>
                    <span class="value">${user.earnings?.tasks_completed || 0}</span>
                </div>
                <div class="stat">
                    <span class="label">Referred</span>
                    <span class="value">${user.referrals?.referred_count || 0}</span>
                </div>
            </div>
            <div class="user-dates">
                <p>Joined: ${formatDate(user.join_date)}</p>
                <p>Last Active: ${formatDate(user.last_active)}</p>
            </div>
        </div>
    `).join('');
}

function formatDate(dateStr) {
    if (!dateStr || dateStr === 'Unknown' || dateStr === 'Never') return dateStr;
    try {
        return new Date(dateStr).toLocaleDateString('en-IN');
    } catch {
        return 'Unknown';
    }
}

// Export functions
export { loadUsersRealtime, filterAndDisplayUsers };
