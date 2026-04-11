/**
 * Surface Hub - Premium Ad Manager 🛰️💰
 * Injects Adsterra/ProfitableCPM scripts into the portal dynamically.
 */

const AdManager = {
    SCRIPTS: {
        BANNER_728: "https://www.highperformanceformat.com/bfb9ddbec7e3e5681a5312f48a68bb2e/invoke.js",
        SOCIAL_BAR: "https://pl29071710.profitablecpmratenetwork.com/dafa116820cb26f5e3dc4219757633bf/invoke.js",
        RECT_300: "https://www.highperformanceformat.com/4c130fd19d0381c4f42d8cdf70579cad/invoke.js",
        BANNER_468: "https://www.highperformanceformat.com/e92210dbd77db33df4ffd95395c4c63a/invoke.js",
        FLOATING_1: "https://pl29071708.profitablecpmratenetwork.com/be/d4/a7/bed4a7d2f891321adb05fbd064bb1832.js",
        FLOATING_2: "https://pl29071707.profitablecpmratenetwork.com/78/7c/78/787c786a9cb2487ccb9000abb92ae3f1.js"
    },

    init() {
        console.log("🏙️ Ad Manager: Initiating Global Monetization...");
        this.injectGlobalScripts();
        this.injectPlaceholders();
    },

    injectGlobalScripts() {
        // Floating/Sticky Scripts (Auto-inject into body)
        [this.SCRIPTS.FLOATING_1, this.SCRIPTS.FLOATING_2].forEach(src => {
            const s = document.createElement('script');
            s.src = src;
            s.async = true;
            document.body.appendChild(s);
        });

        // Social Bar Container & Script
        const socialContainer = document.createElement('div');
        socialContainer.id = "container-dafa116820cb26f5e3dc4219757633bf";
        document.body.appendChild(socialContainer);
        
        const socialScript = document.createElement('script');
        socialScript.src = this.SCRIPTS.SOCIAL_BAR;
        socialScript.async = true;
        socialScript.setAttribute('data-cfasync', 'false');
        document.body.appendChild(socialScript);
    },

    injectPlaceholders() {
        // Use MutationObserver to wait for content if needed, 
        // but for now, we'll try immediate injection into known IDs.
        
        // 1. TOP AD (728x90)
        this.renderIframeAd('ad-portal-top', 'bfb9ddbec7e3e5681a5312f48a68bb2e', 728, 90);
        
        // 2. MIDDLE AD (300x250)
        this.renderIframeAd('ad-portal-middle', '4c130fd19d0381c4f42d8cdf70579cad', 300, 250);
        
        // 3. BOTTOM AD (468x60)
        this.renderIframeAd('ad-portal-bottom', 'e92210dbd77db33df4ffd95395c4c63a', 468, 60);

        // 4. SIDEBAR AD (160x600) - Assuming existing ID if available
        this.renderIframeAd('ad-portal-side', 'cd98d03308146826f3d0f52131597280', 160, 600);
    },

    renderIframeAd(containerId, key, width, height) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = ''; // Clear fallback
        
        const script = document.createElement('script');
        script.innerHTML = `
            atOptions = {
                'key' : '${key}',
                'format' : 'iframe',
                'height' : ${height},
                'width' : ${width},
                'params' : {}
            };
        `;
        container.appendChild(script);

        const invoke = document.createElement('script');
        invoke.src = `https://www.highperformanceformat.com/${key}/invoke.js`;
        container.appendChild(invoke);
        
        console.log(`🎯 Ad Injected: ${containerId} (${key})`);
    }
};

// Start Ad Manager
document.addEventListener('DOMContentLoaded', () => AdManager.init());
