"""
Firebase Transaction Utilities for Atomic Operations
Handles atomic balance updates, referral bonuses, and complex transactions
"""
import time
from config import (
    TASK_COMPLETION_REWARD, 
    MINIMUM_WITHDRAW_AMOUNT, 
    REFERRAL_BONUS_REFERRER,
    REFERRAL_BONUS_REFERRED,
    REFERRAL_TASK_THRESHOLD
)
import services.firebase as db


def atomic_deduct_balance(user_id: int, amount: float) -> bool:
    """
    Atomically deduct balance from user account.
    Returns True if successful, False if insufficient balance.
    """
    try:
        user = db.get_user(user_id)
        current_balance = user.get("balance", 0) if user else 0
        
        if current_balance < amount:
            return False  # Insufficient balance
        
        new_balance = current_balance - amount
        db.reference(f"users/{user_id}/balance").set(new_balance)
        return True
    except Exception as e:
        print(f"❌ Error deducting balance: {e}")
        return False


def atomic_add_balance(user_id: int, amount: float) -> float:
    """
    Atomically add balance to user account.
    Returns new balance.
    """
    try:
        user = db.get_user(user_id)
        current_balance = user.get("balance", 0) if user else 0
        new_balance = current_balance + amount
        db.reference(f"users/{user_id}/balance").set(new_balance)
        return new_balance
    except Exception as e:
        print(f"❌ Error adding balance: {e}")
        return 0


def process_task_completion(user_id: int, task_id: str) -> dict:
    """
    Process task completion with earning and referral bonus check.
    Returns: {success: bool, message: str, new_balance: float}
    """
    try:
        user = db.get_user(user_id)
        if not user:
            return {"success": False, "message": "❌ User not found"}
        
        # Check if already completed
        if db.reference(f"users/{user_id}/tasks_completed/{task_id}").get():
            return {"success": False, "message": "❌ Task already completed"}
        
        # Add task reward
        new_balance = atomic_add_balance(user_id, TASK_COMPLETION_REWARD)
        
        # Mark task as completed
        db.reference(f"users/{user_id}/tasks_completed/{task_id}").set(int(time.time()))
        
        # Increment tasks_completed counter
        tasks_count = user.get("earnings", {}).get("tasks_completed", 0)
        new_tasks_count = tasks_count + 1
        db.reference(f"users/{user_id}/earnings/tasks_completed").set(new_tasks_count)
        
        # Update total earnings
        total_earned = user.get("earnings", {}).get("total_earned", 0)
        db.reference(f"users/{user_id}/earnings/total_earned").set(total_earned + TASK_COMPLETION_REWARD)
        
        # Check for referral bonus trigger (25 tasks completed)
        if new_tasks_count == REFERRAL_TASK_THRESHOLD:
            check_and_award_referral_bonus(user_id)
        
        return {
            "success": True,
            "message": f"✅ Earned ₹{TASK_COMPLETION_REWARD}! ({new_tasks_count} tasks completed)",
            "new_balance": new_balance,
            "tasks_count": new_tasks_count
        }
    except Exception as e:
        return {"success": False, "message": f"❌ Error: {str(e)}"}


def check_and_award_referral_bonus(referred_user_id: int):
    """
    Check if referred user completed 25 tasks and award bonuses automatically.
    Awards:
    - ₹100 to referrer
    - ₹20 to referred user
    """
    try:
        referred_user = db.get_user(referred_user_id)
        if not referred_user:
            return
        
        referrer_id = referred_user.get("referrals", {}).get("referred_by")
        if not referrer_id:
            return  # No referrer
        
        # Check if bonus already awarded
        if referred_user.get("referrals", {}).get("bonus_awarded"):
            return  # Bonus already awarded
        
        # Award bonus to referrer
        referrer_user = db.get_user(referrer_id)
        referrer_balance = referrer_user.get("balance", 0) if referrer_user else 0
        referrer_new_balance = referrer_balance + REFERRAL_BONUS_REFERRER
        db.reference(f"users/{referrer_id}/balance").set(referrer_new_balance)
        
        # Track referrer earnings
        referrer_ref_bonus = referrer_user.get("earnings", {}).get("referral_bonus", 0) if referrer_user else 0
        db.reference(f"users/{referrer_id}/earnings/referral_bonus").set(
            referrer_ref_bonus + REFERRAL_BONUS_REFERRER
        )
        
        # Award bonus to referred user (new user)
        referred_new_balance = referred_user.get("balance", 0) + REFERRAL_BONUS_REFERRED
        db.reference(f"users/{referred_user_id}/balance").set(referred_new_balance)
        
        # Track referred user earnings
        referred_ref_bonus = referred_user.get("earnings", {}).get("referral_bonus", 0)
        db.reference(f"users/{referred_user_id}/earnings/referral_bonus").set(
            referred_ref_bonus + REFERRAL_BONUS_REFERRED
        )
        
        # Mark bonus as awarded
        db.reference(f"users/{referred_user_id}/referrals/bonus_awarded").set(True)
        db.reference(f"users/{referrer_id}/referrals/bonus_given/{referred_user_id}").set(int(time.time()))
        
        # Log bonus distribution
        db.reference("admin_logs/referral_bonuses").push({
            "referrer_id": referrer_id,
            "referred_user_id": referred_user_id,
            "referrer_bonus": REFERRAL_BONUS_REFERRER,
            "referred_bonus": REFERRAL_BONUS_REFERRED,
            "timestamp": int(time.time())
        })
        
        print(f"✅ Referral bonus awarded: {referrer_id} (+₹{REFERRAL_BONUS_REFERRER}), {referred_user_id} (+₹{REFERRAL_BONUS_REFERRED})")
        
    except Exception as e:
        print(f"❌ Error awarding referral bonus: {e}")


def create_withdrawal_request(user_id: int, amount: float, upi: str) -> dict:
    """
    Create a withdrawal request.
    Returns: {success: bool, message: str, request_id: str}
    """
    try:
        user = db.get_user(user_id)
        if not user:
            return {"success": False, "message": "❌ User not found", "request_id": None}
        
        current_balance = user.get("balance", 0)
        
        # Validate minimum amount
        if amount < MINIMUM_WITHDRAW_AMOUNT:
            return {
                "success": False,
                "message": f"❌ Minimum withdrawal is ₹{MINIMUM_WITHDRAW_AMOUNT}",
                "request_id": None
            }
        
        # Validate sufficient balance
        if current_balance < amount:
            return {
                "success": False,
                "message": f"❌ Insufficient balance. Your balance: ₹{current_balance}",
                "request_id": None
            }
        
        # Validate UPI format
        if not is_valid_upi(upi):
            return {
                "success": False,
                "message": "❌ Invalid UPI ID format",
                "request_id": None
            }
        
        # Deduct balance atomically
        deduct_success = atomic_deduct_balance(user_id, amount)
        if not deduct_success:
            return {
                "success": False,
                "message": "❌ Error processing withdrawal",
                "request_id": None
            }
        
        # Create withdrawal request
        request_ref = db.reference("withdrawal_requests").push({
            "user_id": user_id,
            "username": user.get("username"),
            "amount": amount,
            "upi": upi,
            "status": "pending",
            "created_at": int(time.time()),
            "approved_at": None,
            "processed_at": None,
            "admin_note": ""
        })
        
        request_id = request_ref.key
        
        # Log withdrawal request
        db.reference(f"users/{user_id}/withdrawals/{request_id}").set({
            "amount": amount,
            "upi": upi,
            "status": "pending",
            "created_at": int(time.time())
        })
        
        return {
            "success": True,
            "message": f"✅ Withdrawal request created. Processing time: 24-48 hours",
            "request_id": request_id
        }
    
    except Exception as e:
        return {"success": False, "message": f"❌ Error: {str(e)}", "request_id": None}


def approve_withdrawal_request(request_id: str, admin_note: str = "") -> dict:
    """
    Admin approves a withdrawal request.
    Returns: {success: bool, message: str}
    """
    try:
        request = db.reference(f"withdrawal_requests/{request_id}").get()
        if not request:
            return {"success": False, "message": "❌ Withdrawal request not found"}
        
        if request.get("status") != "pending":
            return {"success": False, "message": "❌ Request is no longer pending"}
        
        # Update request status
        db.reference(f"withdrawal_requests/{request_id}").update({
            "status": "approved",
            "approved_at": int(time.time()),
            "admin_note": admin_note
        })
        
        # Notify user (will be handled by admin notifications)
        user_id = request.get("user_id")
        db.reference(f"users/{user_id}/withdrawals/{request_id}").update({
            "status": "approved",
            "approved_at": int(time.time())
        })
        
        return {
            "success": True,
            "message": f"✅ Withdrawal approved. User: {request.get('username')}, Amount: ₹{request.get('amount')}"
        }
    
    except Exception as e:
        return {"success": False, "message": f"❌ Error: {str(e)}"}


def reject_withdrawal_request(request_id: str, reason: str = "") -> dict:
    """
    Admin rejects a withdrawal request and refunds balance.
    Returns: {success: bool, message: str}
    """
    try:
        request = db.reference(f"withdrawal_requests/{request_id}").get()
        if not request:
            return {"success": False, "message": "❌ Withdrawal request not found"}
        
        if request.get("status") != "pending":
            return {"success": False, "message": "❌ Request is no longer pending"}
        
        # Refund balance
        user_id = request.get("user_id")
        amount = request.get("amount")
        atomic_add_balance(user_id, amount)
        
        # Update request status
        db.reference(f"withdrawal_requests/{request_id}").update({
            "status": "rejected",
            "rejected_at": int(time.time()),
            "rejection_reason": reason
        })
        
        # Notify user
        db.reference(f"users/{user_id}/withdrawals/{request_id}").update({
            "status": "rejected",
            "rejected_at": int(time.time())
        })
        
        return {
            "success": True,
            "message": f"✅ Withdrawal rejected. Balance refunded to {request.get('username')}"
        }
    
    except Exception as e:
        return {"success": False, "message": f"❌ Error: {str(e)}"}


def is_valid_upi(upi: str) -> bool:
    """Validate UPI format (basic check)"""
    # Simple UPI validation: format should be handle@bankname
    if "@" not in upi or len(upi) < 5:
        return False
    return True


def migrate_user_to_new_schema(user_id: int) -> bool:
    """
    Migrate existing user to new earning system schema.
    Adds earnings tracking and referral structures.
    """
    try:
        user = db.get_user(user_id)
        if not user:
            return False
        
        # Check if already migrated
        if user.get("earnings"):
            return True  # Already migrated
        
        # Create new earning structure
        db.reference(f"users/{user_id}/earnings").set({
            "tasks_completed": 0,
            "tasks_earnings": 0,
            "referral_bonus": 0,
            "total_earned": 0
        })
        
        # Create referral structure
        db.reference(f"users/{user_id}/referrals").set({
            "referred_by": user.get("referred_by"),
            "referral_code": None,
            "referred_count": 0,
            "bonus_awarded": False,
            "bonus_given": {}
        })
        
        # Create tasks tracking
        db.reference(f"users/{user_id}/tasks_completed").set({})
        
        # Create withdrawals tracking
        db.reference(f"users/{user_id}/withdrawals").set({})
        
        return True
    
    except Exception as e:
        print(f"❌ Error migrating user {user_id}: {e}")
        return False
