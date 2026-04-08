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
            
            // Build CORS-proxy request to bypass browser CORS restrictions
            const corsUrl = `https://api.codetabs.com/v1/proxy?quest=${encodeURIComponent(this.API_URL)}`;
            
            // Direct ShrinkEarn API call
            const params = new URLSearchParams({
                api: this.API_KEY,
                url: longUrl
            });
            
            const response = await fetch(`${this.API_URL}?${params.toString()}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                }
            });
            
            // If response fails due to CORS, try alternative method
            if (!response.ok) {
                console.warn("⚠️ Direct API call failed, using endpoint without headers");
                const altResponse = await fetch(`${this.API_URL}?api=${this.API_KEY}&url=${encodeURIComponent(longUrl)}`);
                
                if (!altResponse.ok) {
                    throw new Error("ShrinkEarn API unavailable");
                }
                
                const data = await altResponse.json();
                
                if (data.status === "success" && data.shortenedUrl) {
                    this.cache[longUrl] = data.shortenedUrl;
                    console.log("✅ Shortlink created:", data.shortenedUrl);
                    return data.shortenedUrl;
                }
            } else {
                const data = await response.json();
                
                if (data.status === "success" && data.shortenedUrl) {
                    this.cache[longUrl] = data.shortenedUrl;
                    console.log("✅ Shortlink created:", data.shortenedUrl);
                    return data.shortenedUrl;
                }
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
