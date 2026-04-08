import sys
import os
import time

# Add bot directory to path for imports
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, ".."))
sys.path.append(os.path.join(_PROJECT_ROOT, "bot"))

from services import firebase as db

def inject():
    print("Initiating Content Refresh...")
    
    # 1. Global Tech Shift
    db.add_content(
        title="🚀 Global Tech Shift: Surface Hub Expansion",
        summary="Announcement of the Surface Hub's global expansion into 15+ new regions, bringing high-intelligence rewards to a massive audience.",
        category="Tech",
        image="https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&q=80&w=800"
    )
    
    # 2. Earnings Record
    db.add_content(
        title="💎 Record Milestone: ₹10 Lakhs Paid Out",
        summary="Verification of total user payouts exceeding ₹10,00,000. Verified and secured by autonomous portal nodes.",
        category="Finance",
        image="https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&q=80&w=800"
    )
    
    # 3. New High-Payout Games
    db.add_content(
        title="🎮 Premium Tasks: New High-Payout Games",
        summary="Integration of new premium gaming intelligence tasks. Earn up to ₹25 per specialized verification task.",
        category="Gaming",
        image="https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&q=80&w=800"
    )

    print("✅ Content Refresh Complete.")

if __name__ == "__main__":
    inject()
