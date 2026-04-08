from datetime import datetime
from config import DEPOSIT_AMOUNT, MIN_WITHDRAW, REWARD_WATCH, REWARD_TASK, REWARD_REFERRAL


def format_profile(user: dict) -> str:
    join_ts = user.get("join_date", 0)
    join_date = datetime.fromtimestamp(join_ts).strftime("%d %b %Y") if join_ts else "Unknown"
    deposit_status = "✅ Approved" if user.get("deposit_status") else "⏳ Pending / Not Deposited"
    return (
        f"👤 *Your Profile*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 User ID: `{user.get('user_id')}`\n"
        f"👤 Username: @{user.get('username', 'N/A')}\n"
        f"💰 Balance: ₹{user.get('balance', 0):.2f}\n"
        f"👁 Ads Watched: {user.get('ads_watched', 0)}\n"
        f"📋 Tasks Done: {user.get('tasks_done', 0)}\n"
        f"🎯 Offers Done: {user.get('offers_done', 0)}\n"
        f"👥 Referrals: {user.get('referrals', 0)}\n"
        f"💳 Deposit Status: {deposit_status}\n"
        f"📅 Joined: {join_date}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )


def format_balance(user: dict) -> str:
    return (
        f"💰 *Wallet Balance*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Available: ₹*{user.get('balance', 0):.2f}*\n"
        f"Min withdraw: ₹{MIN_WITHDRAW}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )


def format_help() -> str:
    return (
        "❓ *Help & Info*\n\n"
        "*How to earn:*\n"
        "1. /deposit - Add ₹100 to unlock premium tasks.\n"
        "2. /watch - Watch 10s ads for quick cash.\n"
        "3. /tasks - Complete website signups & actions.\n"
        "4. /offers - Install apps for high rewards.\n"
        "5. /blogs - Read short blogs and earn ₹5.\n"
        "6. /videos - Watch videos and earn ₹10.\n"
        "7. /refer - Share your link and earn ₹50 per friend!\n\n"
        "*Commands:*\n"
        "/start - Main Menu\n"
        "/profile - Your Stats\n"
        "/balance - Wallet\n"
        "/withdraw - Cash out\n\n"
        "*Earning Rates*\n"
        f"👁 Watch Ad: ₹{REWARD_WATCH}\n"
        f"📋 Task: ₹{REWARD_TASK}\n"
        f"👥 Referral: ₹{REWARD_REFERRAL} (on first deposit)\n"
        "🎯 App Install: ₹30\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 Deposit ₹{DEPOSIT_AMOUNT} once to unlock all tasks & offers!"
    )


def format_stats(stats: dict) -> str:
    return (
        "📊 *Platform Statistics*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Users: {stats['total_users']}\n"
        f"💳 Deposited Users: {stats['deposited_users']}\n"
        f"💰 Total Balance in System: ₹{stats['total_balance_in_system']}\n"
        f"👁 Total Ads Watched: {stats['total_ads_watched']}\n"
        f"📋 Total Tasks Done: {stats['total_tasks_done']}\n"
        f"💸 Total Withdrawn: ₹{stats['total_withdrawn']}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
