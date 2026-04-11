/**
 * ShrinkEarn Shortlink Service
 * Automatically shortens URLs for social sharing with ShrinkEarn
 */

const ShortlinkService = {
    // ShrinkEarn API Configuration
    API_KEY: "9cb7dcf0e024c3b2456fb5dde48e1d4cd0a093b1",
    API_URL: "https://shrinkearn.com/api",
    
    // Cache shortened URLs to avoid repeated requests
    cache: {},
    
    /**
     * Shorten a URL using ShrinkEarn API
     * @param {string} longUrl - The URL to shorten
     * @returns {Promise<string>} - Shortened URL or original if fails
     */
    async shortenUrl(longUrl) {
        if (!longUrl) return longUrl;
        
        // Check cache first
        if (this.cache[longUrl]) {
            console.log("📦 Shortlink (cached):", this.cache[longUrl]);
            return this.cache[longUrl];
        }
        
        try {
            console.log("🔗 Shortening URL:", longUrl.substring(0, 50) + "...");
            
            // Use AllOrigins Proxy to bypass CORS
            const params = new URLSearchParams({
                api: this.API_KEY,
                url: longUrl
            });
            const apiUrl = `${this.API_URL}?${params.toString()}`;
            const proxyUrl = `https://api.allorigins.win/get?url=${encodeURIComponent(apiUrl)}`;
            
            const response = await fetch(proxyUrl);
            if (!response.ok) throw new Error("CORS Proxy failed");
            
            const proxyData = await response.json();
            const data = JSON.parse(proxyData.contents);
            
            if (data.status === "success" && data.shortenedUrl) {
                this.cache[longUrl] = data.shortenedUrl;
                console.log("✅ Shortened (Proxy):", data.shortenedUrl);
                return data.shortenedUrl;
            }
            
        } catch (error) {
            console.error("❌ Shortlink service error:", error.message);
        }
        
        // Return original URL if shortening fails
        console.log("📌 Using original URL (shortening failed)");
        return longUrl;
    },
    
    /**
     * Get shortened URL (async wrapper)
     * @param {string} url - URL to shorten
     * @returns {Promise<string>}
     */
    async getShortUrl(url) {
        return await this.shortenUrl(url);
    },
    
    /**
     * Clear the cache
     */
    clearCache() {
        this.cache = {};
        console.log("🧹 Shortlink cache cleared");
    }
};

// Make available globally
window.ShortlinkService = ShortlinkService;
