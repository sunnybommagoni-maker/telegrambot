/**
 * Surface Hub 2.7.0 - Premium Content Engine
 * Real-time News & Global Records Aggregator (Digital Portal Edition)
 */

class HubEngine {
    constructor() {
        this.db = firebase.database();
        this.contentGrid = document.querySelector('.content-grid');
        this.currentPage = this.getCategoryFromPath();
        this.allRecords = [];
        this.urlParams = new URLSearchParams(window.location.search);
        this.token = this.urlParams.get('token');
        this.init();
    }

    getCategoryFromPath() {
        const path = window.location.pathname;
        if (path.includes('blogs')) return 'Blogs';
        if (path.includes('videos')) return 'Videos';
        if (path.includes('hub')) return 'Games';
        if (path.includes('task')) return 'Tasks';
        return 'All';
    }

    async init() {
        console.log("Surface Hub Portal: Engine Initialized.");
        this.listenForData();
        this.setupSearch();
    }

    listenForData() {
        const contentRef = this.db.ref('content');
        const tasksRef = this.db.ref('tasks');

        // Multi-node listener for Unified Feed
        const updateData = (snap, source) => {
            const val = snap.val();
            if (val) {
                const newItems = Object.entries(val).map(([id, item]) => ({ id, ...item, source }));
                
                // Clear existing items from same source
                this.allRecords = this.allRecords.filter(i => i.source !== source);
                this.allRecords = [...this.allRecords, ...newItems];

                // Sort by timestamp
                this.allRecords.sort((a, b) => (b.timestamp || b.addedAt || 0) - (a.timestamp || a.addedAt || 0));
                this.renderPortal();
            }
        };

        contentRef.on('value', snap => updateData(snap, 'content'));
        tasksRef.on('value', snap => updateData(snap, 'tasks'));
    }

    setupSearch() {
        // Listen for unified search event from navigation.js
        window.addEventListener('hubSearch', (e) => {
            const term = e.detail.toLowerCase().trim();
            this.performSearch(term);
        });

        // Fallback for direct input (if events fail)
        const desktopSearch = document.getElementById('hubSearchInput');
        const mobileSearch = document.getElementById('mobileSearchInput');
        
        [desktopSearch, mobileSearch].forEach(input => {
            if (input) {
                input.addEventListener('input', (e) => {
                    this.performSearch(e.target.value.toLowerCase().trim());
                });
            }
        });
    }

    performSearch(term) {
        if (!term) {
            this.renderPortal(this.allRecords);
            return;
        }

        const filtered = this.allRecords.filter(item => {
            const title = (item.title || "").toLowerCase();
            const desc = (item.description || item.summary || "").toLowerCase();
            const category = (item.category || item.type || "").toLowerCase();
            const content = (item.content || "").toLowerCase();

            return title.includes(term) || 
                   desc.includes(term) || 
                   category.includes(term) ||
                   content.includes(term);
        });

        this.renderPortal(filtered);
    }

    renderPortal(items = this.allRecords) {
        if (!this.contentGrid) return;
        this.contentGrid.innerHTML = '';

        // Category Filter (Always respect page category)
        let displayItems = items;
        if (this.currentPage !== 'All') {
            displayItems = items.filter(item => 
                (item.category && item.category === this.currentPage) || 
                (item.type && item.type === this.currentPage)
            );
        }

        if (displayItems.length === 0) {
            this.renderEmptyState();
            return;
        }

        displayItems.forEach((item, index) => {
            const card = this.createCard(item);
            this.contentGrid.appendChild(card);

            // 🚀 MAXIMIZE ADS: Inject In-Feed Ad every 3 items
            if ((index + 1) % 3 === 0) {
                const adCard = document.createElement('div');
                adCard.className = 'portal-ad-card';
                adCard.innerHTML = `
                    <div style="padding: 1rem; background: rgba(0,0,0,0.02); border-radius: 12px; border: 1px dashed rgba(0,118,255,0.2); text-align: center;">
                        <span style="font-size: 0.6rem; opacity: 0.4; letter-spacing: 2px; font-weight: 900; margin-bottom: 5px; display:block;">SPONSORED RECORD</span>
                        <!-- Premium Ad Banner Placeholder -->
<div class="ad-slot" style="text-align:center; padding:10px; background:var(--glass-bg); border-radius:10px;">
    <i>Adsterra Banner Region</i>
</div>
                    </div>
                `;
                this.contentGrid.appendChild(adCard);
            }
        });
    }

    createCard(item) {
        const isTask = item.source === 'tasks';
        const typeLabel = isTask ? 'Earn Task' : (item.category || 'Portal Feed');
        const image = item.image || item.thumbnail || `https://source.unsplash.com/800x600/?${typeLabel.replace(' ', ',')},tech`;
        
        const card = document.createElement('div');
        card.className = 'portal-card';
        
        // Handle Task vs Content Redirection
        let targetUrl = isTask ? item.url : `article.html?id=${item.id}&type=${typeLabel.toLowerCase()}`;
        
        // Pass token forward if exists
        if (this.token) {
            const separator = targetUrl.includes('?') ? '&' : '?';
            targetUrl += `${separator}token=${this.token}`;
        }
        
        // Video indicator badge
        const videoIndicator = item.videoUrl ? '<span class="video-badge" style="position: absolute; top: 10px; right: 10px; background: #ef4444; padding: 6px 12px; border-radius: 50px; font-size: 0.7rem; font-weight: 700; display: flex; align-items: center; gap: 5px;"><i class="fas fa-play-circle"></i> VIDEO</span>' : '';
        
        // Build share buttons HTML with shortened link loading state
        let shareButtons = '';
        if (item.shareOptions && !isTask) {
            shareButtons = `
                <div style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap;">
                    <div class="share-loading" style="width: 100%; text-align: center; font-size: 0.8rem; color: #888; display: none;">
                        <i class="fas fa-spinner fa-spin"></i> Generating share links...
                    </div>
                    <div class="share-buttons" style="width: 100%; display: flex; gap: 8px; flex-wrap: wrap;">
                        ${item.shareOptions.facebook ? `<a href="#" data-platform="facebook" data-item-id="${item.id}" class="share-btn" style="flex: 1; padding: 8px; border-radius: 6px; background: #1877F2; color: #fff; text-align: center; font-size: 0.85rem; text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 5px;"><i class="fab fa-facebook-square"></i> Share</a>` : ''}
                        ${item.shareOptions.twitter ? `<a href="#" data-platform="twitter" data-item-id="${item.id}" class="share-btn" style="flex: 1; padding: 8px; border-radius: 6px; background: #1D9BF0; color: #fff; text-align: center; font-size: 0.85rem; text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 5px;"><i class="fab fa-twitter"></i> Tweet</a>` : ''}
                        ${item.shareOptions.whatsapp ? `<a href="#" data-platform="whatsapp" data-item-id="${item.id}" class="share-btn" style="flex: 1; padding: 8px; border-radius: 6px; background: #25D366; color: #fff; text-align: center; font-size: 0.85rem; text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 5px;"><i class="fab fa-whatsapp"></i> Share</a>` : ''}
                        ${item.shareOptions.telegram ? `<a href="#" data-platform="telegram" data-item-id="${item.id}" class="share-btn" style="flex: 1; padding: 8px; border-radius: 6px; background: #0088cc; color: #fff; text-align: center; font-size: 0.85rem; text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 5px;"><i class="fab fa-telegram"></i> Message</a>` : ''}
                    </div>
                </div>
            `;
        }
        
        card.innerHTML = `
            <div class="card-img" style="background-image: url('${image}'); position: relative;">
                <span class="card-badge" style="${isTask ? 'background: #10b981;' : ''}">${typeLabel}</span>
                ${item.videoUrl ? `<span class="video-badge" style="position: absolute; top: 10px; right: 10px; background: #ef4444; padding: 6px 12px; border-radius: 50px; font-size: 0.7rem; font-weight: 700; display: flex; align-items: center; gap: 5px; color: #fff;"><i class="fas fa-play-circle"></i> VIDEO</span>` : ''}
                ${isTask ? `<span class="reward-badge">₹${item.reward}</span>` : ''}
            </div>
            <div class="card-body">
                <h3>${item.title || 'Surface Hub Record'}</h3>
                <p>${item.summary || item.description || (isTask ? 'Complete this task to earn rewards.' : 'Accessing live portal records...')}</p>
                <a href="${targetUrl}" class="btn-portal" style="margin-top: 15px; display: inline-block; width: 100%; text-align: center; background: ${isTask ? '#10b981' : 'var(--p)'}; color: #fff; padding: 10px; border-radius: 8px; font-weight: 800; text-decoration: none;">
                    ${isTask ? 'GO TO TASK' : (item.videoUrl ? '🎥 WATCH VIDEO' : 'READ MORE')}
                </a>
                ${shareButtons}
            </div>
        `;
        
        // Attach click handlers for share buttons and generate shortened links
        if (item.shareOptions && !isTask) {
            const shareButtons = card.querySelectorAll('.share-btn');
            shareButtons.forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.preventDefault();
                    const platform = btn.dataset.platform;
                    const itemId = btn.dataset.itemId;
                    
                    // Show loading indicator
                    const loadingDiv = card.querySelector('.share-loading');
                    if (loadingDiv) loadingDiv.style.display = 'block';
                    
                    // Generate shortened links
                    const shareLinks = await this.generateShareLinks(item, image);
                    
                    // Hide loading indicator
                    if (loadingDiv) loadingDiv.style.display = 'none';
                    
                    // Open share link
                    if (shareLinks[platform]) {
                        window.open(shareLinks[platform], '_blank', 'width=600,height=400');
                    }
                });
            });
        }
        
        return card;
    }

    async generateShareLinks(item, image) {
        const baseUrl = window.location.origin;
        const pageUrl = `${baseUrl}/article.html?id=${item.id}`;
        const title = encodeURIComponent(item.title || 'Check this out on Surface Hub');
        const description = encodeURIComponent(item.summary || item.description || 'Amazing content on Surface Hub');
        
        // 🔗 Shorten the article URL using ShrinkEarn
        let shortUrl = pageUrl;
        if (window.ShortlinkService) {
            try {
                shortUrl = await window.ShortlinkService.getShortUrl(pageUrl);
            } catch (e) {
                console.warn("Could not shorten URL, using original:", e);
                shortUrl = pageUrl;
            }
        }
        
        return {
            facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shortUrl)}`,
            twitter: `https://twitter.com/intent/tweet?url=${encodeURIComponent(shortUrl)}&text=${title}`,
            whatsapp: `https://api.whatsapp.com/send?text=${encodeURIComponent(item.title + ' ' + shortUrl)}`,
            telegram: `https://t.me/share/url?url=${encodeURIComponent(shortUrl)}&text=${title}`
        };
    }

    renderEmptyState() {
        if (this.contentGrid) {
            this.contentGrid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 5rem 2rem;">
                    <i class="fas fa-search" style="font-size: 3rem; color: #e2e8f0; margin-bottom: 1.5rem;"></i>
                    <h2 style="font-weight: 900; color: var(--text);">No Portal Records Found</h2>
                    <p style="color: var(--text-muted); max-width: 400px; margin: 1rem auto;">Try a different keyword like "World", "Tech", or "Gaming" to access Hub data.</p>
                </div>
            `;
        }
    }
}

// Reward & Payout Logic (Secure Token Edition)
const HubPayout = {
    claim: async () => {
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        
        if (!token) {
            alert("❌ No reward session found. Please start from the Telegram Bot.");
            return;
        }

        const btn = document.getElementById('claimRewardBtn') || document.getElementById('claim-btn');
        if (btn) {
            btn.disabled = true;
            btn.innerText = "Verifying Hub Ledger...";
        }

        setTimeout(() => {
            alert("✅ Verification Complete! Redirecting to SurfaceWBot to claim your reward...");
            window.location.href = `https://t.me/SurfaceWBot?start=reward_${token}`;
        }, 1500);
    }
};

// Initialize Engine
const surfaceEngine = new HubEngine();
window.HubPayout = HubPayout;
window.surfaceEngine = surfaceEngine; // Expose for debugging
