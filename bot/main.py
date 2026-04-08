import logging
import time
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

from config import BOT_TOKEN
import services.firebase as db
from keep_alive import keep_alive
from utils.keyboards import main_menu_keyboard
from handlers.onboarding import handle_start
from handlers.deposit import start_deposit, handle_screenshot, cancel_deposit, approve_deposit, reject_deposit, WAITING_SCREENSHOT
from handlers.earn import earn_command
from handlers.withdraw import withdraw_command, handle_amount, handle_upi, approve_withdrawal, reject_withdrawal, cancel_withdraw, WAITING_AMOUNT, WAITING_UPI
from handlers.wallet_profile import wallet_command, profile_command

# ════════════════════════════════════════════════════════════════
# LOGGER CONFIGURATION
# ════════════════════════════════════════════════════════════════
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 🛡️ SECURITY: FLOOD CONTROL SYSTEM
USER_LAST_ACTION = {}
FLOOD_THRESHOLD = 1.0  # Seconds between actions per user

def is_flooding(user_id: int) -> bool:
    now = time.time()
    last = USER_LAST_ACTION.get(user_id, 0)
    if now - last < FLOOD_THRESHOLD:
        return True
    USER_LAST_ACTION[user_id] = now
    return False


# ════════════════════════════════════════════════════════════════
# START COMMAND - ONBOARDING
# ════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main start handler - routes to onboarding (new user) or menu (returning user).
    Handles referral code deep links: /start REF_CODE
    """
    user_id = update.effective_user.id
    
    # 🛡️ SECURITY: ANTI-FLOOD
    if is_flooding(user_id):
        return
    
    # Delegate to onboarding handler
    await handle_start(update, context)


# ════════════════════════════════════════════════════════════════
# CALLBACK HANDLER FOR BUTTON CLICKS
# ════════════════════════════════════════════════════════════════

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button clicks (btn_* pattern)"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data

    # 🛡️ SECURITY: ANTI-FLOOD & VALIDATION
    if is_flooding(user_id):
        return
    
    if not data or not isinstance(data, str):
        return logger.warning(f"Malformed callback from {user_id}")

    # Route button clicks to appropriate handlers
    button_routes = {
        "btn_earn": earn_command,
        "btn_deposit": start_deposit,
        "btn_wallet": wallet_command,
        "btn_profile": profile_command,
        "btn_withdraw": withdraw_command,
        "btn_start": start,
    }

    handler = button_routes.get(data)
    if handler:
        await handler(update, context)
    else:
        # Unknown button, return to menu
        await query.message.reply_text(
            "Unknown command. Tap a button below:",
            reply_markup=main_menu_keyboard()
        )


# ════════════════════════════════════════════════════════════════
# BOT SETUP
# ════════════════════════════════════════════════════════════════

async def post_init(application: Application):
    """Set bot menu commands"""
    commands = [
        BotCommand("start", "🚀 Main Menu"),
        BotCommand("earn", "💰 Earn Money"),
        BotCommand("deposit", "💳 Deposit"),
        BotCommand("wallet", "💎 Check Wallet"),
        BotCommand("profile", "👤 My Profile"),
        BotCommand("withdraw", "💸 Withdraw"),
    ]
    await application.bot.set_my_commands(commands)


def main():
    """Main execution loop"""
    # Start Keep-Alive
    keep_alive()

    # Create Bot Application
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # 1. DEPOSIT CONVERSATION HANDLER (Must be added first)
    deposit_conv = ConversationHandler(
        entry_points=[
            CommandHandler("deposit", start_deposit),
            CallbackQueryHandler(start_deposit, pattern="^btn_deposit$")
        ],
        states={
            WAITING_SCREENSHOT: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, handle_screenshot),
                CommandHandler("cancel", cancel_deposit)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_deposit)],
        per_chat=True
    )
    app.add_handler(deposit_conv)

    # 2. ADMIN APPROVAL/REJECTION HANDLERS
    app.add_handler(CallbackQueryHandler(approve_deposit, pattern="^dep_approve_"))
    app.add_handler(CallbackQueryHandler(reject_deposit, pattern="^dep_reject_"))

    # 3. EARN COMMAND HANDLERS (Web flow only)

    # 4. WITHDRAW CONVERSATION HANDLER (Must be before button handler)
    withdraw_conv = ConversationHandler(
        entry_points=[
            CommandHandler("withdraw", withdraw_command),
            CallbackQueryHandler(withdraw_command, pattern="^btn_withdraw$")
        ],
        states={
            WAITING_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount),
                CommandHandler("cancel", cancel_withdraw)
            ],
            WAITING_UPI: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_upi),
                CommandHandler("cancel", cancel_withdraw)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_withdraw)],
        per_chat=True
    )
    app.add_handler(withdraw_conv)

    # 5. WITHDRAWAL ADMIN HANDLERS
    app.add_handler(CallbackQueryHandler(approve_withdrawal, pattern="^with_approve_"))
    app.add_handler(CallbackQueryHandler(reject_withdrawal, pattern="^with_reject_"))

    # 6. MAIN COMMAND HANDLERS
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("earn", earn_command))
    app.add_handler(CommandHandler("wallet", wallet_command))
    app.add_handler(CommandHandler("profile", profile_command))

    # 7. BUTTON CALLBACK HANDLER (for inline buttons)
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^btn_"))

    # Start Polling
    logger.info("✅ Surface Hub Bot is ONLINE (Phase 8 Complete - Withdraw System Ready)")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    import sys
    if "--help" in sys.argv:
        print("Usage: python bot/main.py")
        print("Note: This bot should be run without arguments to start the production service.")
    else:
        main()
