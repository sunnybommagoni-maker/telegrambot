import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import services.firebase as db
from config import DEPOSIT_AMOUNT, ADMIN_TELEGRAM_ID, ADMIN_NAME, UPI_ID
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
    
    # Check if already deposited
    if user and user.get("deposit_status"):
        await message_obj.reply_text(
            "✅ Your account is already *ACTIVATED*!\n"
            "Start earning now 💰",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # Generate UPI QR code
    try:
        qr_bytes = generate_upi_qr(UPI_ID, name="Surface Hub", amount=DEPOSIT_AMOUNT)
    except Exception as e:
        logger.error(f"❌ QR generation error: {e}")
        await message_obj.reply_text(
            "❌ Error generating QR code. Please try again.",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # Deposit message
    deposit_msg = (
        f"💎 *ACCOUNT ACTIVATION*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎁 *SPECIAL OFFER:*\n"
        f"Deposit: **₹{DEPOSIT_AMOUNT}**\n"
        f"Bonus: **₹20** (auto-credited!)\n"
        f"= **₹{DEPOSIT_AMOUNT + 20}** in your account\n\n"
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
    
    # Validate photo was sent
    if not update.message.photo:
        await update.message.reply_text("❌ Please send a *photo* screenshot.")
        return WAITING_SCREENSHOT
    
    # Get highest quality photo
    file_id = update.message.photo[-1].file_id
    
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
        admin_msg = (
            f"💳 *New Deposit Verification Required*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 User: @{username}\n"
            f"🆔 ID: `{user_id}`\n"
            f"💰 Amount: ₹{DEPOSIT_AMOUNT}\n"
            f"⏰ Time: {time.strftime('%H:%M:%S')}\n\n"
            f"📸 Screenshot below. Tap buttons to verify:"
        )
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"dep_approve_{user_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"dep_reject_{user_id}")
            ]
        ])
        
        await context.bot.send_photo(
            chat_id=ADMIN_TELEGRAM_ID,
            photo=file_id,
            caption=admin_msg,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
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
        
        # Add deposit amount to balance
        current_balance = user.get("balance", 0)
        new_balance = current_balance + DEPOSIT_AMOUNT + 20  # Include ₹20 bonus
        db.reference(f"users/{user_id}/balance").set(new_balance)
        
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
        
        # Update admin message
        await query.message.edit_caption(
            caption=query.message.caption + "\n\n✅ *APPROVED*",
            parse_mode="Markdown"
        )
        await query.message.edit_reply_markup(reply_markup=None)
        
        # Notify user
        try:
            username = user.get("username")
            notify_msg = (
                f"✅ *Account Activated!*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💰 Deposit Received: ₹{DEPOSIT_AMOUNT}\n"
                f"🎁 Welcome Bonus: ₹20\n"
                f"= Total Balance: ₹{new_balance}\n\n"
                f"🎉 Your account is now ACTIVE!\n"
                f"Start earning tasks, complete referrals, and withdraw anytime.\n\n"
                f"Let's earn! 💪"
            )
            
            await context.bot.send_message(
                chat_id=user_id,
                text=notify_msg,
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard()
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
        await query.message.edit_caption(
            caption=query.message.caption + "\n\n❌ *REJECTED*",
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
