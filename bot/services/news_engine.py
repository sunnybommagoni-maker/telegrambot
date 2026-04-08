import feedparser
import time
import threading
import random
from services.firebase import add_content, clear_old_content

# ─── Configuration ─────────────────────────────────────────────
# Verified RSS Feeds for Global Intelligence
FEEDS = {
    "World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Tech": "https://hnrss.org/frontpage",
    "Games": "https://www.gamespot.com/feeds/news/",
}

# Image Map for Visual Categories
CATEGORY_IMAGES = {
    "World": "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?q=80&w=800",
    "Tech": "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=800",
    "Games": "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800",
}

class NewsEngine:
    def __init__(self, interval=1800): # Default: Every 30 minutes
        self.interval = interval
        self.running = False
        self._thread = None

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            print("🌐 [Hub News Engine]: Autonomous Global Intelligence Active.")

    def stop(self):
        self.running = False

    def _run(self):
        while self.running:
            try:
                self.sync_all_feeds()
                # Prune content node to keep it performant
                clear_old_content(limit=30)
            except Exception as e:
                print(f"❌ [Hub News Engine]: Error during sync: {e}")
            
            time.sleep(self.interval)

    def sync_all_feeds(self):
        for category, url in FEEDS.items():
            print(f"🔄 [Hub News Engine]: Syncing category -> {category}")
            feed = feedparser.parse(url)
            
            # Mix up the order a bit for freshness
            entries = feed.entries[:5] 
            random.shuffle(entries)

            for entry in entries:
                title = entry.get('title', 'Surface Hub Intel')
                summary = entry.get('summary', 'Access live records for deep intelligence updates.')[:180] + "..."
                link = entry.get('link', 'https://t.me/SurfaceWBot')
                
                # Fetch image from entry if available, otherwise use category default
                image = None
                if 'media_content' in entry:
                    image = entry.media_content[0]['url']
                elif 'media_thumbnail' in entry:
                    image = entry.media_thumbnail[0]['url']
                
                if not image:
                    image = CATEGORY_IMAGES.get(category)

                # Add to Firebase
                add_content(
                    title=title,
                    summary=summary,
                    category=category,
                    image=image,
                    url=link
                )
                print(f"✅ Synced: {title[:30]}...")

if __name__ == "__main__":
    # Test sync
    engine = NewsEngine()
    engine.sync_all_feeds()
