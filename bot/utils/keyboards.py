from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


def main_menu_keyboard():
    """Main menu with 5 core commands: Earn, Deposit, Wallet, Profile, Withdraw"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Earn", callback_data="btn_earn"), InlineKeyboardButton("💳 Deposit", callback_data="btn_deposit")],
        [InlineKeyboardButton("💎 Wallet", callback_data="btn_wallet"), InlineKeyboardButton("👤 Profile", callback_data="btn_profile")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="btn_withdraw")],
    ])


def deposit_keyboard():
    """Deposit flow keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 Send Payment Screenshot", callback_data="btn_deposit_screenshot")],
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="btn_start")]
    ])


def admin_deposit_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Admin approval keyboard for deposits"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"dep_approve_{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"dep_reject_{user_id}")
        ]
    ])


def admin_withdraw_keyboard(user_id: int, withdraw_id: str) -> InlineKeyboardMarkup:
    """Admin approval keyboard for withdrawals"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"with_approve_{user_id}_{withdraw_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"with_reject_{user_id}_{withdraw_id}")
        ]
    ])
