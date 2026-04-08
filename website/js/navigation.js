const firebaseConfig = {
    projectId: "chatting-app-ae637",
    appId: "1:715270614018:web:1e41bf63bbae736efd0b1b",
    databaseURL: "https://chatting-app-ae637-default-rtdb.firebaseio.com",
    storageBucket: "chatting-app-ae637.firebasestorage.app",
    apiKey: "AIzaSyBolwpdLxlR5KYcc-Ga6KRuIS5WvWdES7I",
    authDomain: "chatting-app-ae637.firebaseapp.com",
    messagingSenderId: "715270614018"
};

// Initialize Portal Network
if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
}

const ADSENSE_ID = "ca-pub-5388885815887025";

// Global Component Templates
const navigationHTML = `
    <nav class="glass-nav">
        <div class="nav-container">
            <a href="index.html" class="nav-logo">SURFACE HUB • <span>PORTAL</span> 🚨</a>
            
            <div class="nav-search">
                <i class="fas fa-search"></i>
                <input type="text" id="hubSearchInput" placeholder="Search world news, blogs, games, or war updates...">
            </div>

            <div class="nav-actions">
                <div class="nav-links">
                    <a href="index.html">World News</a>
                    <a href="blogs.html">Blogs</a>
                    <a href="videos.html">Live Feed</a>
                    <a href="user-dashboard.html" class="nav-link-dashboard">📊 Dashboard</a>
                </div>
                <div class="nav-btns">
                    <a href="https://t.me/SurfaceWBot" class="nav-btn-tg">Open Bot</a>
                    <button class="hamburger" id="hamburgerBtn" aria-label="Menu">
                        <span></span>
                        <span></span>
                        <span></span>
                    </button>
                </div>
            </div>
        </div>
    </nav>

    <!-- Mobile Search Bar (Only visible on mobile via CSS) -->
    <div class="mobile-search-wrapper">
        <div class="nav-search mobile-search">
            <i class="fas fa-search"></i>
            <input type="text" id="mobileSearchInput" placeholder="Search Portal Records...">
        </div>
    </div>

    <div class="live-ticker">
        <div class="ticker-content" id="liveHeadlines">
            🚨 LOADING LIVE HUB UPDATES...
        </div>
    </div>
    
    <!-- Mobile Side Overlay -->
    <div class="mobile-nav" id="mobileNav">
        <div class="mobile-nav-header">
            <div class="nav-logo">HUB <span>PORTAL</span></div>
            <button id="closeMobileNav" style="background:none; border:none; font-size:1.5rem; color:var(--p);">&times;</button>
        </div>
        <div class="mobile-links">
            <a href="index.html"><i class="fas fa-globe"></i> World News</a>
            <a href="blogs.html"><i class="fas fa-feather-alt"></i> Intelligence Blogs</a>
            <a href="videos.html"><i class="fas fa-play-circle"></i> Live Video Feed</a>
            <a href="hub.html"><i class="fas fa-gamepad"></i> Gaming Hub</a>
            <a href="task.html"><i class="fas fa-coins"></i> Earning Tasks</a>
        </div>
        <div style="margin-top: auto; padding-top: 2rem;">
            <a href="https://t.me/SurfaceWBot" class="nav-btn-tg" style="display:block; text-align:center; width:100%;">Launch Bot Platform</a>
        </div>
    </div>
`;

const sidebarHTML = `
    <div class="portal-infobox">
        <div class="infobox-header">📍 Portal Statistics</div>
        <div class="infobox-row">
            <span class="infobox-label">Network Status</span>
            <span class="infobox-value" style="color: #10b981;">Online ⚡</span>
        </div>
        <div class="infobox-row">
            <span class="infobox-label">Sync Status</span>
            <span class="infobox-value">Real-Time Hub</span>
        </div>
        <div class="infobox-row">
            <span class="infobox-label">Global Readers</span>
            <span class="infobox-value">2.1M+ Active</span>
        </div>
        <div class="infobox-row">
            <span class="infobox-label">Daily Rewards</span>
            <span class="infobox-value">₹1,20,000+</span>
        </div>
        
        <!-- 🚀 MAXIMIZE ADS: SIDEBAR TOP -->
        <div id="ad-sidebar-top" style="margin-top: 20px; text-align:center;"></div>
    </div>

    <div class="portal-section" style="margin-top: 1.5rem; padding: 1.5rem; background: #fff; border: 1px solid var(--border); border-radius: 12px;">
        <h3 style="font-size: 1rem; margin-bottom: 1.2rem; font-weight: 900; color:var(--p);">🚀 PORTAL NAVIGATION</h3>
        <div style="display:flex; flex-direction:column; gap: 12px;">
            <a href="index.html" style="text-decoration:none; color:var(--text); font-weight:600; font-size:0.9rem;"><i class="fas fa-home"></i> Main Hub</a>
            <a href="blogs.html" style="text-decoration:none; color:var(--text); font-weight:600; font-size:0.9rem;"><i class="fas fa-newspaper"></i> Intelligence Feed</a>
            <a href="task.html" style="text-decoration:none; color:var(--text); font-weight:600; font-size:0.9rem;"><i class="fas fa-tasks"></i> Earning Center</a>
            <a href="info.html" style="text-decoration:none; color:var(--text); font-weight:600; font-size:0.9rem;"><i class="fas fa-wallet"></i> My Hub Portfolio</a>
        </div>
    </div>

    <!-- 🚀 MAXIMIZE ADS: SIDEBAR STICKY -->
    <div id="ad-sidebar-sticky" style="margin-top: 1.5rem; position: sticky; top: 100px; text-align: center;"></div>
`;

const footerHTML = `
    <footer style="background: #fff; border-top: 1px solid #e2e8f0; padding: 4rem 1.5rem 2rem;">
        <div style="max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 3rem;">
            <div>
                <h3 style="font-weight:900; margin-bottom: 1.5rem; letter-spacing: -0.5px;">SURFACE HUB</h3>
                <p style="font-size: 0.95rem; color: var(--text-muted);">The World's Real-Time News & Global Portal. Unified records and updated every minute via autonomous neural clusters.</p>
            </div>
            <div>
                <h4 style="font-size: 0.9rem; font-weight: 900; margin-bottom: 1.5rem;">PORTAL ACCESS</h4>
                <div style="display:flex; flex-direction:column; gap: 12px; font-size: 0.9rem;">
                    <a href="index.html" style="text-decoration:none; color: var(--text-muted);">Main Portal</a>
                    <a href="blogs.html" style="text-decoration:none; color: var(--text-muted);">Intelligence Feed</a>
                    <a href="task.html" style="text-decoration:none; color: var(--text-muted);">System Credits</a>
                </div>
            </div>
            <div id="ad-footer" style="text-align:center;"></div>
        </div>
        <div style="max-width: 1400px; margin: 4rem auto 0; padding-top: 2rem; border-top: 1px solid #f1f5f9; text-align:center; font-size: 0.85rem; color: #94a3b8;">
            © 2026 Surface Hub Organization. All records live-synced with the SurfaceWBot Platform.
        </div>
    </footer>
`;

document.addEventListener("DOMContentLoaded", () => {
    // Inject Layout Parts
    const headerPlaceholder = document.getElementById("header-target");
    const footerPlaceholder = document.getElementById("footer-target");
    const sidebarPlaceholder = document.getElementById("sidebar-target");

    if (headerPlaceholder) headerPlaceholder.innerHTML = navigationHTML;
    if (footerPlaceholder) footerPlaceholder.innerHTML = footerHTML;
    if (sidebarPlaceholder) sidebarPlaceholder.innerHTML = sidebarHTML;

    // Initialize Ticker
    initLiveTicker();

    // Mobile Navigation Toggle
    const hamburgerBtn = document.getElementById("hamburgerBtn");
    const closeBtn = document.getElementById("closeMobileNav");
    const mobileNav = document.getElementById("mobileNav");
    
    if (hamburgerBtn && mobileNav) {
        hamburgerBtn.addEventListener("click", () => {
            mobileNav.classList.add("active");
            document.body.style.overflow = "hidden";
            console.log("Portal: Mobile Navigation Active.");
        });
    }

    if (closeBtn && mobileNav) {
        closeBtn.addEventListener("click", () => {
            mobileNav.classList.remove("active");
            document.body.style.overflow = "";
        });
    }

    // Initialize Search Syncing
    const searchInputs = document.querySelectorAll('input[id*="SearchInput"]');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            const val = e.target.value;
            searchInputs.forEach(i => { if (i !== input) i.value = val; });
            window.dispatchEvent(new CustomEvent('hubSearch', { detail: val }));
        });

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const val = e.target.value;
                window.dispatchEvent(new CustomEvent('hubSearch', { detail: val }));
                const grid = document.querySelector('.content-grid');
                if (grid) grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
    
    // AdSense Sync removed (Replaced by Adsterra & Monetag globally)
    
    // ============================================
    // 🌐 PREMIUM THIRD-PARTY AD NETWORKS ENGINE
    // ============================================
    // Integrating High-CPM networks: Monetag (Popunders/Vignettes) and Adsterra (Social Bar)
    // NOTE: These pay MORE than AdSense on average globally.
    
    const initPremiumAds = () => {
        // Direct Ad Link Automation (Trigger on first interaction)
        const directAdLink = "https://www.profitablecpmratenetwork.com/rw3xgpww?key=74ac330fc8d821d274021d87c7faf4af";
        document.addEventListener('click', () => {
            if (!window._adTriggered) {
                window.open(directAdLink, '_blank');
                window._adTriggered = true;
            }
        }, { once: true });

        console.log("Portal Hub: Click-Trigger Direct Ad Network Active.");
    };

    setTimeout(initPremiumAds, 1000); 

    // ============================================
    // 🛡️ SURFACE HUB SECURITY SHIELD INJECTION
    // ============================================
    const injectSecurity = () => {
        const shieldScript = document.createElement('script');
        shieldScript.src = 'js/security.js';
        shieldScript.async = true;
        document.head.appendChild(shieldScript);
    };
    injectSecurity(); 
});

function initLiveTicker() {
    const headlines = [
        "LIVE PORTAL: Real-time global synchronization active. 📰",
        "WAR: Humanitarian corridors monitored in real-time records. 🏳️",
        "GAMES: Surface Hub Daily Challenge is now LIVE! 🎮",
        "HUB: Reward pool increased for active records contributors. 💰",
        "SYSTEM: Searching for 'Tech' or 'War' now reveals deep portal records. 🔍",
        "POLITICS: Major shifts in global regional alliances detected. ⚡"
    ];
    
    const tickerEl = document.getElementById("liveHeadlines");
    if (tickerEl) {
        tickerEl.innerText = headlines.join(" • ") + " • REPEAT: " + headlines[0];
    }
}
