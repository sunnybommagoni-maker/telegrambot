"""
Earn Handler - Phase 5
3-stage earning workflow: 10s wait → 20s wait → Claim ₹10
"""
import logging
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import services.firebase as db
from utils.firebase_transactions import process_task_completion
from utils.referral_manager import check_referral_bonus_trigger
from config import TASK_COMPLETION_REWARD
from utils.keyboards import main_menu_keyboard
from utils.reward_manager import generate_reward_token
from config import WEBSITE_BASE_URL

logger = logging.getLogger(__name__)

# Track active earn sessions: {user_id: {"stage": 1-3, "task_id": "...", "start_time": timestamp}}
EARN_SESSIONS = {}


async def earn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start earn workflow - Stage 1: 10-second wait
    """
    user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
    
    # Check user has deposited
    user = db.get_user(user_id)
    if not user or not user.get("deposit_status"):
        msg = "❌ Please deposit ₹50 first to activate earning."
        if update.message:
            await update.message.reply_text(msg, reply_markup=main_menu_keyboard())
        else:
            await update.callback_query.message.reply_text(msg, reply_markup=main_menu_keyboard())
        return
    
    # Generate unique task ID
    import uuid
    task_id = str(uuid.uuid4())[:8]
    
    # Track session
    EARN_SESSIONS[user_id] = {
        "stage": 1,
        "task_id": task_id,
        "start_time": int(time.time())
    }
    
    # Stage 1 message
    stage1_msg = (
        "⏳ *STAGE 1: WARM UP*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔄 Processing your task...\n"
        "⏱️  10 seconds remaining\n\n"
        "*Tap Continue when ready!*"
    )
    
    # Generate a browsing session token
    web_token = generate_reward_token(user_id, "browsing_tasks", TASK_COMPLETION_REWARD)
    web_url = f"{WEBSITE_BASE_URL}/task.html?token={web_token}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Browse Website Tasks", url=web_url)],
        [InlineKeyboardButton("▶️ Continue In-Bot →", callback_data=f"earn_stage2_{user_id}_{task_id}")]
    ])
    
    if update.message:
        await update.message.reply_text(stage1_msg, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await update.callback_query.message.reply_text(stage1_msg, parse_mode="Markdown", reply_markup=keyboard)


async def stage2_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Stage 2: 20-second wait
    Callback: earn_stage2_{user_id}_{task_id}
    """
    query = update.callback_query
    await query.answer()
    
    try:
        parts = query.data.split("_")
        user_id = int(parts[2])
        task_id = parts[3]
    except (IndexError, ValueError):
        await query.message.reply_text("❌ Invalid earn session")
        return
    
    # Verify session exists
    if user_id not in EARN_SESSIONS or EARN_SESSIONS[user_id]["task_id"] != task_id:
        await query.message.reply_text("❌ Earn session expired. Start again.", reply_markup=main_menu_keyboard())
        return
    
    # Update session
    EARN_SESSIONS[user_id]["stage"] = 2
    
    # Stage 2 message
    stage2_msg = (
        "⏳ *STAGE 2: PROCESSING*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🟢 Connection established\n"
        "📊 Calculating reward pool...\n"
        "⏱️  20 seconds remaining\n\n"
        "*You're almost there!*"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Claim Reward →", callback_data=f"earn_claim_{user_id}_{task_id}")]
    ])
    
    await query.message.edit_text(stage2_msg, parse_mode="Markdown", reply_markup=keyboard)


async def claim_reward_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Stage 3: Claim reward - Award ₹10
    Callback: earn_claim_{user_id}_{task_id}
    """
    query = update.callback_query
    await query.answer()
    
    try:
        parts = query.data.split("_")
        user_id = int(parts[2])
        task_id = parts[3]
    except (IndexError, ValueError):
        await query.message.reply_text("❌ Invalid earn session")
        return
    
    # Verify session exists
    if user_id not in EARN_SESSIONS or EARN_SESSIONS[user_id]["task_id"] != task_id:
        await query.message.reply_text("❌ Earn session expired. Start again.", reply_markup=main_menu_keyboard())
        return
    
    # Process task completion and add ₹10 reward
    try:
        result = process_task_completion(user_id, task_id)
        
        if result.get("success"):
            # Claim message
            claim_msg = (
                "✅ *REWARD CLAIMED!*\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💰 Earned: ₹{TASK_COMPLETION_REWARD}\n"
                f"📈 Total: {result.get('tasks_count', 0)}/25 tasks\n"
                f"💳 New Balance: ₹{result.get('new_balance', 0)}\n\n"
            )
            
            # Check for referral bonus
            bonus_result = check_referral_bonus_trigger(user_id)
            if bonus_result.get("bonus_awarded"):
                claim_msg += (
                    f"🎁 *REFERRAL BONUS AWARDED!*\n"
                    f"You & your friend earned ₹{TASK_COMPLETION_REWARD}\n\n"
                )
            
            claim_msg += "🔄 Earn more or check your wallet!"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Earn More", callback_data="btn_earn")],
                [InlineKeyboardButton("💎 Wallet", callback_data="btn_wallet")],
                [InlineKeyboardButton("📋 Menu", callback_data="btn_start")]
            ])
            
            await query.message.edit_text(claim_msg, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await query.message.reply_text(
                f"❌ {result.get('message', 'Error claiming reward')}",
                reply_markup=main_menu_keyboard()
            )
    
    except Exception as e:
        logger.error(f"❌ Error claiming reward: {e}")
        await query.message.reply_text(f"❌ Error: {str(e)}", reply_markup=main_menu_keyboard())
    
    finally:
        # Clean up session
        if user_id in EARN_SESSIONS:
            del EARN_SESSIONS[user_id]
