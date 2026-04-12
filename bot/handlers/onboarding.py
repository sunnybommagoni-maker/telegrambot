"""
Welcome & Onboarding Handler
Manages new user signup flow, referral code validation, and initial setup
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import services.firebase as db
from utils.referral_manager import generate_referral_code, validate_and_link_referral
from utils.firebase_transactions import migrate_user_to_new_schema
from config import DEPOSIT_AMOUNT
import time
from utils.reward_manager import verify_and_claim_token
from utils.firebase_transactions import process_task_completion
from utils.keyboards import main_menu_keyboard


async def welcome_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    New user welcome flow with referral code parsing.
    Called from /start when user is new.
    """
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or str(user_id)
    
    # Parse referral code from deep link (/start REF_CODE)
    referred_by = None
    referral_code = None
    
    if context.args and len(context.args) > 0:
        try:
            referral_code = context.args[0]
            # Look up referrer from code
            referred_by_id = db.get_user_by_referral_code(referral_code)
            if referred_by_id and referred_by_id != user_id:
                referred_by = referred_by_id
        except Exception as e:
            print(f"⚠️ Error parsing referral code: {e}")
    
    # Create user in database (now initializes full new schema automatically)
    db.create_user(user_id, username, referred_by=referred_by)
    
    # If has referrer, validate and link
    if referred_by:
        link_result = validate_and_link_referral(user_id, referral_code)
        if link_result.get("success"):
            referrer = db.get_user(referred_by)
            
            # Notify referrer of new referral
            notify_msg = (
                f"👥 *New Referral!*\n\n"
                f"Your friend *{username}* just joined using your referral code!\n"
                f"💰 Earn ₹100 when they complete 25 tasks.\n\n"
                f"Current Referrals: {referrer.get('referrals', {}).get('referred_count', 0)}"
            )
            try:
                await context.bot.send_message(chat_id=referred_by, text=notify_msg, parse_mode="Markdown")
            except Exception as e:
                print(f"⚠️ Could not notify referrer: {e}")
    
    # Generate user's own referral code
    user_referral_code = generate_referral_code(user_id)
    
    # Welcome message
    welcome_msg = (
        f"👋 *Welcome to Surface Hub, {user.first_name}!*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🤑 *Earn Money Easily*\n"
        "Complete simple tasks and earn real cash!\n\n"
        
        "📋 *How it works:*\n"
        "1️⃣  **Deposit** ₹50 to activate your account\n"
        "2️⃣  **Complete Tasks** - Earn ₹10 per task\n"
        "3️⃣  **Reach 25 tasks** - Get ₹20 bonus!\n"
        "4️⃣  **Refer Friends** - Get ₹100 per friend (when they complete 25 tasks)\n"
        "5️⃣  **Withdraw** - Minimum ₹500 via UPI\n\n"
        
        "💡 *Your Referral Code:* `" + user_referral_code + "`\n"
        "Share with friends: `/start " + user_referral_code + "`\n\n"
        
        "🎁 *Special Offer:*\n"
        "New users get ₹20 bonus after first deposit!\n\n"
        
        "⚠️ *Next Step:* Tap the button below to deposit ₹50 and activate your account."
    )
    
    # Deposit button
    keyboard = [[InlineKeyboardButton("💳 Deposit ₹50 Now", callback_data="btn_deposit")]]
    
    await update.message.reply_text(
        welcome_msg,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # Log new user
    db.reference("admin_logs/new_users").push({
        "user_id": user_id,
        "username": username,
        "referred_by": referred_by,
        "referral_code": user_referral_code,
        "created_at": int(time.time())
    })


async def user_returning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Returning user welcome message.
    Shows current balance and quick action buttons.
    """
    user = update.effective_user
    if not user:
        return

    user_id = user.id

    user_data = db.get_user(user_id)
    if not user_data:
        return await welcome_new_user(update, context)

    balance = user_data.get("balance", 0)
    tasks_completed = user_data.get("earnings", {}).get("tasks_completed", 0)

    # Resilient referral retrieval (handles dict or legacy int)
    referrals_data = user_data.get("referrals", {})
    if isinstance(referrals_data, dict):
        referral_code = referrals_data.get("referral_code", "N/A")
    else:
        referral_code = "N/A"

    # Read live system config for feature flags
    try:
        cfg = db.get_system_config()
        watch_enabled = cfg.get("watch_enabled", True)
        website_url   = cfg.get("website_url", "https://chatting-app-ae637.web.app")
        watch_url     = cfg.get("watch_shortlink") or f"{website_url}/watch.html"
    except Exception:
        watch_enabled = True
        website_url   = "https://chatting-app-ae637.web.app"
        watch_url     = f"{website_url}/watch.html"

    welcome_back_msg = (
        f"👋 *Welcome Back, {user.first_name}!*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 *Your Balance:* ₹{balance}\n"
        f"📋 *Tasks Completed:* {tasks_completed}/25\n"
        f"🎯 *Referral Code:* `{referral_code}`\n\n"
        "What would you like to do?"
    )
    if watch_enabled:
        welcome_back_msg += f"\n\n📺 *New:* Watch videos & earn rewards → [Watch Now]({watch_url})"

    if update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_back_msg,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(watch_enabled, watch_url),
            disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            welcome_back_msg,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(watch_enabled, watch_url),
            disable_web_page_preview=True
        )


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main start handler - routes to new user, returning user, or reward claim.
    """
    if not update.effective_user:
        return
        
    user_id = update.effective_user.id
    
    # Check for reward token first: /start reward_TOKEN
    if context.args and len(context.args) > 0 and context.args[0].startswith("reward_"):
        token = context.args[0].replace("reward_", "")
        
        # Verify user exists first
        if not db.user_exists(user_id):
            await welcome_new_user(update, context)
            # Re-check for token logic after registration if needed, 
            # but usually registration message should come first.
            return

        # Verification logic
        verify_result = verify_and_claim_token(token)
        if verify_result.get("success"):
            # Ensure it's the same user
            if verify_result.get("user_id") != user_id:
                await update.message.reply_text("❌ This reward link is not for you.")
                return
            
            # Process reward
            reward_result = await process_task_completion(user_id, verify_result.get("task_id"), context.bot)
            if reward_result.get("success"):
                success_msg = (
                    "🎊 *HUB REWARD VERIFIED!*\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"✅ Task: `{verify_result.get('task_id')}`\n"
                    f"💰 Added: ₹{reward_result.get('added_amount', 10)}\n"
                    f"💳 New Balance: ₹{reward_result.get('new_balance')}\n\n"
                    "Keep exploring the Portal to earn more!"
                )
                await update.message.reply_text(success_msg, parse_mode="Markdown", reply_markup=main_menu_keyboard())
                return
            else:
                await update.message.reply_text(f"❌ Claim failed: {reward_result.get('message')}")
                return
        else:
            await update.message.reply_text(f"{verify_result.get('message')}")
            # fall through to show regular menu
    
    # Check if user exists
    if not db.user_exists(user_id):
        # New user - show welcome onboarding
        await welcome_new_user(update, context)
    else:
        # Returning user - show welcome back
        await user_returning(update, context)
