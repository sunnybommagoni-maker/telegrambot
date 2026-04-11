"""
Bot keyboards — v3.0
Updated: Added Watch button + dynamic config-aware menus
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard(watch_enabled: bool = True):
    """
    Main menu with 6 core commands: Earn, Deposit, Wallet, Profile, Withdraw, Watch
    watch_enabled: read from system_config in Firebase — controlled via Admin Panel
    """
    rows = [
        [
            InlineKeyboardButton("💰 Earn", callback_data="btn_earn"),
            InlineKeyboardButton("💳 Deposit", callback_data="btn_deposit"),
        ],
        [
            InlineKeyboardButton("💎 Wallet", callback_data="btn_wallet"),
            InlineKeyboardButton("👤 Profile", callback_data="btn_profile"),
        ],
        [
            InlineKeyboardButton("💸 Withdraw", callback_data="btn_withdraw"),
        ],
    ]
    if watch_enabled:
        rows.append([
            InlineKeyboardButton("📺 Watch & Earn", url="https://chatting-app-ae637.web.app/watch.html"),
        ])
    return InlineKeyboardMarkup(rows)


def deposit_keyboard():
    """Deposit flow keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 Send Payment Screenshot", callback_data="btn_deposit_screenshot")],
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="btn_start")],
    ])


def admin_deposit_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Admin approval keyboard for deposits"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"dep_approve_{user_id}"),
            InlineKeyboardButton("❌ Reject",  callback_data=f"dep_reject_{user_id}"),
        ]
    ])


def admin_withdraw_keyboard(user_id: int, withdraw_id: str) -> InlineKeyboardMarkup:
    """Admin approval keyboard for withdrawals"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"with_approve_{user_id}_{withdraw_id}"),
            InlineKeyboardButton("❌ Reject",  callback_data=f"with_reject_{user_id}_{withdraw_id}"),
        ]
    ])
