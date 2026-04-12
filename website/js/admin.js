/**
 * Surface Hub Admin Console v3.0
 * Unified, self-contained admin engine
 * Real-time Firebase listeners on every tab
 */

// ══════════════════════════════════════════
// FIREBASE INIT
// ══════════════════════════════════════════
const firebaseConfig = {
    projectId: "chatting-app-ae637",
    appId: "1:715270614018:web:1e41bf63bbae736efd0b1b",
    databaseURL: "https://chatting-app-ae637-default-rtdb.firebaseio.com",
    storageBucket: "chatting-app-ae637.appspot.com",
    apiKey: "AIzaSyBolwpdLxlR5KYcc-Ga6KRuIS5WvWdES7I",
    authDomain: "chatting-app-ae637.firebaseapp.com",
    messagingSenderId: "715270614018"
};

if (!firebase.apps || !firebase.apps.length) firebase.initializeApp(firebaseConfig);
const db = window.db = firebase.database();
const auth = window.auth = firebase.auth();
window.firebase = firebase;

// ══════════════════════════════════════════
// STATE
// ══════════════════════════════════════════
let _allUsers = {}, _allDeposits = {}, _allWithdrawals = {}, _allReferrals = {};
let _activeListeners = []; // track all db listeners so we can detach if needed

// ══════════════════════════════════════════
// ADMIN APP
// ══════════════════════════════════════════
const AdminApp = {
    user: null,
    activeTab: 'dashboard',

    // ── INIT ──────────────────────────────
    init() {
        try {
            auth.onAuthStateChanged(user => {
                if (user) {
                    this.user = user;
                    const loginOverlay = document.getElementById('login-overlay');
                    if (loginOverlay) loginOverlay.style.display = 'none';
                    const emailTag = document.getElementById('admin-email-tag');
                    if (emailTag) emailTag.textContent = user.email;
                    this.startAllListeners();
                    toast('✅ Welcome back!', 'success');
                } else {
                    this.user = null;
                    const loginOverlay = document.getElementById('login-overlay');
                    if (loginOverlay) loginOverlay.style.display = 'flex';
                }
            });
        } catch (e) {
            console.error('Init Error:', e);
            toast('❌ Critical Error: ' + e.message, 'error');
        }
    },

    // ── AUTH ──────────────────────────────
    async login() {
        const email = document.getElementById('adminEmail').value.trim();
        const pass  = document.getElementById('adminPassword').value;
        const errEl = document.getElementById('loginError');
        errEl.style.display = 'none';
        if (!email || !pass) { errEl.textContent = '❌ Email and password required'; errEl.style.display = 'block'; return; }
        try {
            await auth.signInWithEmailAndPassword(email, pass);
        } catch (e) {
            errEl.textContent = '❌ ' + (e.code === 'auth/wrong-password' ? 'Invalid credentials' : e.code === 'auth/user-not-found' ? 'User not found' : e.message);
            errEl.style.display = 'block';
        }
    },

    logout() { auth.signOut(); },

    // ── TAB NAVIGATION ────────────────────
    setTab(tabId, el) {
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.nav-item, .mob-btn').forEach(n => n.classList.remove('active'));
        const tab = document.getElementById('tab-' + tabId);
        if (tab) { tab.classList.add('active'); this.activeTab = tabId; }
        if (el && el.classList) el.classList.add('active');
        // sync sidebar + mob nav
        document.querySelectorAll(`[data-tab="${tabId}"]`).forEach(n => n.classList.add('active'));
        // Lazy load analytics
        if (tabId === 'analytics') this.renderAnalytics();
    },

    // ── MODAL ─────────────────────────────
    openModal(id) { document.getElementById(id).classList.add('open'); },
    closeModal(id) { document.getElementById(id).classList.remove('open'); },
    openWatchModal() { this._wpEditId = null; this.openModal('watch-modal'); },
    openContentModal() { this._cpEditId = null; this.openModal('content-modal'); },

    // ── REALTIME LISTENERS ─────────────────
    startAllListeners() {
        this.listenUsers();
        this.listenDeposits();
        this.listenWithdrawals();
        this.listenReferrals();
        this.listenTasks();
        this.listenContent();
        this.listenWatchPosts();
        this.listenBroadcasts();
        this.loadSettings();
    },

    // ─────────────────────────────────────────
    // USERS
    // ─────────────────────────────────────────
    listenUsers() {
        db.ref('users').on('value', snap => {
            _allUsers = {};
            let totalEarnings = 0, totalTasks = 0, activeCount = 0;
            snap.forEach(child => {
                const u = child.val();
                if (!u) return;
                _allUsers[child.key] = { ...u, _id: child.key };
                if (u.deposit_status) activeCount++;
                totalEarnings += (u.balance || 0);
                totalTasks += (u.earnings?.tasks_completed || 0);
            });
            const count = Object.keys(_allUsers).length;
            // KPIs
            setText('kpi-users', count);
            setText('kpi-active-users', `Active: ${activeCount}`);
            setText('kpi-earnings', '₹' + totalEarnings.toFixed(0));
            setText('kpi-distributed', `Dist: ₹${(totalEarnings * 0.85).toFixed(0)}`);
            setText('kpi-tasks', totalTasks);
            setText('kpi-avg-tasks', `Avg: ${count > 0 ? (totalTasks/count).toFixed(1) : 0}`);
            setText('user-count-label', `${count} users total`);
            // badge
            const newUsers = Object.values(_allUsers).filter(u => !u.deposit_status).length;
            setBadge('badge-users', newUsers);
            this.renderUsersTable();
            this.pushActivity(`👥 Users updated: ${count} total, ${activeCount} active`, '#3b82f6');
        });
    },

    renderUsersTable() {
        const search = (document.getElementById('user-search')?.value || '').toLowerCase();
        const statusF = document.getElementById('user-status-filter')?.value || '';
        const sortF   = document.getElementById('user-sort')?.value || 'newest';
        let users = Object.values(_allUsers);
        // filter
        if (search) users = users.filter(u =>
            String(u._id).includes(search) ||
            (u.username || '').toLowerCase().includes(search) ||
            (u.first_name || '').toLowerCase().includes(search)
        );
        if (statusF === 'active')   users = users.filter(u => u.deposit_status && !u.banned);
        if (statusF === 'inactive') users = users.filter(u => !u.deposit_status);
        if (statusF === 'banned')   users = users.filter(u => u.banned);
        // sort
        if (sortF === 'balance') users.sort((a,b) => (b.balance||0) - (a.balance||0));
        else if (sortF === 'tasks') users.sort((a,b) => (b.earnings?.tasks_completed||0) - (a.earnings?.tasks_completed||0));
        else users.sort((a,b) => (b.joined_at||0) - (a.joined_at||0));

        const tbody = document.getElementById('users-tbody');
        if (!tbody) return;
        if (users.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><i class="fas fa-users-slash"></i><p>No users found</p></div></td></tr>`;
            return;
        }
        tbody.innerHTML = users.map(u => {
            const name = u.username || u.first_name || 'Unknown';
            const initial = name.charAt(0).toUpperCase();
            const status = u.banned ? `<span class="chip chip-banned">Banned</span>` :
                           u.deposit_status ? `<span class="chip chip-active">Active</span>` :
                           `<span class="chip chip-pending">Inactive</span>`;
            return `<tr>
              <td><div style="display:flex;align-items:center;gap:10px">
                <div class="user-avatar">${initial}</div>
                <div><div style="font-weight:600">${escHtml(name)}</div><div style="font-size:.7rem;color:var(--muted)">${u._id}</div></div>
              </div></td>
              <td><strong>₹${(u.balance||0).toFixed(2)}</strong></td>
              <td>${u.earnings?.tasks_completed||0}</td>
              <td>${status}</td>
              <td style="font-size:.73rem;color:var(--muted)">${u.last_active ? new Date(u.last_active).toLocaleDateString('en-IN') : 'N/A'}</td>
              <td style="white-space:nowrap">
                <button class="btn btn-info btn-sm" onclick="AdminApp.viewUser('${u._id}')"><i class="fas fa-eye"></i></button>
                <button class="btn ${u.banned ? 'btn-success' : 'btn-warn'} btn-sm" onclick="AdminApp.toggleBan('${u._id}',${!!u.banned})">
                  ${u.banned ? '✓ Unban' : '🚫 Ban'}
                </button>
                <button class="btn btn-ghost btn-sm" onclick="AdminApp.adjustBalance('${u._id}')">₹ Adjust</button>
              </td>
            </tr>`;
        }).join('');
    },

    viewUser(uid) {
        const u = _allUsers[uid];
        if (!u) return;
        const name = u.username || u.first_name || uid;
        document.getElementById('modal-user-title').textContent = `👤 ${name}`;
        document.getElementById('modal-user-body').innerHTML = `
          <div class="kpi-grid" style="grid-template-columns:1fr 1fr 1fr;margin-bottom:1rem">
            <div class="kpi"><div class="kpi-value">₹${(u.balance||0).toFixed(2)}</div><div class="kpi-label">Balance</div></div>
            <div class="kpi"><div class="kpi-value">${u.earnings?.tasks_completed||0}</div><div class="kpi-label">Tasks</div></div>
            <div class="kpi"><div class="kpi-value">${u.referrals?.referred_count||0}</div><div class="kpi-label">Referrals</div></div>
          </div>
          <table style="width:100%;font-size:.8rem;border-collapse:collapse">
            ${[
              ['User ID', uid],
              ['Username', u.username || 'N/A'],
              ['First Name', u.first_name || 'N/A'],
              ['Deposit Status', u.deposit_status ? '✅ Activated' : '❌ Not Activated'],
              ['Banned', u.banned ? '🚫 Yes' : '✓ No'],
              ['Joined', u.joined_at ? new Date(u.joined_at*1000).toLocaleString('en-IN') : 'N/A'],
              ['Referral Code', u.referrals?.referral_code || 'N/A'],
              ['Referred By', u.referrals?.referred_by || 'None'],
              ['Total Earned', '₹' + (u.earnings?.total_earned || u.balance || 0)],
              ['Withdrawn', '₹' + (u.earnings?.total_withdrawn || 0)],
            ].map(([k,v]) => `<tr style="border-bottom:1px solid var(--border)"><td style="padding:.5rem;color:var(--muted)">${k}</td><td style="padding:.5rem;font-weight:600">${v}</td></tr>`).join('')}
          </table>
          <div style="display:flex;gap:.7rem;margin-top:1rem;flex-wrap:wrap">
            <button class="btn btn-warn btn-sm" onclick="AdminApp.adjustBalance('${uid}')"><i class="fas fa-coins"></i> Adjust Balance</button>
            <button class="btn ${u.banned?'btn-success':'btn-danger'} btn-sm" onclick="AdminApp.toggleBan('${uid}',${!!u.banned});AdminApp.closeModal('user-modal')">
              ${u.banned ? '✓ Unban User' : '🚫 Ban User'}
            </button>
          </div>`;
        this.openModal('user-modal');
    },

    async toggleBan(uid, isBanned) {
        const action = isBanned ? 'Unban' : 'Ban';
        if (!confirm(`${action} user ${uid}?`)) return;
        try {
            await db.ref(`users/${uid}/banned`).set(!isBanned);
            toast(`${isBanned ? '✅ User unbanned' : '🚫 User banned'}`, isBanned ? 'success' : 'error');
            this.pushActivity(`${isBanned ? '✅ Unban' : '🚫 Ban'} action on user ${uid}`, isBanned ? '#10b981' : '#ef4444');
        } catch (e) { toast('❌ Error: ' + e.message, 'error'); }
    },

    async adjustBalance(uid) {
        const u = _allUsers[uid];
        if (!u) return;
        const current = u.balance || 0;
        const input = prompt(`Adjust balance for user ${u.username || uid}\nCurrent: ₹${current}\n\nEnter new balance:`);
        if (input === null) return;
        const newBal = parseFloat(input);
        if (isNaN(newBal) || newBal < 0) { toast('❌ Invalid amount', 'error'); return; }
        try {
            await db.ref(`users/${uid}/balance`).set(newBal);
            await db.ref('admin_logs/balance_adjustments').push({
                user_id: uid, old_balance: current, new_balance: newBal,
                adjusted_by: this.user?.email, timestamp: Date.now()
            });
            toast(`✅ Balance updated to ₹${newBal}`, 'success');
            this.pushActivity(`💰 Balance adjusted for ${uid}: ₹${current} → ₹${newBal}`, '#6366f1');
        } catch (e) { toast('❌ ' + e.message, 'error'); }
    },

    // ─────────────────────────────────────────
    // DEPOSITS
    // ─────────────────────────────────────────
    listenDeposits() {
        db.ref('deposits').on('value', snap => {
            _allDeposits = {};
            snap.forEach(child => { _allDeposits[child.key] = { ...child.val(), _id: child.key }; });
            const pending = Object.values(_allDeposits).filter(d => (d.status || 'pending') === 'pending');
            const approved = Object.values(_allDeposits).filter(d => d.status === 'approved');
            setText('kpi-dep-pending', pending.length);
            setText('kpi-dep-approved', `Approved: ${approved.length}`);
            setBadge('badge-deposits', pending.length);
            setText('dep-pending-count', `${pending.length} Pending`);
            setText('dep-approved-count', `${approved.length} Approved`);
            this.renderDeposits();
        });
    },

    filterDeposits() { this.renderDeposits(); },
    renderDeposits() {
        const filter = document.getElementById('dep-filter')?.value || '';
        let deposits = Object.values(_allDeposits);
        if (filter) deposits = deposits.filter(d => (d.status || 'pending') === filter);
        deposits.sort((a,b) => (b.created_at||0) - (a.created_at||0));
        const el = document.getElementById('deposits-list');
        if (!el) return;
        if (deposits.length === 0) { el.innerHTML = `<div class="empty-state"><i class="fas fa-credit-card"></i><p>No deposits ${filter || ''}</p></div>`; return; }
        el.innerHTML = deposits.map(d => {
            const status = d.status || 'pending';
            const u = _allUsers[d.user_id] || {};
            const name = d.username || u.username || d.user_id;
            const time = d.created_at ? new Date(d.created_at * 1000).toLocaleString('en-IN') : 'N/A';
            return `<div class="glass-card" style="margin-bottom:1rem;display:flex;gap:1.2rem;flex-wrap:wrap;align-items:flex-start">
              ${d.screenshot_id ? `<img class="screenshot-thumb" src="https://api.telegram.org/file/bot..." alt="Screenshot" title="Screenshot">` : '<div style="width:60px;height:60px;border-radius:8px;background:var(--card);display:flex;align-items:center;justify-content:center;color:var(--muted)"><i class="fas fa-image"></i></div>'}
              <div style="flex:1;min-width:200px">
                <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.4rem">
                  <strong>${escHtml(String(name))}</strong>
                  <span class="chip chip-${status}">${status === 'pending' ? '⏳ Pending' : status === 'approved' ? '✅ Approved' : '❌ Rejected'}</span>
                </div>
                <div style="font-size:.78rem;color:var(--muted)">ID: ${d.user_id} | ₹${d.amount || 50} | ${time}</div>
                ${d.admin_note ? `<div style="font-size:.72rem;color:var(--muted);margin-top:.3rem">Note: ${d.admin_note}</div>` : ''}
              </div>
              ${status === 'pending' ? `<div style="display:flex;gap:.5rem">
                <button class="btn btn-success btn-sm" onclick="AdminApp.approveDeposit('${d.user_id}')"><i class="fas fa-check"></i> Approve</button>
                <button class="btn btn-danger btn-sm" onclick="AdminApp.rejectDeposit('${d.user_id}')"><i class="fas fa-times"></i> Reject</button>
              </div>` : ''}
            </div>`;
        }).join('');
    },

    async approveDeposit(userId) {
        if (!confirm(`Approve deposit for user ${userId}?`)) return;
        const user = _allUsers[userId] || {};
        try {
            const cfg = await this._getConfig();
            const bonus = cfg.welcome_bonus || 20;
            const depositAmt = cfg.deposit_amount || 50;
            const newBal = (user.balance || 0) + depositAmt + bonus;
            const updates = {};
            updates[`deposits/${userId}/status`] = 'approved';
            updates[`deposits/${userId}/approved_at`] = Date.now() / 1000 | 0;
            updates[`deposits/${userId}/admin_note`] = `Approved by ${this.user?.email}`;
            updates[`users/${userId}/deposit_status`] = true;
            updates[`users/${userId}/balance`] = newBal;
            updates[`admin_logs/deposit_approvals/${Date.now()}`] = { user_id: userId, amount: depositAmt, bonus, final_balance: newBal, by: this.user?.email, ts: Date.now() };
            await db.ref().update(updates);
            toast('✅ Deposit approved! User notified via bot.', 'success');
            this.pushActivity(`✅ Deposit approved for ${user.username || userId} — Balance: ₹${newBal}`, '#10b981');
        } catch(e) { toast('❌ ' + e.message, 'error'); }
    },

    async rejectDeposit(userId) {
        const reason = prompt('Rejection reason (optional):') ?? '';
        try {
            await db.ref(`deposits/${userId}`).update({
                status: 'rejected',
                rejected_at: Date.now() / 1000 | 0,
                admin_note: reason || `Rejected by ${this.user?.email}`
            });
            toast('❌ Deposit rejected. User will be notified.', 'error');
            this.pushActivity(`❌ Deposit rejected for user ${userId}`, '#ef4444');
        } catch(e) { toast('❌ ' + e.message, 'error'); }
    },

    // ─────────────────────────────────────────
    // WITHDRAWALS
    // ─────────────────────────────────────────
    listenWithdrawals() {
        db.ref('withdrawal_requests').on('value', snap => {
            _allWithdrawals = {};
            snap.forEach(child => { _allWithdrawals[child.key] = { ...child.val(), _id: child.key }; });
            const pending = Object.values(_allWithdrawals).filter(w => w.status === 'pending');
            const totalAmt = pending.reduce((s,w) => s + (w.amount||0), 0);
            setText('kpi-with-pending', pending.length);
            setText('kpi-with-amount', `₹${totalAmt.toFixed(0)}`);
            setBadge('badge-withdrawals', pending.length);
            setText('with-pending-count', `${pending.length} Pending`);
            setText('with-total-amount', `₹${totalAmt.toFixed(0)} Due`);
            this.renderWithdrawals();
        });
    },

    filterWithdrawals() { this.renderWithdrawals(); },
    renderWithdrawals() {
        const filter = document.getElementById('with-filter')?.value || '';
        let withdrawals = Object.values(_allWithdrawals);
        if (filter) withdrawals = withdrawals.filter(w => w.status === filter);
        withdrawals.sort((a,b) => (b.created_at||0) - (a.created_at||0));
        const el = document.getElementById('withdrawals-list');
        if (!el) return;
        if (withdrawals.length === 0) { el.innerHTML = `<div class="empty-state"><i class="fas fa-money-bill-wave"></i><p>No withdrawals ${filter || ''}</p></div>`; return; }
        el.innerHTML = withdrawals.map(w => {
            const status = w.status || 'pending';
            const user = _allUsers[w.user_id] || {};
            const name = user.username || w.user_id;
            const time = w.created_at ? new Date(w.created_at).toLocaleString('en-IN') : 'N/A';
            return `<div class="glass-card" style="margin-bottom:1rem">
              <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem">
                <div>
                  <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.3rem">
                    <strong>${escHtml(String(name))}</strong>
                    <span class="chip chip-${status === 'pending' ? 'pending' : status === 'approved' ? 'approved' : 'rejected'}">${status}</span>
                  </div>
                  <div style="font-size:.8rem"><strong>₹${w.amount}</strong> → ${escHtml(w.upi || 'N/A')}</div>
                  <div style="font-size:.72rem;color:var(--muted)">ID: ${w.user_id} | ${time}</div>
                </div>
                ${status === 'pending' ? `<div style="display:flex;gap:.5rem">
                  <button class="btn btn-success btn-sm" onclick="AdminApp.approveWithdrawal('${w._id}','${w.user_id}')"><i class="fas fa-check"></i> Approve</button>
                  <button class="btn btn-danger btn-sm" onclick="AdminApp.rejectWithdrawal('${w._id}','${w.user_id}',${w.amount})"><i class="fas fa-times"></i> Reject</button>
                </div>` : ''}
              </div>
            </div>`;
        }).join('');
    },

    async approveWithdrawal(requestId, userId) {
        if (!confirm(`Approve withdrawal for user ${userId}?`)) return;
        try {
            await db.ref(`withdrawal_requests/${requestId}`).update({
                status: 'approved', approved_at: Date.now(), approved_by: this.user?.email
            });
            toast('✅ Withdrawal approved! Bot will notify user.', 'success');
            this.pushActivity(`✅ Withdrawal approved: ${requestId}`, '#10b981');
        } catch(e) { toast('❌ ' + e.message, 'error'); }
    },

    async rejectWithdrawal(requestId, userId, amount) {
        const reason = prompt('Rejection reason:') ?? '';
        if (reason === null) return;
        try {
            // refund balance
            const user = _allUsers[userId] || {};
            const newBal = (user.balance || 0) + (amount || 0);
            const updates = {};
            updates[`withdrawal_requests/${requestId}/status`] = 'rejected';
            updates[`withdrawal_requests/${requestId}/rejected_at`] = Date.now();
            updates[`withdrawal_requests/${requestId}/note`] = reason;
            updates[`users/${userId}/balance`] = newBal;
            await db.ref().update(updates);
            toast(`❌ Withdrawal rejected. ₹${amount} refunded to user.`, 'error');
            this.pushActivity(`❌ Withdrawal rejected: ${requestId}, ₹${amount} refunded`, '#ef4444');
        } catch(e) { toast('❌ ' + e.message, 'error'); }
    },

    // ─────────────────────────────────────────
    // REFERRALS
    // ─────────────────────────────────────────
    listenReferrals() {
        db.ref('users').on('value', snap => {
            let referrers = [], totalReferrals = 0, bonusCount = 0;
            snap.forEach(child => {
                const u = child.val();
                if (u?.referrals?.referred_count > 0) {
                    referrers.push({ id: child.key, ...u });
                    totalReferrals += u.referrals.referred_count;
                    if (u.referrals.bonus_awarded) bonusCount++;
                }
            });
            setText('kpi-referrals', totalReferrals);
            setText('kpi-ref-bonus', `Bonus: ${bonusCount}`);
            setText('ref-kpi-referrers', referrers.length);
            setText('ref-kpi-total', totalReferrals);
            setText('ref-kpi-bonus', bonusCount);
            referrers.sort((a,b) => (b.referrals?.referred_count||0) - (a.referrals?.referred_count||0));
            const tbody = document.getElementById('referrals-tbody');
            if (!tbody) return;
            tbody.innerHTML = referrers.map((u,i) => {
                const name = u.username || u.first_name || u.id;
                return `<tr>
                  <td style="font-weight:900;${i<3?`color:${['#f59e0b','#9ca3af','#b45309'][i]}`:''}"> ${['🥇','🥈','🥉'][i] || (i+1)}</td>
                  <td>${escHtml(String(name))}</td>
                  <td><code style="font-size:.75rem;background:rgba(255,255,255,0.06);padding:2px 8px;border-radius:6px">${u.referrals?.referral_code || 'N/A'}</code></td>
                  <td><strong>${u.referrals?.referred_count || 0}</strong></td>
                  <td>${u.referrals?.bonus_awarded ? '<span class="chip chip-approved">Awarded</span>' : '<span class="chip chip-pending">Pending</span>'}</td>
                  <td><button class="btn btn-success btn-sm" onclick="AdminApp.awardReferralBonus('${u.id}')"><i class="fas fa-gift"></i> Award Bonus</button></td>
                </tr>`;
            }).join('') || `<tr><td colspan="6"><div class="empty-state"><i class="fas fa-share-nodes"></i><p>No referrers yet</p></div></td></tr>`;
        });
    },

    async awardReferralBonus(userId) {
        const u = _allUsers[userId] || {};
        const cfg = await this._getConfig();
        const bonus = cfg.referrer_bonus || 100;
        if (!confirm(`Award ₹${bonus} referral bonus to ${u.username || userId}?`)) return;
        try {
            const newBal = (u.balance || 0) + bonus;
            await db.ref().update({
                [`users/${userId}/balance`]: newBal,
                [`users/${userId}/referrals/bonus_awarded`]: true
            });
            toast(`✅ ₹${bonus} bonus awarded!`, 'success');
        } catch(e) { toast('❌ ' + e.message, 'error'); }
    },

    // ─────────────────────────────────────────
    // WATCH POSTS
    // ─────────────────────────────────────────
    listenWatchPosts() {
        db.ref('watch_posts').on('value', snap => {
            const posts = [];
            snap.forEach(child => posts.push({ ...child.val(), _id: child.key }));
            posts.sort((a,b) => (b.featured?1:0) - (a.featured?1:0) || (b.timestamp||0) - (a.timestamp||0));
            const grid = document.getElementById('watch-posts-grid');
            if (!grid) return;
            if (posts.length === 0) {
                grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><i class="fas fa-play-circle"></i><p>No watch posts yet.</p></div>`;
                return;
            }
            grid.innerHTML = posts.map(p => `
              <div class="content-card">
                ${p.image ? `<img src="${escHtml(p.image)}" alt="thumb" onerror="this.style.display='none'">` : `<div style="height:160px;background:var(--card);display:flex;align-items:center;justify-content:center;font-size:3rem">📺</div>`}
                <div class="content-card-body">
                  ${p.featured ? `<span class="chip chip-approved" style="margin-bottom:.4rem">⭐ Featured</span>` : ''}
                  <div style="font-size:.65rem;color:var(--p);font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:.2rem">${p.category || 'General'}</div>
                  <h4>${escHtml(p.title || 'Untitled')}</h4>
                  <p style="margin-top:.3rem">${escHtml((p.description || '').substring(0,80))}${(p.description||'').length>80?'...':''}</p>
                  ${p.reward ? `<div style="font-size:.75rem;color:#10b981;margin-top:.4rem;font-weight:700">💰 ₹${p.reward} reward</div>` : ''}
                </div>
                <div class="content-card-actions">
                  ${p.video_url ? `<a href="${escHtml(p.video_url)}" target="_blank" class="btn btn-info btn-sm"><i class="fas fa-play"></i> Watch</a>` : ''}
                  <button class="btn btn-danger btn-sm" onclick="AdminApp.deleteWatchPost('${p._id}')"><i class="fas fa-trash"></i></button>
                </div>
              </div>`).join('');
        });
    },

    previewWatchImg(url) {
        const prev = document.getElementById('wp-img-preview');
        if (!prev) return;
        if (url) { prev.src = url; prev.style.display = 'block'; }
        else { prev.style.display = 'none'; }
    },

    async handleVideoUpload(input) {
        const file = input.files[0];
        if (!file) return;
        const statusEl = document.getElementById('video-upload-status');
        statusEl.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Uploading ${file.name}...`;
        try {
            const storageRef = firebase.storage().ref(`videos/${Date.now()}_${file.name}`);
            const task = storageRef.put(file);
            task.on('state_changed', 
                snap => {
                    const pct = (snap.bytesTransferred / snap.totalBytes * 100).toFixed(0);
                    statusEl.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Uploading: ${pct}%`;
                },
                err => { throw err; },
                async () => {
                    const url = await storageRef.getDownloadURL();
                    document.getElementById('wp-video').value = url;
                    statusEl.innerHTML = `<span style="color:var(--success)">✅ Upload Complete!</span>`;
                    toast('📺 Video uploaded and linked!', 'success');
                }
            );
        } catch (e) {
            statusEl.innerHTML = `<span style="color:var(--danger)">❌ Upload Failed</span>`;
            toast('❌ Upload error: ' + e.message, 'error');
        }
    },

    async saveWatchPost() {
        const title = document.getElementById('wp-title')?.value.trim();
        const desc  = document.getElementById('wp-desc')?.value.trim();
        const image = document.getElementById('wp-image')?.value.trim();
        const video = document.getElementById('wp-video')?.value.trim();
        const cat   = document.getElementById('wp-category')?.value;
        const reward = parseInt(document.getElementById('wp-reward')?.value) || 0;
        const featured = document.getElementById('wp-featured')?.checked;
        if (!title || !video) { toast('❌ Title and Video URL are required', 'error'); return; }
        const post = { title, description: desc, image, video_url: video, category: cat, reward, featured, timestamp: Date.now(), enabled: true };
        try {
            await db.ref('watch_posts').push(post);
            toast('✅ Watch post published!', 'success');
            this.closeModal('watch-modal');
            // clear
            ['wp-title','wp-desc','wp-image','wp-video'].forEach(id => { const el = document.getElementById(id); if(el) el.value=''; });
            document.getElementById('wp-img-preview').style.display = 'none';
            document.getElementById('video-upload-status').innerHTML = '';
            this.pushActivity(`📺 New watch post: "${title}"`, '#6366f1');
        } catch(e) { toast('❌ ' + e.message, 'error'); }
    },

    async deleteWatchPost(postId) {
        if (!confirm('Delete this watch post?')) return;
        await db.ref(`watch_posts/${postId}`).remove();
        toast('🗑️ Watch post deleted', 'error');
    },

    // ─────────────────────────────────────────
    // HUB CONTENT
    // ─────────────────────────────────────────
    listenContent() {
        db.ref('content').on('value', snap => {
            const posts = [];
            snap.forEach(child => posts.push({ ...child.val(), _id: child.key }));
            posts.sort((a,b) => (b.timestamp||0) - (a.timestamp||0));
            const grid = document.getElementById('content-grid');
            if (!grid) return;
            if (posts.length === 0) { grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><i class="fas fa-newspaper"></i><p>No hub posts yet.</p></div>`; return; }
            grid.innerHTML = posts.map(p => `
              <div class="content-card">
                ${p.image ? `<img src="${escHtml(p.image)}" alt="thumb" onerror="this.style.display='none'">` : `<div style="height:160px;background:var(--card);display:flex;align-items:center;justify-content:center;font-size:3rem">📝</div>`}
                <div class="content-card-body">
                  <div style="font-size:.65rem;color:var(--p);font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:.2rem">${p.category||'Blogs'}</div>
                  <h4>${escHtml(p.title||'Untitled')}</h4>
                  <p>${escHtml((p.summary||'').substring(0,80))}${(p.summary||'').length>80?'...':''}</p>
                </div>
                <div class="content-card-actions">
                  <button class="btn btn-danger btn-sm" onclick="AdminApp.deleteContent('${p._id}')"><i class="fas fa-trash"></i> Delete</button>
                </div>
              </div>`).join('');
        });
    },

    async saveContent() {
        const title   = document.getElementById('cp-title')?.value.trim();
        const summary = document.getElementById('cp-summary')?.value.trim();
        const image   = document.getElementById('cp-image')?.value.trim();
        const cat     = document.getElementById('cp-category')?.value;
        const reward  = parseInt(document.getElementById('cp-reward')?.value) || 10;
        if (!title || !summary) { toast('❌ Title and summary required', 'error'); return; }
        try {
            await db.ref('content').push({ title, summary, image, category: cat, reward, timestamp: Date.now(), enabled: true });
            toast('✅ Post published!', 'success');
            this.closeModal('content-modal');
            this.pushActivity(`📝 New hub post: "${title}"`, '#3b82f6');
        } catch(e) { toast('❌ ' + e.message, 'error'); }
    },

    async deleteContent(postId) {
        if (!confirm('Delete this post?')) return;
        await db.ref(`content/${postId}`).remove();
        toast('🗑️ Post deleted', 'error');
    },

    // ─────────────────────────────────────────
    // TASKS
    // ─────────────────────────────────────────
    listenTasks() {
        db.ref('tasks').on('value', snap => {
            const tasks = [];
            snap.forEach(child => tasks.push({ ...child.val(), _id: child.key }));
            tasks.sort((a,b) => (b.addedAt||0) - (a.addedAt||0));
            setText('task-total-count', tasks.length);
            const list = document.getElementById('task-list');
            if (!list) return;
            if (tasks.length === 0) { list.innerHTML = `<div class="empty-state"><i class="fas fa-tasks"></i><p>No tasks yet</p></div>`; return; }
            list.innerHTML = tasks.map(t => `
              <div style="background:rgba(255,255,255,0.03);border-radius:12px;padding:.9rem;border:1px solid var(--border);margin-bottom:.6rem;display:flex;justify-content:space-between;align-items:center;gap:.8rem">
                <div style="flex:1;min-width:0">
                  <div style="font-weight:600;font-size:.85rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escHtml(t.title||'Untitled')}</div>
                  <div style="font-size:.72rem;color:var(--muted);margin-top:2px">💰 ₹${t.reward || 0} · ${t.category || 'general'} · ${t.completions||0} done</div>
                </div>
                <div style="display:flex;gap:.4rem;flex-shrink:0">
                  <button class="btn btn-warn btn-sm" onclick="AdminApp.toggleTask('${t._id}',${!!t.enabled})">${t.enabled!==false?'⏸ Pause':'▶ Enable'}</button>
                  <button class="btn btn-danger btn-sm" onclick="AdminApp.deleteTask('${t._id}')"><i class="fas fa-trash"></i></button>
                </div>
              </div>`).join('');
        });
    },

    async saveTask() {
        const title  = document.getElementById('task-title')?.value.trim();
        const url    = document.getElementById('task-url')?.value.trim();
        const reward = parseInt(document.getElementById('task-reward-amt')?.value) || 10;
        const cat    = document.getElementById('task-category')?.value;
        if (!title || !url) { toast('❌ Title and URL required', 'error'); return; }
        try {
            await db.ref('tasks').push({ title, url, reward, category: cat, enabled: true, completions: 0, addedAt: Date.now() });
            toast('✅ Task synced to bot & website!', 'success');
            document.getElementById('task-title').value = '';
            document.getElementById('task-url').value = '';
            this.pushActivity(`🎯 New task: "${title}" (₹${reward})`, '#f59e0b');
        } catch(e) { toast('❌ ' + e.message, 'error'); }
    },

    async toggleTask(taskId, isEnabled) {
        await db.ref(`tasks/${taskId}/enabled`).set(!isEnabled);
        toast(`Task ${isEnabled ? 'paused' : 'enabled'}`, isEnabled ? 'error' : 'success');
    },

    async deleteTask(taskId) {
        if (!confirm('Delete this task?')) return;
        await db.ref(`tasks/${taskId}`).remove();
        toast('🗑️ Task deleted', 'error');
    },

    // ─────────────────────────────────────────
    // BROADCAST
    // ─────────────────────────────────────────
    listenBroadcasts() {
        db.ref('broadcast_queue').orderByChild('timestamp').limitToLast(20).on('value', snap => {
            const items = [];
            snap.forEach(child => items.push({ ...child.val(), _id: child.key }));
            items.sort((a,b) => (b.timestamp||0) - (a.timestamp||0));
            const el = document.getElementById('bc-list');
            if (!el) return;
            if (items.length === 0) { el.innerHTML = `<div class="empty-state"><i class="fas fa-inbox"></i><p>No broadcasts queued</p></div>`; return; }
            el.innerHTML = items.map(item => {
                const statusCls = item.status === 'sent' ? 'bc-sent' : item.status === 'failed' ? 'bc-failed' : 'bc-pending';
                const time = item.timestamp ? new Date(item.timestamp).toLocaleTimeString('en-IN') : '';
                return `<div class="bc-item">
                  <div style="flex:1;min-width:0">
                    <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.3rem">
                      <span class="bc-status ${statusCls}">${item.status||'pending'}</span>
                      <span style="font-size:.7rem;color:var(--muted)">${time}</span>
                    </div>
                    <div style="font-size:.82rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escHtml((item.message||'').substring(0,100))}</div>
                  </div>
                  <button class="btn btn-danger btn-sm" onclick="AdminApp.deleteBroadcast('${item._id}')"><i class="fas fa-trash"></i></button>
                </div>`;
            }).join('');
        });
    },

    async sendBroadcast() {
        const msg   = document.getElementById('bc-msg')?.value.trim();
        const img   = document.getElementById('bc-img')?.value.trim();
        const link  = document.getElementById('bc-link')?.value.trim();
        const label = document.getElementById('bc-link-label')?.value.trim() || 'Open Link';
        if (!msg) { toast('❌ Message cannot be empty', 'error'); return; }
        try {
            await db.ref('broadcast_queue').push({
                message: msg, image: img || null,
                link: link || null, link_label: label,
                status: 'pending', timestamp: Date.now(), target: 'all'
            });
            toast('📢 Broadcast queued! Bot will send to all users.', 'success');
            ['bc-msg','bc-img','bc-link','bc-link-label'].forEach(id => { const el = document.getElementById(id); if(el) el.value=''; });
            this.pushActivity(`📢 Broadcast sent: "${msg.substring(0,50)}"`, '#ec4899');
        } catch(e) { toast('❌ ' + e.message, 'error'); }
    },

    async deleteBroadcast(id) {
        await db.ref(`broadcast_queue/${id}`).remove();
        toast('🗑️ Broadcast removed', 'error');
    },

    // ─────────────────────────────────────────
    // SETTINGS
    // ─────────────────────────────────────────
    async _getConfig() {
        const snap = await db.ref('system_config').once('value');
        return snap.val() || {};
    },

    async loadSettings() {
        try {
            const cfg = await this._getConfig();
            setVal('cfg-maintenance', cfg.maintenance_mode, 'checkbox');
            setVal('cfg-earn-enabled', cfg.earn_enabled !== false, 'checkbox');
            setVal('cfg-deposits-open', cfg.deposits_open !== false, 'checkbox');
            setVal('cfg-withdrawals-open', cfg.withdrawals_open !== false, 'checkbox');
            setVal('cfg-watch-enabled', cfg.watch_enabled !== false, 'checkbox');
            setVal('cfg-deposit-amount', cfg.deposit_amount || 50);
            setVal('cfg-task-reward', cfg.task_reward || 10);
            setVal('cfg-min-withdraw', cfg.min_withdraw || 500);
            setVal('cfg-referrer-bonus', cfg.referrer_bonus || 100);
            setVal('cfg-referred-bonus', cfg.referred_bonus || 20);
            setVal('cfg-ref-threshold', cfg.referral_threshold || 25);
            setVal('cfg-upi-id', cfg.upi_id || '');
            setVal('cfg-upi-name', cfg.upi_name || 'Surface Hub');
            setVal('cfg-welcome-bonus', cfg.welcome_bonus || 20);
            setVal('cfg-website-url', cfg.website_url || 'https://chatting-app-ae637.web.app');
            setVal('cfg-maintenance-msg', cfg.maintenance_message || '');
            setVal('cfg-welcome-msg', cfg.welcome_message || '');
            setVal('cfg-admin-ids', (cfg.admin_ids || []).join(','));
            setVal('cfg-watch-shortlink', cfg.watch_shortlink || '');
        } catch(e) { console.error('Settings load error:', e); }
    },

    async saveSettings() {
        const cfg = {
            maintenance_mode:    document.getElementById('cfg-maintenance')?.checked || false,
            earn_enabled:        document.getElementById('cfg-earn-enabled')?.checked !== false,
            deposits_open:       document.getElementById('cfg-deposits-open')?.checked !== false,
            withdrawals_open:    document.getElementById('cfg-withdrawals-open')?.checked !== false,
            watch_enabled:       document.getElementById('cfg-watch-enabled')?.checked !== false,
            deposit_amount:      parseFloat(document.getElementById('cfg-deposit-amount')?.value) || 50,
            task_reward:         parseFloat(document.getElementById('cfg-task-reward')?.value) || 10,
            min_withdraw:        parseFloat(document.getElementById('cfg-min-withdraw')?.value) || 500,
            referrer_bonus:      parseFloat(document.getElementById('cfg-referrer-bonus')?.value) || 100,
            referred_bonus:      parseFloat(document.getElementById('cfg-referred-bonus')?.value) || 20,
            referral_threshold:  parseInt(document.getElementById('cfg-ref-threshold')?.value) || 25,
            upi_id:              document.getElementById('cfg-upi-id')?.value.trim() || '',
            upi_name:            document.getElementById('cfg-upi-name')?.value.trim() || 'Surface Hub',
            welcome_bonus:       parseFloat(document.getElementById('cfg-welcome-bonus')?.value) || 20,
            website_url:         document.getElementById('cfg-website-url')?.value.trim() || '',
            maintenance_message: document.getElementById('cfg-maintenance-msg')?.value.trim() || '',
            welcome_message:     document.getElementById('cfg-welcome-msg')?.value.trim() || '',
            admin_ids:           (document.getElementById('cfg-admin-ids')?.value || '').split(',').map(s => s.trim()).filter(Boolean),
            watch_shortlink:     document.getElementById('cfg-watch-shortlink')?.value.trim() || '',
            last_updated:        Date.now(),
            updated_by:          this.user?.email || 'admin'
        };
        try {
            await db.ref('system_config').set(cfg);
            setText('settings-status', '✅ Settings saved at ' + new Date().toLocaleTimeString('en-IN'));
            toast('✅ Settings saved! Bot will use new values instantly.', 'success');
            this.pushActivity('⚙️ System settings updated', '#6366f1');
        } catch(e) { toast('❌ Error saving settings: ' + e.message, 'error'); }
    },

    // ─────────────────────────────────────────
    // ANALYTICS
    // ─────────────────────────────────────────
    renderAnalytics() {
        const users = Object.values(_allUsers);
        const today = new Date().toDateString();
        const todayUsers = users.filter(u => u.joined_at && new Date(u.joined_at * 1000).toDateString() === today).length;
        const balances = users.map(u => u.balance || 0);
        const topBal = balances.length > 0 ? Math.max(...balances) : 0;
        setText('an-today', todayUsers);
        const todayEarnings = users
            .filter(u => new Date((u.joined_at||0)*1000).toDateString() === today)
            .reduce((s,u) => s + (u.balance||0), 0);
        setText('an-earnings-today', '₹' + todayEarnings.toFixed(0));
        setText('an-tasks-today', users.reduce((s,u) => s + (u.earnings?.tasks_completed||0), 0));
        setText('an-top-balance', '₹' + topBal.toFixed(0));

        // Top earners
        const sorted = [...users].sort((a,b) => (b.balance||0) - (a.balance||0)).slice(0,10);
        const maxBal = sorted[0]?.balance || 1;
        document.getElementById('top-earners-list').innerHTML = sorted.map((u,i) => {
            const name = u.username || u.first_name || u._id;
            const pct  = ((u.balance||0) / maxBal * 100).toFixed(0);
            return `<div class="top-earner">
              <div class="rank ${i<3?`rank-${i+1}`:''}">${['🥇','🥈','🥉'][i]||i+1}</div>
              <div style="flex:1;min-width:0"><div style="font-size:.83rem;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escHtml(String(name))}</div>
              <div class="chart-bar-bg" style="margin-top:4px"><div class="chart-bar-fill" style="width:${pct}%"></div></div></div>
              <div style="font-size:.85rem;font-weight:700;flex-shrink:0">₹${(u.balance||0).toFixed(0)}</div>
            </div>`;
        }).join('') || '<div class="empty-state"><i class="fas fa-trophy"></i><p>No data</p></div>';

        // Breakdown
        const totalBal = users.reduce((s,u)=>s+(u.balance||0),0);
        const totalTasks = users.reduce((s,u)=>s+(u.earnings?.tasks_completed||0),0);
        document.getElementById('earnings-breakdown').innerHTML = [
            ['Total Users', users.length, users.length, '#3b82f6'],
            ['Activated', users.filter(u=>u.deposit_status).length, users.length, '#10b981'],
            ['Total Tasks Done', totalTasks, Math.max(totalTasks,1), '#f59e0b'],
            ['Total Balance Pool', `₹${totalBal.toFixed(0)}`, null, '#6366f1'],
        ].map(([label, val, max, color]) => `
          <div class="chart-bar-wrap">
            <div class="chart-label"><span>${label}</span><strong>${val}</strong></div>
            ${max !== null ? `<div class="chart-bar-bg"><div class="chart-bar-fill" style="width:${max>0?(+String(val).replace('₹','')/max*100).toFixed(0):0}%;background:${color}"></div></div>` : ''}
          </div>`).join('');
    },

    // ─────────────────────────────────────────
    // ACTIVITY FEED
    // ─────────────────────────────────────────
    _activityItems: [],
    pushActivity(text, color = '#3b82f6') {
        this._activityItems.unshift({ text, color, time: new Date().toLocaleTimeString('en-IN') });
        if (this._activityItems.length > 20) this._activityItems.pop();
        const feed = document.getElementById('activity-feed');
        if (!feed) return;
        feed.innerHTML = this._activityItems.map(item => `
          <div class="activity-item">
            <div class="act-icon" style="background:${item.color}22;color:${item.color}"><i class="fas fa-circle-dot"></i></div>
            <div class="act-text">${escHtml(item.text)}</div>
            <div class="act-time">${item.time}</div>
          </div>`).join('');
    }
};

// ══════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════
function setText(id, val) { const el = document.getElementById(id); if(el) el.textContent = val; }
function setVal(id, val, type = 'text') {
    const el = document.getElementById(id);
    if (!el) return;
    if (type === 'checkbox') el.checked = !!val;
    else el.value = val ?? '';
}
function setBadge(id, count) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = count;
    el.style.display = count > 0 ? 'inline-flex' : 'none';
}
function escHtml(str) {
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

let _toastTimer;
function toast(msg, type = '') {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = 'show ' + type;
    clearTimeout(_toastTimer);
    _toastTimer = setTimeout(() => { el.className = ''; }, 3500);
}

// ── Expose to global for onclick handlers ──
window.AdminApp = AdminApp;
window.toast    = toast;

// ── Wire up search/filter inputs once DOM ready ──
document.addEventListener('DOMContentLoaded', () => {
    AdminApp.init();

    // live search
    document.getElementById('user-search')?.addEventListener('input', () => AdminApp.renderUsersTable());
    document.getElementById('user-status-filter')?.addEventListener('change', () => AdminApp.renderUsersTable());
    document.getElementById('user-sort')?.addEventListener('change', () => AdminApp.renderUsersTable());
    document.getElementById('ref-search')?.addEventListener('input', () => {
        const q = document.getElementById('ref-search').value.toLowerCase();
        document.querySelectorAll('#referrals-tbody tr').forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
    });
});
