"""
Referral Handler - Phase 6  
Display referral code and referral statistics
Bonus distribution happens automatically via process_task_completion()
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import services.firebase as db
from utils.referral_manager import get_referral_code, get_referral_statistics, get_all_referrals
from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)


async def referral_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display referral code and sharing instructions"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ User not found", reply_markup=main_menu_keyboard())
        return
    
    # Get or generate referral code
    referral_code = get_referral_code(user_id)
    stats = get_referral_statistics(user_id)
    
    ref_info = (
        f"👥 *Your Referral Code*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔗 Your Code: `{referral_code}`\n\n"
        
        f"📊 *Referral Stats:*\n"
        f"👫 Total Referred: {stats.get('total_referred', 0)}\n"
        f"✅ Active Friends: {stats.get('active_referrals', 0)}\n"
        f"🏷️  Pending: {stats.get('pending_referrals', 0)}\n"
        f"🎁 Qualified (25 tasks): {stats.get('qualified_for_bonus', 0)}\n"
        f"💰 Bonus Awarded: {'Yes ✅' if stats.get('bonus_awarded') else 'No'}\n\n"
        
        f"💵 *Earnings:*\n"
        f"Potential Earnings: ₹{stats.get('potential_earnings', 0)}\n\n"
        
        f"📢 *How to Share:*\n"
        f"Send this link to friends:\n"
        f"`/start {referral_code}`\n\n"
        
        f"🎉 *Your friend gets ₹20 bonus*\n"
        f"*You get ₹100 when they complete 25 tasks!*"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 My Referrals", callback_data="referral_list")],
        [InlineKeyboardButton("💎 Wallet", callback_data="btn_wallet")],
        [InlineKeyboardButton("📋 Menu", callback_data="btn_start")]
    ])
    
    if update.message:
        await update.message.reply_text(ref_info, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await update.callback_query.message.reply_text(ref_info, parse_mode="Markdown", reply_markup=keyboard)


async def referral_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display list of referred users with their status"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    referrals = get_all_referrals(user_id)
    
    if not referrals:
        list_msg = (
            "😴 *No Referrals Yet*\n\n"
            "Share your code with friends to earn ₹100 per referral!\n"
            "They get ₹20 bonus when they join."
        )
    else:
        list_msg = f"👥 *Your Referrals ({len(referrals)})*\n━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for ref in referrals:
            status_icon = "✅" if ref["status"] == "active" else "⏳"
            bonus_icon = "🎁" if ref["bonus_eligible"] else ""
            
            list_msg += (
                f"{status_icon} @{ref['username']}\n"
                f"   Tasks: {ref['tasks_completed']}/25 {bonus_icon}\n\n"
            )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Back to Referral", callback_data="btn_profile")],
        [InlineKeyboardButton("📋 Menu", callback_data="btn_start")]
    ])
    
    await query.message.edit_text(list_msg, parse_mode="Markdown", reply_markup=keyboard)
