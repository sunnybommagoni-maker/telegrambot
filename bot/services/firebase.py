import firebase_admin
from firebase_admin import credentials, db
from config import FIREBASE_URL, FIREBASE_CREDENTIALS_PATH
import time
import os
import json

# ── Resolve serviceAccountKey.json path ────────────────────────
# This file is at: bot/services/firebase.py
# Project root is : bot/../.. = telegram bot/
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))

# ── Initialize ────────────────────────────────────────────────
# Priority 1: Environment Variable (Safe for Cloud/Hugging Face)
_ENV_CREDS = os.getenv("FIREBASE_SERVICE_ACCOUNT")

if _ENV_CREDS:
    try:
        # Load credentials from JSON string in environment variable
        cred_dict = json.loads(_ENV_CREDS)
        cred = credentials.Certificate(cred_dict)
        print("Firebase initialized via Environment Variable")
    except Exception as e:
        print(f"Error loading Firebase Environment Variable: {e}")
        # Fallback to file if env fails
        if not os.path.isabs(FIREBASE_CREDENTIALS_PATH):
            _CRED_PATH = os.path.join(_PROJECT_ROOT, FIREBASE_CREDENTIALS_PATH)
        else:
            _CRED_PATH = FIREBASE_CREDENTIALS_PATH
        cred = credentials.Certificate(_CRED_PATH)
else:
    # Priority 2: Local File (Standard for Dev)
    if not os.path.isabs(FIREBASE_CREDENTIALS_PATH):
        _CRED_PATH = os.path.join(_PROJECT_ROOT, FIREBASE_CREDENTIALS_PATH)
    else:
        _CRED_PATH = FIREBASE_CREDENTIALS_PATH
    
    if os.path.exists(_CRED_PATH):
        cred = credentials.Certificate(_CRED_PATH)
        print("Firebase initialized via Local File")
    else:
        print(f"Firebase credentials NOT FOUND at: {_CRED_PATH}")
        raise FileNotFoundError(f"Firebase credentials missing. Add FIREBASE_SERVICE_ACCOUNT secret or {_CRED_PATH} file.")

firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_URL})

# Export db.reference so other files can use db.reference() when importing this module
reference = db.reference

# ════════════════════════════════════════════════════════════════
#  USER FUNCTIONS
# ════════════════════════════════════════════════════════════════

def get_user(user_id: int) -> dict | None:
    return db.reference(f"users/{user_id}").get()

def user_exists(user_id: int) -> bool:
    return get_user(user_id) is not None

def create_user(user_id: int, username: str, referred_by: int | None = None, initial_balance: float = 0) -> dict:
    data = {
        "user_id": user_id,
        "username": username or f"user_{user_id}",
        "balance": initial_balance,
        "ads_watched": 0,
        "tasks_done": 0,
        "offers_done": 0,
        "deposit_status": False,
        "referrals": {
            "referral_code": None,
            "referred_count": 0,
            "referrals_list": {}
        },
        "referred_by": referred_by,
        "join_date": int(time.time()),
        "banned": False,
    }
    db.reference(f"users/{user_id}").set(data)
    return data

def update_user(user_id: int, data: dict):
    db.reference(f"users/{user_id}").update(data)

def update_balance(user_id: int, delta: float) -> float:
    """Atomically increment user balance and return new balance."""
    ref = db.reference(f"users/{user_id}/balance")
    current = ref.get() or 0
    new_balance = round(current + delta, 2)
    ref.set(new_balance)
    return new_balance

def get_all_users() -> dict:
    return db.reference("users").get() or {}

def get_all_user_ids() -> list[int]:
    users = get_all_users()
    return list(users.keys()) if users else []

# ════════════════════════════════════════════════════════════════
#  DEPOSIT FUNCTIONS
# ════════════════════════════════════════════════════════════════

def save_deposit(user_id: int, file_id: str):
    db.reference(f"deposits/{user_id}").set({
        "user_id": user_id,
        "screenshot": file_id,
        "status": "pending",
        "timestamp": int(time.time()),
    })

def get_deposit(user_id: int) -> dict | None:
    return db.reference(f"deposits/{user_id}").get()

def approve_deposit(user_id: int):
    from config import REWARD_REFERRAL
    
    db.reference(f"deposits/{user_id}").update({"status": "approved"})
    db.reference(f"users/{user_id}").update({"deposit_status": True})
    
    # Credit the Referrer if exists
    user = get_user(user_id)
    if user and user.get("referred_by"):
        credit_referral(user["referred_by"], REWARD_REFERRAL)

def reject_deposit(user_id: int):
    db.reference(f"deposits/{user_id}").update({"status": "rejected"})

def get_all_deposits() -> dict:
    return db.reference("deposits").get() or {}

# ════════════════════════════════════════════════════════════════
#  WITHDRAW FUNCTIONS
# ════════════════════════════════════════════════════════════════

def create_withdraw(user_id: int, amount: float, upi: str) -> str:
    ref = db.reference("withdraws").push({
        "user_id": user_id,
        "amount": amount,
        "upi": upi,
        "status": "pending",
        "timestamp": int(time.time()),
    })
    return ref.key

def get_withdraw(withdraw_id: str) -> dict | None:
    return db.reference(f"withdraws/{withdraw_id}").get()

def approve_withdraw(withdraw_id: str):
    db.reference(f"withdraws/{withdraw_id}").update({"status": "completed"})

def reject_withdraw(withdraw_id: str):
    db.reference(f"withdraws/{withdraw_id}").update({"status": "rejected"})

def get_pending_withdraws() -> dict:
    all_w = db.reference("withdraws").get() or {}
    return {k: v for k, v in all_w.items() if v.get("status") == "pending"}

def get_all_withdraws() -> dict:
    return db.reference("withdraws").get() or {}

# ════════════════════════════════════════════════════════════════
#  TASKS FUNCTIONS
# ════════════════════════════════════════════════════════════════

def get_tasks() -> dict:
    return db.reference("tasks").get() or {}

def add_task(link: str, reward: float, description: str = "") -> str:
    ref = db.reference("tasks").push({
        "link": link,
        "reward": reward,
        "description": description,
        "type": "task",
        "active": True,
        "created_at": int(time.time()),
    })
    return ref.key

def complete_task(user_id: int, task_id: str, reward: float):
    done = db.reference(f"users/{user_id}/tasks_done").get() or 0
    db.reference(f"users/{user_id}/tasks_done").set(done + 1)
    update_balance(user_id, reward)
    db.reference(f"user_tasks/{user_id}/{task_id}").set(True)

def has_done_task(user_id: int, task_id: str) -> bool:
    return db.reference(f"user_tasks/{user_id}/{task_id}").get() is not None

# ════════════════════════════════════════════════════════════════
#  ADS FUNCTIONS
# ════════════════════════════════════════════════════════════════

def get_ads() -> dict:
    return db.reference("ads").get() or {}

def add_ad(link: str, reward: float) -> str:
    ref = db.reference("ads").push({
        "link": link,
        "reward": reward,
        "type": "ad",
        "active": True,
        "created_at": int(time.time()),
    })
    return ref.key

def record_ad_watch(user_id: int, reward: float):
    watched = db.reference(f"users/{user_id}/ads_watched").get() or 0
    db.reference(f"users/{user_id}/ads_watched").set(watched + 1)
    update_balance(user_id, reward)

# ════════════════════════════════════════════════════════════════
#  OFFERS FUNCTIONS
# ════════════════════════════════════════════════════════════════

def get_offers() -> dict:
    return db.reference("offers").get() or {}

def add_offer(link: str, reward: float, description: str) -> str:
    ref = db.reference("offers").push({
        "link": link,
        "reward": reward,
        "description": description,
        "type": "offer",
        "active": True,
        "created_at": int(time.time()),
    })
    return ref.key

def complete_offer(user_id: int, offer_id: str, reward: float):
    done = db.reference(f"users/{user_id}/offers_done").get() or 0
    db.reference(f"users/{user_id}/offers_done").set(done + 1)
    update_balance(user_id, reward)
    db.reference(f"user_offers/{user_id}/{offer_id}").set(True)

def has_done_offer(user_id: int, offer_id: str) -> bool:
    return db.reference(f"user_offers/{user_id}/{offer_id}").get() is not None

# ════════════════════════════════════════════════════════════════
#  REFERRAL FUNCTIONS
# ════════════════════════════════════════════════════════════════

def credit_referral(referrer_id: int, reward: float):
    ref_count = db.reference(f"users/{referrer_id}/referrals").get() or 0
    db.reference(f"users/{referrer_id}/referrals").set(ref_count + 1)
    update_balance(referrer_id, reward)

# ════════════════════════════════════════════════════════════════
#  STATS FUNCTIONS
# ════════════════════════════════════════════════════════════════

def get_stats() -> dict:
    users = get_all_users()
    total_users = len(users)
    total_balance = sum(u.get("balance", 0) for u in users.values())
    total_ads = sum(u.get("ads_watched", 0) for u in users.values())
    total_tasks = sum(u.get("tasks_done", 0) for u in users.values())
    deposited = sum(1 for u in users.values() if u.get("deposit_status"))
    withdraws = get_all_withdraws()
    total_withdrawn = sum(
        w.get("amount", 0) for w in withdraws.values() if w.get("status") == "completed"
    )
    return {
        "total_users": total_users,
        "deposited_users": deposited,
        "total_balance_in_system": round(total_balance, 2),
        "total_ads_watched": total_ads,
        "total_tasks_done": total_tasks,
        "total_withdrawn": round(total_withdrawn, 2),
    }

# ════════════════════════════════════════════════════════════════
#  BROADCAST FUNCTIONS (WEB SYNC)
# ════════════════════════════════════════════════════════════════

def get_broadcast_queue() -> dict:
    return db.reference("broadcast_queue").get() or {}

def delete_broadcast(qid: str):
    db.reference(f"broadcast_queue/{qid}").delete()

def add_broadcast_from_web(message: str, image_url: str = None):
    db.reference("broadcast_queue").push({
        "message": message,
        "image_url": image_url,
        "status": "pending",
        "timestamp": int(time.time()),
    })

def get_all_user_ids() -> list[int]:
    users = db.reference("users").get() or {}
    return [int(uid) for uid in users.keys()]

# ════════════════════════════════════════════════════════════════
#  CONTENT / NEWS FUNCTIONS
# ════════════════════════════════════════════════════════════════

def add_content(title: str, summary: str, category: str, image: str = None, url: str = None) -> str:
    """Adds a real-time record to the Surface Hub portal."""
    ref = db.reference("content").push({
        "title": title,
        "summary": summary,
        "category": category,
        "image": image,
        "url": url,
        "timestamp": int(time.time()),
        "addedAt": int(time.time())
    })
    return ref.key

def clear_old_content(limit: int = 50):
    """Prunes the content node to keep it performant."""
    ref = db.reference("content")
    content = ref.get() or {}
    if len(content) > limit:
        # Sort by timestamp and remove oldest
        sorted_keys = sorted(content.keys(), key=lambda k: content[k].get("timestamp", 0))
        to_delete = len(content) - limit
        for i in range(to_delete):
            ref.child(sorted_keys[i]).delete()


# ════════════════════════════════════════════════════════════════
#  EARNING SYSTEM FUNCTIONS (NEW - PHASE 2)
# ════════════════════════════════════════════════════════════════

def get_earnings_dashboard() -> dict:
    """Get comprehensive earnings dashboard statistics"""
    users = get_all_users()
    total_users = len(users)
    
    total_balance = 0
    total_earnings = 0
    total_tasks_completed = 0
    deposited_count = 0
    
    for user_id, user_data in users.items():
        balance = user_data.get("balance", 0)
        total_balance += balance
        
        earnings = user_data.get("earnings", {})
        total_earnings += earnings.get("total_earned", 0)
        total_tasks_completed += earnings.get("tasks_completed", 0)
        
        if user_data.get("deposit_status"):
            deposited_count += 1
    
    # Get withdrawal stats
    withdrawals = db.reference("withdrawal_requests").get() or {}
    pending_withdrawals = sum(1 for w in withdrawals.values() if w.get("status") == "pending")
    
    # Get deposit stats
    deposits = db.reference("deposits").get() or {}
    pending_deposits = sum(1 for d in deposits.values() if d.get("status") == "pending")
    
    return {
        "total_users": total_users,
        "deposited_users": deposited_count,
        "total_balance_in_system": round(total_balance, 2),
        "total_earnings_distributed": round(total_earnings, 2),
        "total_tasks_completed": total_tasks_completed,
        "pending_withdrawals": pending_withdrawals,
        "pending_deposits": pending_deposits
    }


def get_user_earnings(user_id: int) -> dict:
    """Get user earnings breakdown"""
    user = get_user(user_id)
    if not user:
        return {}
    
    earnings = user.get("earnings", {})
    return {
        "tasks_completed": earnings.get("tasks_completed", 0),
        "tasks_earnings": earnings.get("tasks_earnings", 0),
        "referral_bonus": earnings.get("referral_bonus", 0),
        "total_earned": earnings.get("total_earned", 0),
        "current_balance": user.get("balance", 0)
    }


def get_pending_withdrawals() -> list:
    """Get all pending withdrawal requests"""
    withdrawals = db.reference("withdrawal_requests").get() or {}
    pending = []
    for w_id, w_data in withdrawals.items():
        if w_data.get("status") == "pending":
            pending.append({
                "request_id": w_id,
                **w_data
            })
    return pending


def get_pending_deposits() -> list:
    """Get all pending deposit verifications"""
    deposits = db.reference("deposits").get() or {}
    pending = []
    for user_id, d_data in deposits.items():
        if d_data.get("status") == "pending":
            user = get_user(int(user_id))
            pending.append({
                "user_id": user_id,
                "username": user.get("username", "Unknown") if user else "Unknown",
                **d_data
            })
    return pending


def get_referral_network(user_id: int) -> dict:
    """Get user's referral network"""
    user = get_user(user_id)
    if not user:
        return {}
    
    referrals = user.get("referrals", {})
    referred_users_dict = referrals.get("referrals_list", {})
    
    referred_users = []
    for ref_user_id, ref_data in referred_users_dict.items():
        referred_user = get_user(int(ref_user_id))
        if referred_user:
            referred_users.append({
                "user_id": ref_user_id,
                "username": referred_user.get("username"),
                "status": "active" if referred_user.get("deposit_status") else "pending",
                "tasks_completed": referred_user.get("earnings", {}).get("tasks_completed", 0),
                "bonus_eligible": referred_user.get("earnings", {}).get("tasks_completed", 0) >= 25
            })
    
    return {
        "referrer_id": user_id,
        "referral_code": referrals.get("referral_code"),
        "total_referred": referrals.get("referred_count", 0),
        "bonus_awarded": referrals.get("bonus_awarded", False),
        "referred_users": referred_users
    }


def create_referral_code(user_id: int) -> str:
    """Generate unique referral code for user"""
    import string
    import random
    
    # Generate 6-char code
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    db.reference(f"users/{user_id}/referrals/referral_code").set(code)
    db.reference(f"referral_codes/{code}").set(user_id)
    
    return code


def get_user_by_referral_code(code: str) -> int:
    """Get user_id from referral code"""
    return db.reference(f"referral_codes/{code}").get()

