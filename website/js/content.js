/**
 * Surface Hub Content Engine- PREMIUM
 * Handles user persistence, rewards, and AdSense synchronization.
 */

// Initialize Firebase
const firebaseConfig = {
    databaseURL: "https://chatting-app-ae637-default-rtdb.firebaseio.com"
};
if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
}
const db = firebase.database();

// Persistence Logic - Robust Synchronization
const params = new URLSearchParams(window.location.search);
let user_id = params.get('user_id');
let reward = parseFloat(params.get('reward') || '0');
let ad_id = params.get('ad_id') || params.get('task_id') || params.get('offer_id') || 'gen_ad';

// Restore from localStorage if URL is missing data
if (!user_id) {
    user_id = localStorage.getItem('surface_user_id');
    console.log("Surface Hub: Restored User ID from persistence layer.");
}
if (!reward || reward === 0) {
    reward = parseFloat(localStorage.getItem('surface_reward') || '5');
    console.log("Surface Hub: Restored Reward Value from persistence layer.");
}

// Save back to localStorage for next navigation
if (user_id) {
    localStorage.setItem('surface_user_id', user_id);
    localStorage.setItem('surface_reward', reward);
    console.log(`Surface Hub: Session Validated for ${user_id} (Reward: ₹${reward})`);
} else {
    console.warn("Surface Hub: No User ID found. Rewards disabled.");
}

/**
 * claimReward()
 * The final step to inject balance into Firebase safely.
 */
function claimReward() {
    if (!user_id) {
        alert("❌ Error: Session Expired. Please restart from SurfaceWBot.");
        return;
    }

    const btn = document.getElementById('claim-btn');
    if (btn) {
        btn.disabled = true;
        btn.innerText = "Processing Payout...";
    }

    // Transaction for atomic balance updates
    db.ref(`users/${user_id}/balance`).transaction((currentValue) => {
        return (currentValue || 0) + reward;
    }).then(() => {
        if (ad_id !== 'gen_ad') {
            db.ref(`user_tasks/${user_id}/${ad_id}`).set(true);
        }
        
        console.log("Surface Hub: Payout Successful!");
        alert(`✅ ₹${reward} added to your wallet! Check your bot balance.`);
        
        // Redirect back to Telegram
        setTimeout(() => {
            window.location.href = "https://t.me/SurfaceWBot";
        }, 1500);
    }).catch((err) => {
        console.error("Surface Hub: Payout Failed", err);
        alert("❌ Network Error. Please try again or contact support.");
        if (btn) {
            btn.disabled = false;
            btn.innerText = "Retry Claim Reward";
        }
    });
}

