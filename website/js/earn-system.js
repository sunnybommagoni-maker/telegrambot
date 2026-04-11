/**
 * Surface Hub - Earn System v2.0
 * Mandatory 2-Step Verification with Timers
 */

const EarnSystem = {
    // Configuration
    HOME_TIMER: 10,       // Seconds for Step 1
    TASK_TIMER: 20,       // Seconds for Step 2
    RANDOM_PAGES: [
        'blogs.html',
        'help.html',
        'info.html',
        'videos.html',
        'hub.html'
    ],

    init() {
        this.urlParams = new URLSearchParams(window.location.search);
        this.token = this.urlParams.get('token') || localStorage.getItem('earn_token');
        this.step = parseInt(this.urlParams.get('step')) || parseInt(localStorage.getItem('earn_step')) || 0;

        if (!this.token || !this.step) {
            console.log("ℹ️ No active earn session detected.");
            return;
        }

        // Persist for page refreshes
        localStorage.setItem('earn_token', this.token);
        localStorage.setItem('earn_step', this.step);

        console.log(`🤑 Earn Session Active: Step ${this.step}`);
        this.injectStyles();
        this.startFlow();
    },

    injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
            #earn-timer-bar {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                background: rgba(0, 118, 255, 0.95);
                backdrop-filter: blur(10px);
                color: white;
                padding: 12px;
                text-align: center;
                z-index: 99999;
                font-weight: 800;
                font-family: 'Inter', sans-serif;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 5px;
                border-bottom: 2px solid rgba(255,255,255,0.2);
            }
            #earn-progress-container {
                width: 80%;
                height: 4px;
                background: rgba(255,255,255,0.2);
                border-radius: 2px;
                overflow: hidden;
            }
            #earn-progress-fill {
                height: 100%;
                background: #fff;
                width: 0%;
                transition: width 1s linear;
            }
            #earn-action-container {
                position: fixed;
                bottom: 20px;
                left: 0;
                width: 100%;
                padding: 0 20px;
                z-index: 99998;
                display: none;
                animation: slideUp 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            }
            #earn-action-btn {
                background: #10b981;
                color: white;
                width: 100%;
                max-width: 500px;
                margin: 0 auto;
                padding: 18px;
                border-radius: 12px;
                text-align: center;
                font-weight: 900;
                font-size: 1.1rem;
                cursor: pointer;
                box-shadow: 0 10px 30px rgba(16, 185, 129, 0.4);
                border: none;
                text-transform: uppercase;
                letter-spacing: 1px;
                display: block;
            }
            @keyframes slideUp {
                from { transform: translateY(100px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    },

    startFlow() {
        // Create UI elements
        const timerBar = document.createElement('div');
        timerBar.id = 'earn-timer-bar';
        timerBar.innerHTML = `
            <div>STEP ${this.step}/2: VERIFYING SESSION...</div>
            <div id="earn-timer-display">Wait <span id="seconds-left">--</span> seconds</div>
            <div id="earn-progress-container"><div id="earn-progress-fill"></div></div>
        `;
        document.body.prepend(timerBar);

        const actionContainer = document.createElement('div');
        actionContainer.id = 'earn-action-container';
        actionContainer.innerHTML = `
            <button id="earn-action-btn">
                ${this.step === 1 ? 'Continue to Next Step →' : '💰 Claim Reward (₹10)'}
            </button>
        `;
        document.body.appendChild(actionContainer);

        const duration = this.step === 1 ? this.HOME_TIMER : this.TASK_TIMER;
        this.runTimer(duration);
    },

    runTimer(seconds) {
        let timeLeft = seconds;
        const display = document.getElementById('seconds-left');
        const progress = document.getElementById('earn-progress-fill');
        
        const update = () => {
            display.innerText = timeLeft;
            const percent = ((seconds - timeLeft) / seconds) * 100;
            progress.style.width = `${percent}%`;

            if (timeLeft <= 0) {
                this.onTimerComplete();
            } else {
                timeLeft--;
                setTimeout(update, 1000);
            }
        };

        update();
    },

    onTimerComplete() {
        document.getElementById('earn-timer-display').innerHTML = "✅ Verification Ready!";
        document.getElementById('earn-progress-fill').style.width = "100%";
        document.getElementById('earn-action-container').style.display = 'block';

        const btn = document.getElementById('earn-action-btn');
        btn.onclick = () => this.handleAction();
    },

    handleAction() {
        if (this.step === 1) {
            // Pick random page
            const randomPage = this.RANDOM_PAGES[Math.floor(Math.random() * this.RANDOM_PAGES.length)];
            const nextUrl = `${randomPage}?token=${this.token}&step=2`;
            
            // Show loading state
            document.getElementById('earn-action-btn').innerText = "Redirecting...";
            setTimeout(() => {
                window.location.href = nextUrl;
            }, 500);
        } else {
            // Claim Reward
            this.claimReward();
        }
    },

    claimReward() {
        const btn = document.getElementById('earn-action-btn');
        btn.disabled = true;
        btn.innerText = "Processing Hub Reward...";

        // Use the existing HubPayout logic if available, or implement directly
        setTimeout(() => {
            alert("✅ Verification Complete! Redirecting to SurfaceWBot to claim your ₹10 reward...");
            
            // Clear persistence
            localStorage.removeItem('earn_token');
            localStorage.removeItem('earn_step');
            
            window.location.href = `https://t.me/SurfaceWBot?start=reward_${this.token}`;
        }, 1500);
    }
};

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', () => EarnSystem.init());
