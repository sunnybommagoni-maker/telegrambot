import logging
import time
import asyncio
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

from config import BOT_TOKEN, ADMIN_IDS
import telegram
import services.firebase as db
from keep_alive import keep_alive
from utils.keyboards import main_menu_keyboard
from handlers.onboarding import handle_start
from handlers.deposit import start_deposit, handle_screenshot, cancel_deposit, approve_deposit, reject_deposit, WAITING_SCREENSHOT
from handlers.earn import earn_command
from handlers.withdraw import withdraw_command, handle_amount, handle_upi, approve_withdrawal, reject_withdrawal, cancel_withdraw, WAITING_AMOUNT, WAITING_UPI
from handlers.wallet_profile import wallet_command, profile_command
from handlers.referral import refer_command
from services.news_agent import autonomous_news_job

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
# MAINTENANCE MODE CHECK
# ════════════════════════════════════════════════════════════════

async def check_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Returns True if bot is in maintenance mode (caller should halt).
    Sends maintenance message to user if so.
    Admin users bypass maintenance mode.
    """
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id:
        return False

    # Admins bypass maintenance mode
    if user_id in ADMIN_IDS:
        return False

    try:
        cfg = db.get_system_config()
        if cfg.get("maintenance_mode"):
            msg = cfg.get("maintenance_message") or "🔧 Bot is under maintenance. Please try again later."
            if update.message:
                await update.message.reply_text(msg)
            elif update.callback_query:
                await update.callback_query.answer(msg[:200], show_alert=True)
            return True
    except Exception as e:
        logger.warning(f"Could not check maintenance mode: {e}")
    return False


# ════════════════════════════════════════════════════════════════
# START COMMAND - ONBOARDING
# ════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main start handler - routes to onboarding or menu."""
    user_id = update.effective_user.id

    if is_flooding(user_id):
        return

    if await check_maintenance(update, context):
        return

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

    if is_flooding(user_id):
        return

    if not data or not isinstance(data, str):
        return logger.warning(f"Malformed callback from {user_id}")

    # Maintenance check (bypass earn/deposit/withdraw)
    if await check_maintenance(update, context):
        return

    # Route button clicks to appropriate handlers
    button_routes = {
        "btn_earn":     earn_command,
        "btn_deposit":  start_deposit,
        "btn_wallet":   wallet_command,
        "btn_profile":  profile_command,
        "btn_withdraw": withdraw_command,
        "btn_refer":    refer_command,
        "btn_start":    start,
    }

    handler = button_routes.get(data)
    if handler:
        await handler(update, context)
    else:
        await query.message.reply_text(
            "Unknown command. Tap a button below:",
            reply_markup=main_menu_keyboard()
        )


# ════════════════════════════════════════════════════════════════
# BROADCAST PROCESSOR JOB (runs every 2 minutes)
# ════════════════════════════════════════════════════════════════

async def process_broadcasts(context: ContextTypes.DEFAULT_TYPE):
    """
    Job: Picks up pending broadcast messages from Firebase queue
    (queued by admin panel) and sends them to all users.
    """
    try:
        pending = db.get_broadcast_queue_pending()
        if not pending:
            return

        user_ids = db.get_all_user_ids()
        logger.info(f"📢 Broadcasting {len(pending)} messages to {len(user_ids)} users")

        for bc_id, bc_data in pending.items():
            message = bc_data.get("message", "")
            image   = bc_data.get("image")
            link    = bc_data.get("link")
            label   = bc_data.get("link_label", "Open Link")

            if not message:
                db.mark_broadcast_sent(bc_id)
                continue

            # Build inline keyboard if link provided
            keyboard = None
            if link:
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(label, url=link)]])

            sent_count, failed_count = 0, 0

            for uid in user_ids:
                try:
                    if image:
                        await context.bot.send_photo(
                            chat_id=uid, photo=image,
                            caption=f"📢 *Surface Hub Update*\n\n{message}",
                            parse_mode="Markdown", reply_markup=keyboard
                        )
                    else:
                        await context.bot.send_message(
                            chat_id=uid,
                            text=f"📢 *Surface Hub Update*\n\n{message}",
                            parse_mode="Markdown", reply_markup=keyboard
                        )
                    sent_count += 1
                    await asyncio.sleep(0.05)  # Telegram rate limit: ~20 msg/sec
                except Exception as e:
                    failed_count += 1
                    logger.debug(f"Could not send broadcast to {uid}: {e}")

            db.mark_broadcast_sent(bc_id)
            logger.info(f"✅ Broadcast {bc_id} complete: {sent_count} sent, {failed_count} failed")

    except Exception as e:
        logger.error(f"❌ Broadcast processor error: {e}")


# ════════════════════════════════════════════════════════════════
# BOT SETUP
# ════════════════════════════════════════════════════════════════

async def post_init(application: Application):
    """Set bot menu commands"""
    commands = [
        BotCommand("start",    "🚀 Main Menu"),
        BotCommand("earn",     "💰 Earn Money"),
        BotCommand("refer",    "👥 Refer & Earn"),
        BotCommand("deposit",  "💳 Deposit"),
        BotCommand("wallet",   "💎 Check Wallet"),
        BotCommand("profile",  "👤 My Profile"),
        BotCommand("withdraw", "💸 Withdraw"),
    ]
    await application.bot.set_my_commands(commands)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error."""
    if isinstance(context.error, telegram.error.Conflict):
        logger.warning("⚠️ Conflict detected (Ghost bot instance). Update ignored.")
        return
    logger.error("Exception while handling an update:", exc_info=context.error)


def main():
    """Main execution loop"""
    keep_alive()

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_error_handler(error_handler)

    # 🔗 JOB QUEUE
    if app.job_queue:
        app.job_queue.run_repeating(autonomous_news_job, interval=10800, first=5)
        app.job_queue.run_repeating(process_broadcasts, interval=120, first=30)  # Every 2 min
        logger.info("🕒 AI News Agent + Broadcast Processor scheduled.")

    # 1. DEPOSIT CONVERSATION
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

    # 2. ADMIN DEPOSIT APPROVAL
    app.add_handler(CallbackQueryHandler(approve_deposit, pattern="^dep_approve_"))
    app.add_handler(CallbackQueryHandler(reject_deposit,  pattern="^dep_reject_"))

    # 3. WITHDRAW CONVERSATION
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

    # 4. ADMIN WITHDRAWAL APPROVAL
    app.add_handler(CallbackQueryHandler(approve_withdrawal, pattern="^with_approve_"))
    app.add_handler(CallbackQueryHandler(reject_withdrawal, pattern="^with_reject_"))

    # 5. MAIN COMMANDS
    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("earn",    earn_command))
    app.add_handler(CommandHandler("refer",   refer_command))
    app.add_handler(CommandHandler("wallet",  wallet_command))
    app.add_handler(CommandHandler("profile", profile_command))

    # 6. BUTTON CALLBACKS
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^btn_"))

    logger.info("✅ Surface Hub Bot v3.0 ONLINE — Admin Panel + Watch Feature + Broadcast Processor READY")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    import sys
    if "--help" in sys.argv:
        print("Usage: python bot/main.py")
    else:
        main()
