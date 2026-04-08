from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from services import firebase as db
from utils.keyboards import main_menu_keyboard
from utils.messages import format_profile, format_balance, format_help
from config import ADMIN_IDS, REWARD_REFERRAL


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or str(user_id)

    # Parse referral code from /start payload
    referred_by = None
    if context.args:
        try:
            ref_id = int(context.args[0])
            if ref_id != user_id and db.user_exists(ref_id):
                referred_by = ref_id
        except (ValueError, TypeError):
            pass

    if not db.user_exists(user_id):
        # NEW USER: Give ₹20 Welcome Bonus instantly!
        INITIAL_WELCOME_BONUS = 20
        db.create_user(user_id, username, referred_by, initial_balance=INITIAL_WELCOME_BONUS)
        
        welcome = (
            f"👋 *WELCOME TO SURFACE HUB, {user.first_name}!*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "The world's highest paying earning platform is now at your fingertips! 🚀\n\n"
            "🎁 *Joining Bonus:* **₹20.00** credited instantly!\n\n"
            "💎 *Premium Earning Potential:*\n"
            "▪️ Watch Ads: **₹10.00** per view!\n"
            "▪️ High Payout Tasks: **₹25.00+** each!\n"
            "▪️ Refers: **₹100.00** per friend!\n\n"
            "⚠️ *Activation Required:*\n"
            "To prevent bot spam and unlock these high-paying payouts, a one-time **₹50 activation deposit** is required.\n\n"
            "🔥 **MEGA OFFER:** Deposit ₹50 today and get a **₹100.00 Total Value** account (₹50 deposit + ₹50 Bonus)!"
        )
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = [[InlineKeyboardButton("💎 Activate Account (₹50)", callback_data="btn_deposit")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        user_data = db.get_user(user_id)
        is_activated = user_data.get("deposit_status", False)
        balance = user_data.get("balance", 0)
        
        if not is_activated:
            welcome = (
                f"🚀 *WELCOME BACK, {user.first_name}!*\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "⚠️ *Account Status: Inactive*\n\n"
                "You haven't activated your premium status yet. Deposit ₹50 to unlock ₹10/ad and ₹25/task payouts!\n\n"
                f"💰 *Current Balance:* ₹{balance:.2f}"
            )
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = [[InlineKeyboardButton("💎 Activate Now (₹50)", callback_data="btn_deposit")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            welcome = (
                f"🚀 *WELCOME BACK, {user.first_name}!* 💎\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "Your premium earning dashboard is active.\n\n"
                f"💰 *Balance:* ₹{balance:.2f}\n\n"
                "Use the menu below to maximize your daily income! 👇"
            )
            reply_markup = main_menu_keyboard()

    await update.message.reply_text(
        welcome,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
        user_id = query.from_user.id
    else:
        message = update.message
        user_id = update.effective_user.id

    user = db.get_user(user_id)
    if not user:
        await message.reply_text("Please use /start first.")
        return
    await message.reply_text(
        format_profile(user),
        parse_mode="Markdown",
    )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
        user_id = query.from_user.id
    else:
        message = update.message
        user_id = update.effective_user.id

    user = db.get_user(user_id)
    if not user:
        await message.reply_text("Please use /start first.")
        return
    await message.reply_text(
        format_balance(user),
        parse_mode="Markdown",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message
    await message.reply_text(
        format_help(),
        parse_mode="Markdown",
    )


async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
        user_id = query.from_user.id
    else:
        message = update.message
        user_id = update.effective_user.id

    bot = context.bot
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    link = f"https://t.me/{bot_username}?start={user_id}"
    user = db.get_user(user_id)
    referrals = user.get("referrals", 0) if user else 0

    await message.reply_text(
        f"👥 *MEGA REFERRAL PROGRAM* 💰\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Earn massive passive income by inviting friends!\n\n"
        f"🎁 Reward: **₹{REWARD_REFERRAL}.00** per friend!\n"
        f"*(Credited when your friend makes their first deposit)*\n\n"
        f"🔗 *Your Unique Link:*\n"
        f"`{link}`\n\n"
        f"📊 *Stats:*\n"
        f"▪️ Total Referrals: **{referrals}**\n"
        f"▪️ Potential Earnings: **₹{referrals * REWARD_REFERRAL}**",
        parse_mode="Markdown",
    )
