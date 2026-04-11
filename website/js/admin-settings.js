// Settings Core
const db = window.db;
const auth = window.auth;

// Configuration Path
const CONFIG_PATH = 'system_config';

// Initialize Settings Tab
export async function initSettingsTab() {
    const container = document.getElementById('settings-tab-content');
    if (!container) return;
    
    container.innerHTML = `
        <div class="admin-section">
            <h3>⚙️ SYSTEM SETTINGS</h3>
            <div class="settings-form">
                <div class="form-group">
                    <label>Deposit Amount (₹)</label>
                    <input type="number" id="deposit-amount" placeholder="50" min="1">
                    <small>Required deposit for account activation</small>
                </div>
                
                <div class="form-group">
                    <label>Task Reward (₹)</label>
                    <input type="number" id="task-reward" placeholder="10" min="1">
                    <small>Amount awarded per completed task</small>
                </div>
                
                <div class="form-group">
                    <label>Minimum Withdrawal (₹)</label>
                    <input type="number" id="min-withdraw" placeholder="500" min="1">
                    <small>Minimum balance to withdraw</small>
                </div>
                
                <div class="form-group">
                    <label>Referral Task Threshold</label>
                    <input type="number" id="referral-threshold" placeholder="25" min="1">
                    <small>Tasks needed to trigger referral bonus</small>
                </div>
                
                <div class="form-group">
                    <label>Referrer Bonus (₹)</label>
                    <input type="number" id="referrer-bonus" placeholder="100" min="1">
                    <small>Bonus for person who referred</small>
                </div>
                
                <div class="form-group">
                    <label>Referred User Bonus (₹)</label>
                    <input type="number" id="referred-bonus" placeholder="20" min="1">
                    <small>Bonus for referred user</small>
                </div>
                
                <div class="form-group">
                    <label>Admin Email</label>
                    <input type="email" id="admin-email" placeholder="admin@hub.com">
                    <small>Email for notifications</small>
                </div>
                
                <div class="form-group">
                    <label>Admin Telegram ID</label>
                    <input type="text" id="admin-telegram-id" placeholder="5936922644">
                    <small>For bot notifications</small>
                </div>
                
                <button class="btn-save" onclick="saveSettings()">💾 Save Settings</button>
                <button class="btn-reset" onclick="loadSettings()">↻ Reload</button>
            </div>
            <div id="settings-status"></div>
        </div>
    `;
    
    internalLoadSettings();
}

// Load current settings
async function internalLoadSettings() {
    try {
        const snapshot = await db.ref(CONFIG_PATH).once('value');
        const config = snapshot.val() || {};
        
        document.getElementById('deposit-amount').value = config.deposit_amount || 50;
        document.getElementById('task-reward').value = config.task_reward || 10;
        document.getElementById('min-withdraw').value = config.min_withdraw || 500;
        document.getElementById('referral-threshold').value = config.referral_threshold || 25;
        document.getElementById('referrer-bonus').value = config.referrer_bonus || 100;
        document.getElementById('referred-bonus').value = config.referred_bonus || 20;
        document.getElementById('admin-email').value = config.admin_email || '';
        document.getElementById('admin-telegram-id').value = config.admin_telegram_id || '';
        
        showStatus('✅ Settings loaded', 'success');
    } catch (error) {
        showStatus('❌ Error loading settings: ' + error.message, 'error');
    }
}

// Save settings to Firebase
async function internalSaveSettings() {
    try {
        const config = {
            deposit_amount: parseFloat(document.getElementById('deposit-amount').value),
            task_reward: parseFloat(document.getElementById('task-reward').value),
            min_withdraw: parseFloat(document.getElementById('min-withdraw').value),
            referral_threshold: parseInt(document.getElementById('referral-threshold').value),
            referrer_bonus: parseFloat(document.getElementById('referrer-bonus').value),
            referred_bonus: parseFloat(document.getElementById('referred-bonus').value),
            admin_email: document.getElementById('admin-email').value,
            admin_telegram_id: document.getElementById('admin-telegram-id').value,
            last_updated: new Date().toISOString()
        };
        
        await db.ref(CONFIG_PATH).set(config);
        showStatus('✅ Settings saved successfully!', 'success');
    } catch (error) {
        showStatus('❌ Error saving settings: ' + error.message, 'error');
    }
}

function showStatus(message, type) {
    const statusEl = document.getElementById('settings-status');
    statusEl.textContent = message;
    statusEl.className = `status-message ${type}`;
    setTimeout(() => statusEl.textContent = '', 5000);
}

// Make functions global for onclick handlers
window.saveSettings = internalSaveSettings;
window.loadSettings = internalLoadSettings;
window.initSettingsTab = initSettingsTab;

// Optional: No need for bottom exports if they are exported at definition
// window assignments already handle onclick accessibility
