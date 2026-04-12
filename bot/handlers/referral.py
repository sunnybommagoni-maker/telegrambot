"""
Referral Handler
Manages the /refer command and referral statistics display.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import services.firebase as db
from utils.referral_manager import get_referral_statistics
from config import WEBSITE_BASE_URL, REFERRAL_BONUS_REFERRER

async def refer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Shows referral stats and sharing options.
    """
    user = update.effective_user
    if not user:
        return

    user_id = user.id
    user_data = db.get_user(user_id)
    
    if not user_data:
        return # Should not happen if registered

    referrals = user_data.get("referrals", {})
    code = referrals.get("referral_code", "N/A")
    
    # Get stats
    stats = get_referral_statistics(user_id)
    total = stats.get("total_referred", 0)
    active = stats.get("active_referrals", 0)
    potential = stats.get("potential_earnings", 0)
    
    # Sharing Link
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start={code}"
    share_url = f"https://t.me/share/url?url={invite_link}&text=Join%20Surface%20Hub%20and%20start%20earning%20real%20cash!%20💰"

    msg = (
        "👥 *Refer & Earn System*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎁 *Reward:* Earn ₹{REFERRAL_BONUS_REFERRER} for every friend who joins and completes 25 tasks!\n\n"
        
        f"📊 *Your Statistics:*\n"
        f"• Total Referrals: `{total}`\n"
        f"• Active (Deposited): `{active}`\n"
        f"• Potential Earnings: `₹{potential}`\n\n"
        
        f"🔗 *Your Referral Link:*\n"
        f"`{invite_link}`\n\n"
        "Tap the button below to share with your friends and start earning!"
    )

    keyboard = [
        [InlineKeyboardButton("🚀 Share Invite Link", url=share_url)],
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="btn_start")]
    ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
