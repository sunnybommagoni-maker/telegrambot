import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import services.firebase as db
from config import DEPOSIT_AMOUNT, ADMIN_IDS, ADMIN_NAME, UPI_ID
from utils.qr import generate_upi_qr
from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)

# ConversationHandler state
WAITING_SCREENSHOT = 1


async def start_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Initialize deposit flow - show UPI QR code.
    Triggered by: /deposit command or btn_deposit callback
    """
    # Handle both message and callback query
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message_obj = query.message
    else:
        message_obj = update.message
    
    user_id = update.effective_user.id
    user = db.get_user(user_id)

    # Read live config from Firebase (admin-controlled)
    cfg = db.get_system_config()
    if not cfg.get('deposits_open', True):
        await message_obj.reply_text(
            "💳 *Deposits are currently closed.*\n"
            "Please try again later or contact support.",
            parse_mode="Markdown", reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END

    deposit_amt = cfg.get('deposit_amount', DEPOSIT_AMOUNT)
    upi_id      = cfg.get('upi_id', UPI_ID)
    upi_name    = cfg.get('upi_name', 'Surface Hub')
    welcome_bonus = cfg.get('welcome_bonus', 20)
    watch_enabled = cfg.get('watch_enabled', True)

    # Check if already deposited
    if user and user.get("deposit_status"):
        await message_obj.reply_text(
            "✅ Your account is already *ACTIVATED*!\n"
            "Start earning now 💰",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(watch_enabled)
        )
        return ConversationHandler.END

    # Generate UPI QR code
    try:
        qr_bytes = generate_upi_qr(upi_id, name=upi_name, amount=deposit_amt)
    except Exception as e:
        logger.error(f"❌ QR generation error: {e}")
        await message_obj.reply_text(
            "❌ Error generating QR code. Please try again.",
            reply_markup=main_menu_keyboard(watch_enabled)
        )
        return ConversationHandler.END

    # Deposit message
    deposit_msg = (
        f"💎 *ACCOUNT ACTIVATION*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎁 *SPECIAL OFFER:*\n"
        f"Deposit: **₹{deposit_amt}**\n"
        f"Bonus: **₹{welcome_bonus}** (auto-credited!)\n"
        f"= **₹{deposit_amt + welcome_bonus}** in your account\n\n"
        f"📱 *How to Pay:*\n"
        f"1️⃣  Scan the QR code below\n"
        f"2️⃣  Complete the payment\n"
        f"3️⃣  Take a screenshot of success\n"
        f"4️⃣  Send screenshot here\n\n"
        f"⏱️  *Admin Verification:*\n"
        f"Payment verified within 10-30 minutes\n"
        f"Your account activates instantly ✅"
    )

    # Send QR code
    await message_obj.reply_photo(
        photo=qr_bytes,
        caption=deposit_msg,
        parse_mode="Markdown"
    )

    # Prompt for screenshot
    await message_obj.reply_text(
        "📸 Please send your payment screenshot here:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="btn_start")]
        ])
    )
    
    return WAITING_SCREENSHOT


async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle screenshot upload and create admin approval request
    """
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    username = user.get("username") if user else update.effective_user.first_name
    
    # Extract file_id and type
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        send_method = context.bot.send_photo
    elif update.message.document:
        file_id = update.message.document.file_id
        send_method = context.bot.send_document
    else:
        await update.message.reply_text("❌ Please send a *screenshot* as a photo or file.")
        return WAITING_SCREENSHOT
    
    # Save deposit request to Firebase
    try:
        db.reference(f"deposits/{user_id}").set({
            "user_id": user_id,
            "username": username,
            "amount": DEPOSIT_AMOUNT,
            "screenshot_id": file_id,
            "status": "pending",
            "created_at": int(time.time()),
            "approved_at": None,
            "rejected_at": None,
            "admin_note": ""
        })
    except Exception as e:
        logger.error(f"❌ Error saving deposit: {e}")
        await update.message.reply_text(
            "❌ Error processing deposit. Please try again."
        )
        return ConversationHandler.END
    
    # Confirm to user
    await update.message.reply_text(
        "✅ *Screenshot Received!*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Your deposit is under review by admin.\n"
        "You'll receive notification when activated ⏱️\n\n"
        "(Usually verified within 10-30 minutes)",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    
    # Notify admin
    try:
        # Escape username for Markdown
        safe_username = username.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`") if username else "Unknown"
        
        admin_msg = (
            f"💳 *New Deposit Verification Required*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 User: @{safe_username}\n"
            f"🆔 ID: `{user_id}`\n"
            f"💰 Amount: ₹{DEPOSIT_AMOUNT}\n"
            f"⏰ Time: {time.strftime('%H:%M:%S')}\n\n"
            f"📸 Screenshot above. Tap buttons to verify:"
        )
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"dep_approve_{user_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"dep_reject_{user_id}")
            ]
        ])
        
        for admin_id in ADMIN_IDS:
            try:
                # Use detected send method (photo or document)
                await send_method(
                    chat_id=admin_id,
                    **{"photo" if update.message.photo else "document": file_id},
                    caption=admin_msg,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
        
        logger.info(f"✓ Admin notified for deposit from {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Error notifying admin: {e}")
    
    return ConversationHandler.END


async def approve_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin approves deposit - activates account and adds bonus
    Callback: dep_approve_{user_id}
    """
    query = update.callback_query
    await query.answer()

    if update.effective_user.id not in ADMIN_IDS:
        await query.message.reply_text("❌ Unauthorized access.")
        return
    
    # Extract user_id from callback data
    try:
        user_id = int(query.data.split("_")[-1])
    except (ValueError, IndexError):
        await query.message.reply_text("❌ Invalid deposit ID")
        return
    
    user = db.get_user(user_id)
    if not user:
        await query.message.reply_text(f"❌ User {user_id} not found")
        return
    
    # Check if already approved
    if user.get("deposit_status"):
        await query.message.reply_text(f"✓ Deposit already approved for {user.get('username')}")
        return
    
    # Approve deposit
    try:
        # Mark deposit as approved
        db.reference(f"deposits/{user_id}").update({
            "status": "approved",
            "approved_at": int(time.time()),
            "admin_note": f"Approved by {ADMIN_NAME}"
        })
        
        # Activate user account
        db.reference(f"users/{user_id}/deposit_status").set(True)
        
        # Add deposit amount + bonus to balance using atomic operator
        # Benefit: Safe even if balance was changed simultaneously
        bonus = 20
        new_balance = db.update_balance(user_id, DEPOSIT_AMOUNT + bonus)
        
        # Log approval
        db.reference("admin_logs/deposit_approvals").push({
            "user_id": user_id,
            "username": user.get("username"),
            "amount": DEPOSIT_AMOUNT,
            "bonus": 20,
            "final_balance": new_balance,
            "approved_by": ADMIN_NAME,
            "timestamp": int(time.time())
        })
        
        # Update admin message safely
        try:
            current_caption = query.message.caption or "📸 Deposit Verification Request"
            # Add status without re-parsing original markdown if possible, or use HTML
            await query.message.edit_caption(
                caption=current_caption + "\n\n✅ APPROVED",
                # Omit parse_mode to keep original style or prevent re-parse errors
            )
            await query.message.edit_reply_markup(reply_markup=None)
        except Exception as e:
            logger.error(f"⚠️ Could not update admin message UI: {e}")
        
        # Notify user
        try:
            cfg = db.get_system_config()
            watch_enabled = cfg.get("watch_enabled", True)
            website_url   = cfg.get("website_url", "https://chatting-app-ae637.web.app")
            watch_url     = cfg.get("watch_shortlink") or f"{website_url}/watch.html"

            notify_msg = (
                f"✅ <b>Account Activated!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💰 Deposit Received: ₹{DEPOSIT_AMOUNT}\n"
                f"🎁 Welcome Bonus: ₹20\n"
                f"= Total Balance: <b>₹{new_balance}</b>\n\n"
                f"🎉 Your account is now ACTIVE!\n"
                f"Start earning tasks, complete referrals, and withdraw anytime.\n\n"
                f"Let's earn! 💪"
            )
            
            await context.bot.send_message(
                chat_id=user_id,
                text=notify_msg,
                parse_mode="HTML",
                reply_markup=main_menu_keyboard(watch_enabled, watch_url)
            )
        except Exception as e:
            logger.error(f"❌ Could not notify user: {e}")
        
        logger.info(f"✅ Deposit approved for {user_id} by {ADMIN_NAME}")
        
    except Exception as e:
        logger.error(f"❌ Error approving deposit: {e}")
        await query.message.reply_text(f"❌ Error: {str(e)}")


async def reject_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin rejects deposit - keeps balance unchanged, allows retry
    Callback: dep_reject_{user_id}
    """
    query = update.callback_query
    await query.answer()

    if update.effective_user.id not in ADMIN_IDS:
        await query.message.reply_text("❌ Unauthorized access.")
        return
    
    # Extract user_id from callback data
    try:
        user_id = int(query.data.split("_")[-1])
    except (ValueError, IndexError):
        await query.message.reply_text("❌ Invalid deposit ID")
        return
    
    user = db.get_user(user_id)
    if not user:
        await query.message.reply_text(f"❌ User {user_id} not found")
        return
    
    # Reject deposit
    try:
        db.reference(f"deposits/{user_id}").update({
            "status": "rejected",
            "rejected_at": int(time.time()),
            "admin_note": f"Rejected by {ADMIN_NAME}"
        })
        
        # Log rejection
        db.reference("admin_logs/deposit_rejections").push({
            "user_id": user_id,
            "username": user.get("username"),
            "amount": DEPOSIT_AMOUNT,
            "rejected_by": ADMIN_NAME,
            "timestamp": int(time.time())
        })
        
        # Update admin message
        current_caption = query.message.caption or "📸 Deposit Verification Request"
        await query.message.edit_caption(
            caption=current_caption + "\n\n❌ *REJECTED*",
            parse_mode="Markdown"
        )
        await query.message.edit_reply_markup(reply_markup=None)
        
        # Notify user to retry
        try:
            username = user.get("username")
            notify_msg = (
                f"❌ *Deposit Not Verified*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Your payment screenshot couldn't be verified.\n\n"
                f"📸 Common reasons:\n"
                f"• Screenshot unclear or incomplete\n"
                f"• Payment not from correct UPI ID\n"
                f"• Amount doesn't match ₹{DEPOSIT_AMOUNT}\n\n"
                f"🔄 Please try again with a clear screenshot.\n"
                f"Use the button below to retry:"
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Retry Deposit", callback_data="btn_deposit")]
            ])
            
            await context.bot.send_message(
                chat_id=user_id,
                text=notify_msg,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"❌ Could not notify user: {e}")
        
        logger.info(f"❌ Deposit rejected for {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Error rejecting deposit: {e}")
        await query.message.reply_text(f"❌ Error: {str(e)}")


async def cancel_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel deposit flow"""
    await update.message.reply_text(
        "❌ Deposit cancelled. Try again anytime!",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END
