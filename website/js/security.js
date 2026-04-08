/**
 * SURFACE HUB SHIELD - Anti-Tamper Security v1.0.0
 * Blocks standard inspection, tampering and source discovery.
 */
(function() {
    'use strict';

    // 1. Disable Right Click
    document.addEventListener('contextmenu', (e) => e.preventDefault());

    // 2. Disable Common Inspection Key Commands
    document.addEventListener('keydown', (e) => {
        // Blocks F12, Ctrl+Shift+I, Ctrl+Shift+C (Inspect), Ctrl+Shift+J (Console), Ctrl+U (View Source)
        if (
            e.keyCode === 123 || 
            (e.ctrlKey && e.shiftKey && (e.keyCode === 73 || e.keyCode === 74 || e.keyCode === 67)) ||
            (e.ctrlKey && e.keyCode === 85)
        ) {
            e.preventDefault();
            return false;
        }
    });

    // 3. Console Anti-Debugging
    const blockConsole = () => {
        const warning = "⚠️ SECURITY ALERT: Unauthorized source manipulation attempt detected. This portal is monitored by Surface Hub Neural Cluster Sec.";
        setInterval(() => {
            console.clear();
            console.log("%c" + warning, "color: red; font-size: 20px; font-weight: bold;");
        }, 1000);
    };

    // 4. Prevent Selection (User-friendly version: only on sensitive UI)
    document.body.style.userSelect = 'none';
    document.body.style.webkitUserSelect = 'none';

    // 5. Detect DevTools Opening
    let devtoolsOpen = false;
    const threshold = 160;
    const checkDevTools = () => {
        const widthThreshold = window.outerWidth - window.innerWidth > threshold;
        const heightThreshold = window.outerHeight - window.innerHeight > threshold;
        if (widthThreshold || heightThreshold) {
            if (!devtoolsOpen) {
                console.warn("DevTools interaction detected.");
            }
            devtoolsOpen = true;
        } else {
            devtoolsOpen = false;
        }
    }
    
    window.addEventListener('resize', checkDevTools);
    setInterval(checkDevTools, 1000);

    console.log("Shield Active: Data Integrity Secured.");
})();
