"""
Wallet & Profile Handlers - Phase 7
Display user balance, earnings, and referral information
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import services.firebase as db
from utils.referral_manager import get_referral_code, get_referral_statistics
from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)


async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display user's wallet with real-time balance and earnings"""
    user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        msg = "❌ User not found"
    else:
        balance = user.get("balance", 0)
        earnings = user.get("earnings", {})
        
        wallet_msg = (
            f"💎 *YOUR WALLET*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            
            f"💰 Current Balance: ₹{balance}\n\n"
            
            f"📊 *Earnings Breakdown:*\n"
            f"📋 Tasks Completed: {earnings.get('tasks_completed', 0)}\n"
            f"   └─ Earned: ₹{earnings.get('tasks_completed', 0) * 10}\n"
            
            f"🎁 Referral Bonus: ₹{earnings.get('referral_bonus', 0)}\n\n"
            
            f"💵 Total Earned (All Time): ₹{earnings.get('total_earned', 0)}\n\n"
            
            f"📈 Progress to 25 tasks: {earnings.get('tasks_completed', 0)}/25 "
            f"{'✅' if earnings.get('tasks_completed', 0) >= 25 else '⏳'}\n"
        )
        
        if user.get("referrals", {}).get("bonus_awarded"):
            wallet_msg += f"🎊 Referral Bonus: Unlocked ✅\n"
        else:
            wallet_msg += f"🎊 Referral Bonus: Locked (25 tasks needed)\n"
        
        msg = wallet_msg
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Earn More", callback_data="btn_earn")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="btn_wallet")],
        [InlineKeyboardButton("📋 Menu", callback_data="btn_start")]
    ])
    
    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await update.callback_query.message.edit_text(msg, parse_mode="Markdown", reply_markup=keyboard)


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display user profile with referral code and stats"""
    user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        msg = "❌ User not found"
    else:
        referral_code = get_referral_code(user_id)
        stats = get_referral_statistics(user_id)
        
        profile_msg = (
            f"👤 *YOUR PROFILE*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            
            f"👤 Username: @{user.get('username', 'N/A')}\n"
            f"🆔 ID: `{user_id}`\n"
            f"📅 Joined: <recent>\n\n"
            
            f"🔗 *Referral Code:*\n"
            f"`{referral_code}`\n\n"
            
            f"👥 *Referrals:*\n"
            f"Total: {stats.get('total_referred', 0)}\n"
            f"Active: {stats.get('active_referrals', 0)}\n"
            f"Eligible: {stats.get('qualified_for_bonus', 0)}\n\n"
            
            f"🎯 *Account Status:*\n"
            f"Deposit: {'✅ Active' if user.get('deposit_status') else '❌ Pending'}\n"
            f"Tasks: {user.get('earnings', {}).get('tasks_completed', 0)}/25\n"
        )
        msg = profile_msg
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 My Referrals", callback_data="referral_list")],
        [InlineKeyboardButton("💎 Wallet", callback_data="btn_wallet")],
        [InlineKeyboardButton("📋 Menu", callback_data="btn_start")]
    ])
    
    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await update.callback_query.message.edit_text(msg, parse_mode="Markdown", reply_markup=keyboard)
