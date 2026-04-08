import os
from dotenv import load_dotenv
import logging

# Load env from parent dir
load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO)

# Import services
import sys
# Add 'bot' directory to path so 'services.xxx' works
current_dir = os.path.dirname(os.path.abspath(__file__))
bot_dir = os.path.join(current_dir, 'bot')
if bot_dir not in sys.path:
    sys.path.insert(0, bot_dir)

try:
    from services.news_agent import AIAgent
except ImportError as e:
    print(f"❌ Initial import failed: {e}")
    # Try one more level
    sys.path.insert(0, current_dir)
    from bot.services.news_agent import AIAgent

if __name__ == "__main__":
    print("🚀 Triggering Autonomous AI News Sweep (Test Mode)...")
    agent = AIAgent()
    agent.run_update()
    print("✅ Test Complete. Check your Firebase or Portal Website now!")
