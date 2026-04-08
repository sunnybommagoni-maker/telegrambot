"""
Withdraw Handler - Phase 8
Collect UPI, validate, and create admin approval requests
"""
import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import services.firebase as db
from config import MINIMUM_WITHDRAW_AMOUNT, ADMIN_IDS, ADMIN_NAME
from utils.firebase_transactions import create_withdrawal_request, approve_withdrawal_request, reject_withdrawal_request
from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)

# ConversationHandler states
WAITING_AMOUNT = 1
WAITING_UPI = 2


async def withdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start withdrawal flow - ask for amount"""
    user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
    user = db.get_user(user_id)
    
    # Check minimum deposit
    if not user or not user.get("deposit_status"):
        msg = "❌ Please deposit ₹50 first"
        if update.message:
            await update.message.reply_text(msg, reply_markup=main_menu_keyboard())
        else:
            await update.callback_query.message.reply_text(msg, reply_markup=main_menu_keyboard())
        return ConversationHandler.END
    
    balance = user.get("balance", 0)
    
    withdraw_msg = (
        f"💸 *WITHDRAW EARNINGS*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        
        f"💰 Your Balance: ₹{balance}\n"
        f"⚠️  Minimum: ₹{MINIMUM_WITHDRAW_AMOUNT}\n\n"
        
        f"How much would you like to withdraw?\n"
        f"(Send amount in rupees, e.g., 500)\n\n"
        
        f"⏱️  Processing: 24-48 hours"
    )
    
    if update.message:
        await update.message.reply_text(withdraw_msg, parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text(withdraw_msg, parse_mode="Markdown")
    
    return WAITING_AMOUNT


async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle withdrawal amount input"""
    try:
        amount = float(update.message.text)
        
        if amount < MINIMUM_WITHDRAW_AMOUNT:
            await update.message.reply_text(
                f"❌ Minimum withdrawal: ₹{MINIMUM_WITHDRAW_AMOUNT}"
            )
            return WAITING_AMOUNT
        
        # Store amount in context
        context.user_data["withdraw_amount"] = amount
        
        # Ask for UPI
        upi_msg = (
            f"💳 *Enter Your UPI ID*\n\n"
            f"Amount: ₹{amount}\n\n"
            f"Example formats: user@upi, user@okhdfcbank, user@paytm"
        )
        await update.message.reply_text(upi_msg, parse_mode="Markdown")
        
        return WAITING_UPI
    
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid amount (e.g., 500)")
        return WAITING_AMOUNT


async def handle_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process UPI and create withdrawal request"""
    user_id = update.effective_user.id
    upi = update.message.text.strip()
    amount = context.user_data.get("withdraw_amount", 0)
    
    # Create withdrawal request
    result = create_withdrawal_request(user_id, amount, upi)
    
    if result.get("success"):
        success_msg = (
            f"✅ *Withdrawal Request Created*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💸 Amount: ₹{amount}\n"
            f"💳 UPI: {upi}\n"
            f"⏱️  Expected: 24-48 hours\n\n"
            f"Admin will verify and process your withdrawal soon!"
        )
        
        await update.message.reply_text(success_msg, parse_mode="Markdown", reply_markup=main_menu_keyboard())
        
        # Notify admin
        try:
            admin_msg = (
                f"💸 *New Withdrawal Request*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👤 User: @{db.get_user(user_id).get('username')}\n"
                f"🆔 ID: `{user_id}`\n"
                f"💰 Amount: ₹{amount}\n"
                f"💳 UPI: {upi}\n⏱️  Time: {time.strftime('%H:%M:%S')}\n\n"
                f"Status: Pending approval"
            )
            
            request_id = result.get("request_id")
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"with_approve_{request_id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"with_reject_{request_id}")
                ]
            ])
            
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=admin_msg,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
        except Exception as e:
            logger.error(f"❌ Error notifying admin: {e}")
    else:
        error_msg = f"❌ {result.get('message', 'Withdrawal failed')}"
        await update.message.reply_text(error_msg, reply_markup=main_menu_keyboard())
    
    return ConversationHandler.END


async def approve_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin approves withdrawal"""
    query = update.callback_query
    await query.answer()

    if update.effective_user.id not in ADMIN_IDS:
        await query.message.reply_text("❌ Unauthorized access.")
        return
    
    try:
        # data format: with_approve_REQUESTID
        request_id = query.data.split("_")[-1]
    except (ValueError, IndexError):
        await query.message.reply_text("❌ Invalid withdrawal ID")
        return
    
    # Get request to find user_id
    request = db.reference(f"withdrawal_requests/{request_id}").get()
    if not request:
        await query.message.reply_text("❌ Withdrawal request not found")
        return
    
    user_id = request.get("user_id")
    
    # Approve
    result = approve_withdrawal_request(request_id, f"Approved by {ADMIN_NAME}")
    
    if result.get("success"):
        # Update admin message
        current_text = query.message.text or "💳 Withdrawal Request"
        await query.message.edit_text(
            text=current_text + "\n\n✅ *APPROVED*",
            parse_mode="Markdown"
        )
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Withdrawal Approved!\n\nYour withdrawal has been approved and will be processed within 24-48 hours.",
                reply_markup=main_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Could not notify user: {e}")


async def reject_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin rejects withdrawal"""
    query = update.callback_query
    await query.answer()
    
    try:
        # data format: with_reject_REQUESTID
        request_id = query.data.split("_")[-1]
    except (ValueError, IndexError):
        await query.message.reply_text("❌ Invalid withdrawal ID")
        return
    
    # Get request to find user_id
    request = db.reference(f"withdrawal_requests/{request_id}").get()
    if not request:
        await query.message.reply_text("❌ Withdrawal request not found")
        return
    
    user_id = request.get("user_id")
    
    # Refund balance
    result = reject_withdrawal_request(request_id, "Rejected by admin")
    
    if result.get("success"):
        # Update admin message
        current_text = query.message.text or "💳 Withdrawal Request"
        await query.message.edit_text(
            text=current_text + "\n\n❌ *REJECTED*",
            parse_mode="Markdown"
        )
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Withdrawal Rejected\n\nYour balance has been refunded. Please check and try again.",
                reply_markup=main_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Could not notify user: {e}")


async def cancel_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel withdrawal"""
    await update.message.reply_text("❌ Withdrawal cancelled.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END
