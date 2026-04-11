/**
 * Surface Hub Admin Console v2.8.0
 * Real-time Command & Control with Video Support & Social Sharing
 * Firebase Connected - All Features Live
 */

// Import Phase 9 Admin Modules (Dynamic)
let adminDashboard, adminUsers, adminWithdrawals, adminDeposits, adminReferrals, adminSettings;

async function loadAdminModules() {
    try {
        adminDashboard = await import('./admin-dashboard.js');
        adminUsers = await import('./admin-users.js');
        adminWithdrawals = await import('./admin-withdrawals.js');
        adminDeposits = await import('./admin-deposits.js');
        adminReferrals = await import('./admin-referrals.js');
        adminSettings = await import('./admin-settings.js');
        console.log('✅ Phase 9 Admin Modules Loaded');
    } catch (error) {
        console.warn('⚠️ Phase 9 modules not fully loaded:', error);
    }
}

// Load modules on startup
loadAdminModules();

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

const db = window.db = firebase.database();
const storage = window.storage = firebase.storage();
const auth = window.auth = firebase.auth();
window.firebase = firebase;

/**
 * ADMIN APPLICATION - Main Controller
 */
const AdminApp = {
    user: null,
    currentFile: null,
    statsInterval: null,

    // ==================== INITIALIZATION ====================
    init() {
        console.log("🚀 Admin Console v2.8.0 - Initializing...");
        this.listenToAuth();
    },

    startListeners() {
        if (this.statsInterval) clearInterval(this.statsInterval);
        
        console.log("📡 Starting Real-time listeners...");
        this.loadStats();
        this.listenToInventory();
        this.monitorBroadcasts();
        console.log("✅ All systems online - Real-time listeners active");
    },

    // ==================== AUTHENTICATION ====================
    listenToAuth() {
        auth.onAuthStateChanged((user) => {
            if (user) {
                this.user = user;
                document.getElementById('login-overlay').style.display = 'none';
                console.log("✅ Admin Authenticated:", user.email);
                this.startListeners();
            } else {
                this.user = null;
                document.getElementById('login-overlay').style.display = 'flex';
            }
        });
    },

    async login() {
        const email = document.getElementById('adminEmail').value;
        const pass = document.getElementById('adminPassword').value;
        const errEl = document.getElementById('loginError');

        if (!email || !pass) {
            errEl.innerText = "❌ Email and password required";
            errEl.style.display = 'block';
            return;
        }

        try {
            const result = await auth.signInWithEmailAndPassword(email, pass);
            errEl.style.display = 'none';
            console.log("🔐 Login Successful:", result.user.email);
        } catch (error) {
            console.error("Login Error:", error.code);
            let msg = "Unknown error";
            if (error.code === 'auth/user-not-found') msg = "User not found";
            if (error.code === 'auth/wrong-password') msg = "Invalid credentials";
            if (error.code === 'auth/invalid-email') msg = "Invalid email format";

            errEl.innerText = "❌ " + msg;
            errEl.style.display = 'block';
        }
    },

    logout() {
        auth.signOut().then(() => {
            window.location.reload();
        });
    },

    // ==================== TAB NAVIGATION ====================
    setTab(tabId, el) {
        // Remove active from all tabs and nav items
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

        // Add active to selected
        const tab = document.getElementById(`tab-${tabId}`);
        if (tab) {
            tab.classList.add('active');
            if (el && el.classList) el.classList.add('active');
            
            // Initialize Phase 9 tabs when clicked
            switch(tabId) {
                case 'dashboard':
                    if (adminDashboard?.initDashboardTab) {
                        adminDashboard.initDashboardTab();
                    }
                    break;
                case 'analytics':
                    if (adminUsers?.initUsersTab) {
                        adminUsers.initUsersTab();
                    }
                    break;
                case 'withdrawals':
                    if (adminWithdrawals?.initWithdrawalsTab) {
                        adminWithdrawals.initWithdrawalsTab();
                    }
                    break;
                case 'deposits':
                    if (adminDeposits?.initDepositsTab) {
                        adminDeposits.initDepositsTab();
                    }
                    break;
                case 'referrals':
                    if (adminReferrals?.initReferralsTab) {
                        adminReferrals.initReferralsTab();
                    }
                    break;
                case 'settings':
                    if (adminSettings?.initSettingsTab) {
                        adminSettings.initSettingsTab();
                    }
                    break;
            }
        }
    },

    // ==================== DASHBOARD STATS (REAL-TIME) ====================
    loadStats() {
        // User Count & Total Balance
        db.ref('users').on('value', snap => {
            const usersEl = document.getElementById('stat-users');
            if (usersEl) {
                usersEl.innerText = snap.numChildren().toLocaleString();
            }

            let totalBalance = 0;
            snap.forEach(user => {
                totalBalance += (user.val().balance || 0);
            });

            const rewardsEl = document.getElementById('stat-rewards');
            if (rewardsEl) {
                rewardsEl.innerText = `₹${totalBalance.toLocaleString()}`;
            }
        });

        // Additional stats can be added here
    },

    // ==================== POST MANAGEMENT WITH VIDEO & SHARING ====================
    handleFile(input) {
        if (input.files && input.files[0]) {
            const file = input.files[0];

            // Validate file type
            if (!file.type.match('image.*')) {
                alert("❌ Please select an image file");
                return;
            }

            this.currentFile = file;
            const reader = new FileReader();
            reader.onload = e => {
                const preview = document.getElementById('post-preview');
                preview.src = e.target.result;
                preview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    },

    async savePost() {
        // Get form values
        const title = document.getElementById('post-title').value?.trim();
        const category = document.getElementById('post-cat').value;
        const summary = document.getElementById('post-summary').value?.trim();
        const videoUrl = document.getElementById('post-video').value?.trim();
        const imageUrl = document.getElementById('post-url').value?.trim();

        // Validation
        if (!title || !summary) {
            alert("❌ Fill required fields: Title and Summary");
            return;
        }

        const btn = document.getElementById('btn-publish-post');
        let finalImage = imageUrl;

        try {
            // Upload file if provided
            if (this.currentFile) {
                btn.innerText = "📤 UPLOADING IMAGE...";
                btn.disabled = true;

                const timestamp = Date.now();
                const ref = storage.ref(`posts/${timestamp}_${this.currentFile.name}`);
                const uploadTask = ref.put(this.currentFile);

                await new Promise((resolve, reject) => {
                    uploadTask.on('state_changed',
                        (snapshot) => {
                            const progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
                            btn.innerText = `📤 UPLOADING ${Math.round(progress)}%`;
                        },
                        reject,
                        resolve
                    );
                });

                finalImage = await ref.getDownloadURL();
            }

            if (!finalImage) {
                alert("❌ Provide image URL or upload file");
                btn.disabled = false;
                btn.innerText = "PUBLISH TO PORTAL";
                return;
            }

            btn.innerText = "🔄 PUBLISHING...";

            // Collect share preferences
            const shareOptions = {
                facebook: document.getElementById('share-facebook').checked,
                twitter: document.getElementById('share-twitter').checked,
                whatsapp: document.getElementById('share-whatsapp').checked,
                telegram: document.getElementById('share-telegram').checked
            };

            // Create post object with video support
            const postData = {
                title,
                category,
                summary,
                image: finalImage,
                videoUrl: videoUrl || null,
                thumbnail: finalImage,
                timestamp: Date.now(),
                author: "Admin",
                type: category,
                content: summary,
                description: summary,
                reward: 10,
                enabled: true,
                shareOptions
            };

            // Save to Firebase
            const newPostRef = db.ref('content').push();
            await newPostRef.set(postData);

            btn.innerText = "✅ PUBLISHED!";
            setTimeout(() => {
                btn.innerText = "PUBLISH TO PORTAL";
                btn.disabled = false;
            }, 1500);

            console.log("✅ Post published with video and share options:", newPostRef.key);
            this.resetPostForm();
            alert("🚀 POST PUBLISHED TO PORTAL HUB (Video & Share Options Active)");

        } catch (error) {
            console.error("Error saving post:", error);
            alert("❌ Error: " + error.message);
            btn.innerText = "PUBLISH TO PORTAL";
            btn.disabled = false;
        }
    },

    resetPostForm() {
        document.getElementById('post-title').value = '';
        document.getElementById('post-cat').value = 'Blogs';
        document.getElementById('post-summary').value = '';
        document.getElementById('post-url').value = '';
        document.getElementById('post-video').value = '';
        document.getElementById('post-preview').style.display = 'none';
        this.currentFile = null;

        // Reset share checkboxes to all enabled
        document.getElementById('share-facebook').checked = true;
        document.getElementById('share-twitter').checked = true;
        document.getElementById('share-whatsapp').checked = true;
        document.getElementById('share-telegram').checked = true;
    },

    // ==================== TASK MANAGEMENT ====================
    saveTask() {
        const title = document.getElementById('task-title').value?.trim();
        const url = document.getElementById('task-url').value?.trim();
        const reward = parseInt(document.getElementById('task-reward').value) || 5;

        if (!title || !url) {
            alert("❌ Fill task title and URL");
            return;
        }

        const taskData = {
            title,
            url,
            reward,
            type: "external_link",
            addedAt: Date.now(),
            enabled: true,
            completions: 0
        };

        db.ref('tasks').push(taskData).then(ref => {
            console.log("✅ Task created:", ref.key);
            alert(`✅ TASK SYNCED TO BOT & WEB (ID: ${ref.key})`);
            document.getElementById('task-title').value = '';
            document.getElementById('task-url').value = '';
            document.getElementById('task-reward').value = '10';
        }).catch(err => {
            alert("❌ Error: " + err.message);
        });
    },

    deleteItem(path, id) {
        if (confirm("⚠️ Permanently delete this record?")) {
            db.ref(`${path}/${id}`).remove().then(() => {
                console.log(`✅ Deleted: ${path}/${id}`);
            }).catch(err => {
                alert("❌ Delete failed: " + err.message);
            });
        }
    },

    // ==================== BROADCAST ENGINE ====================
    sendBroadcast() {
        const message = document.getElementById('bc-msg').value?.trim();
        const image = document.getElementById('bc-img').value?.trim();

        if (!message) {
            alert("❌ Message cannot be empty");
            return;
        }

        const broadcastData = {
            message,
            image: image || null,
            status: "pending",
            timestamp: Date.now(),
            type: "system_notification",
            targetUsers: "all"
        };

        db.ref('broadcast_queue').push(broadcastData).then(ref => {
            console.log("✅ Broadcast queued:", ref.key);
            alert("📢 BROADCAST QUEUED - Bot will process soon");
            document.getElementById('bc-msg').value = '';
            document.getElementById('bc-img').value = '';
        }).catch(err => {
            alert("❌ Error: " + err.message);
        });
    },

    monitorBroadcasts() {
        db.ref('broadcast_queue').on('value', snap => {
            const container = document.getElementById('bc-list');
            if (!container) return;

            container.innerHTML = '';
            let hasItems = false;

            snap.forEach(child => {
                hasItems = true;
                const item = child.val();
                const statusColor = {
                    'pending': '#eab308',
                    'processing': '#3b82f6',
                    'sent': '#10b981',
                    'failed': '#ef4444'
                }[item.status] || '#888';

                const timeAgo = this.getTimeAgo(item.timestamp);

                container.innerHTML += `
                    <div class="inventory-item">
                        <div style="flex-grow: 1;">
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 5px;">
                                <span style="padding: 4px 10px; border-radius: 50px; background: ${statusColor}; font-size: 0.65rem; font-weight: 700; text-transform: uppercase;">
                                    ${item.status || 'pending'}
                                </span>
                                <span style="font-size: 0.75rem; opacity: 0.6;">${timeAgo}</span>
                            </div>
                            <p style="font-size: 0.9rem; margin: 5px 0 0 0; line-height: 1.4;">
                                ${item.message.substring(0, 80)}${item.message.length > 80 ? '...' : ''}
                            </p>
                        </div>
                        <button class="nav-item" style="padding: 5px 10px; margin: 0; color: #ef4444;" 
                            onclick="AdminApp.deleteItem('broadcast_queue', '${child.key}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
            });

            if (!hasItems) {
                container.innerHTML = `
                    <div class="glass-card" style="background: rgba(0,0,0,0.05); text-align: center;">
                        <p style="opacity: 0.5;">📭 No active broadcasts</p>
                    </div>
                `;
            }
        });
    },

    // ==================== INVENTORY LISTENERS (REAL-TIME) ====================
    listenToInventory() {
        // CONTENT INVENTORY (Posts with Video & Share Indicators)
        db.ref('content').on('value', snap => {
            const postList = document.getElementById('post-list');
            if (!postList) return;

            postList.innerHTML = '';
            let postCount = 0;

            snap.forEach(child => {
                postCount++;
                const item = child.val();
                const hasVideo = item.videoUrl ? '🎥' : '📄';
                const shareCount = [
                    item.shareOptions?.facebook,
                    item.shareOptions?.twitter,
                    item.shareOptions?.whatsapp,
                    item.shareOptions?.telegram
                ].filter(Boolean).length;

                postList.innerHTML += `
                    <div class="inventory-item" style="flex-direction: column; align-items: flex-start;">
                        <div style="width: 100%; display: flex; justify-content: space-between; align-items: center;">
                            <div style="flex-grow: 1;">
                                <strong style="color: var(--p);">[${item.category}] ${hasVideo}</strong>
                                <div style="margin-top: 4px; font-size: 0.9rem;">${item.title}</div>
                                <div style="font-size: 0.75rem; opacity: 0.6; margin-top: 4px;">
                                    📤 Share Options: ${shareCount} enabled
                                </div>
                            </div>
                            <button class="nav-item" style="padding: 8px 12px; margin: 0; color: #ef4444;" 
                                onclick="AdminApp.deleteItem('content', '${child.key}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                `;
            });

            if (postCount === 0) {
                postList.innerHTML = '<p style="opacity: 0.5; text-align: center;">No posts yet</p>';
            }
        });

        // TASK INVENTORY
        db.ref('tasks').on('value', snap => {
            const taskList = document.getElementById('task-list');
            if (!taskList) return;

            taskList.innerHTML = '';
            let taskCount = 0;

            snap.forEach(child => {
                taskCount++;
                const item = child.val();

                taskList.innerHTML += `
                    <div class="inventory-item">
                        <div style="flex-grow: 1;">
                            <strong>${item.title}</strong><br>
                            <small style="opacity: 0.5;">💰 Reward: ₹${item.reward} | 📋 Completions: ${item.completions || 0}</small>
                        </div>
                        <button class="nav-item" style="padding: 5px 10px; margin: 0; color: #ef4444;" 
                            onclick="AdminApp.deleteItem('tasks', '${child.key}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
            });

            if (taskCount === 0) {
                taskList.innerHTML = '<p style="opacity: 0.5; text-align: center;">No tasks created</p>';
            }
        });
    },

    // ==================== UTILITY FUNCTIONS ====================
    getTimeAgo(timestamp) {
        const now = Date.now();
        const diff = now - timestamp;

        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return "Just now";
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return `${days}d ago`;
    }
};

// ==================== AUTO-INIT ====================
window.AdminApp = AdminApp; // Make global for onclick handlers

document.addEventListener('DOMContentLoaded', () => {
    AdminApp.init();
});
