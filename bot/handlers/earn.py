"""
Earn Handler - Overhauled Web-Only Flow
New 2-Step Verification: Shortlink → Home (10s) → Random Page (20s) → Claim
"""
import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import services.firebase as db
from config import WEBSITE_BASE_URL, TASK_COMPLETION_REWARD
from utils.reward_manager import generate_reward_token
from utils.keyboards import main_menu_keyboard
from utils.shortlink import ShortlinkService

logger = logging.getLogger(__name__)

async def earn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start earn workflow - Generates a monetized web link
    """
    user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    # 1. Check user has deposited (Activation check)
    user = db.get_user(user_id)
    if not user or not user.get("deposit_status"):
        msg = (
            "⚠️ *Account Not Activated*\n\n"
            "To unlock earning tasks, you must deposit ₹50 first. "
            "This ensures you are a real user."
        )
        keyboard = [[InlineKeyboardButton("💳 Deposit ₹50 Now", callback_data="btn_deposit")]]
        
        if update.message:
            await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.callback_query.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # 2. Daily Limit Check (Optional, but good for stability)
    # Could check how many tasks completed today here.

    # 3. Generate Secure Reward Token
    # Unique task ID for this session
    import uuid
    task_id = f"web_{str(uuid.uuid4())[:6]}"
    
    token = generate_reward_token(user_id, task_id, TASK_COMPLETION_REWARD)
    
    # 4. Construct Destination URL (Website Home Page with step=1)
    # Using the website root as the starting point
    destination_url = f"{WEBSITE_BASE_URL}/index.html?token={token}&step=1"
    
    # 5. Shorten via ShrinkEarn
    short_url = ShortlinkService.get_short_url(destination_url)
    
    # 6. Send Earning Message
    earn_msg = (
        "🤑 *EARN TASK AVAILABLE*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💰 *Reward:* ₹10\n"
        "⏱️ *Duration:* ~30 seconds\n"
        "🔗 *Type:* Web Verification\n\n"
        
        "📋 *Instructions:*\n"
        "1️⃣  Click the button below to start.\n"
        "2️⃣  Wait 10s on the Home page.\n"
        "3️⃣  Continue to a random page and wait 20s.\n"
        "4️⃣  Click 'Claim' to get your money!\n\n"
        
        "⚠️ *Note:* Don't close the browser until you see 'Verification Complete'."
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 START TASK (₹10)", url=short_url)],
        [InlineKeyboardButton("💎 Wallet", callback_data="btn_wallet"), InlineKeyboardButton("📋 Menu", callback_data="btn_start")]
    ])
    
    if update.message:
        await update.message.reply_text(earn_msg, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await update.callback_query.message.edit_text(earn_msg, parse_mode="Markdown", reply_markup=keyboard)

# Old stage handlers removed as per requirements (in-bot earning disabled)
