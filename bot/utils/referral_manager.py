"""
Referral System Manager
Handles referral code generation, tracking, and bonus distribution
"""
import string
import random
import time
from config import REFERRAL_BONUS_REFERRER, REFERRAL_BONUS_REFERRED, REFERRAL_TASK_THRESHOLD
import services.firebase as db


def generate_referral_code(user_id: int, length: int = 8) -> str:
    """
    Generate a unique referral code for the user.
    Format: User-initiated or auto-generated code
    """
    try:
        # Check if user already has referral code
        user = db.get_user(user_id)
        if user and user.get("referrals", {}).get("referral_code"):
            return user["referrals"]["referral_code"]
        
        # Generate unique code
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            # Check if code already exists
            if not db.reference(f"referral_codes/{code}").get():
                break
        
        # Store mapping
        db.reference(f"users/{user_id}/referrals/referral_code").set(code)
        db.reference(f"referral_codes/{code}").set(user_id)
        
        # Initialize referrals list
        db.reference(f"users/{user_id}/referrals/referrals_list").set({})
        
        return code
    
    except Exception as e:
        print(f"❌ Error generating referral code: {e}")
        return None


def get_referral_code(user_id: int) -> str:
    """Get user's referral code, or generate if doesn't exist"""
    try:
        user = db.get_user(user_id)
        if user and user.get("referrals", {}).get("referral_code"):
            return user["referrals"]["referral_code"]
        
        # Generate if doesn't exist
        return generate_referral_code(user_id)
    
    except Exception as e:
        print(f"❌ Error getting referral code: {e}")
        return None


def validate_and_link_referral(referred_user_id: int, referral_code: str) -> dict:
    """
    Validate referral code and link referred user to referrer.
    Should be called after new user registration.
    Returns: {success: bool, message: str, referrer_id: int}
    """
    try:
        # Check if user already linked to referrer
        user = db.get_user(referred_user_id)
        if user and user.get("referrals", {}).get("referred_by"):
            return {
                "success": False,
                "message": "❌ User already has a referrer",
                "referrer_id": None
            }
        
        # Get referrer ID from code
        referrer_id = db.reference(f"referral_codes/{referral_code}").get()
        if not referrer_id:
            return {
                "success": False,
                "message": "❌ Invalid referral code",
                "referrer_id": None
            }
        
        # Prevent self-referral
        if referrer_id == referred_user_id:
            return {
                "success": False,
                "message": "❌ Cannot refer yourself",
                "referrer_id": None
            }
        
        # Link referrer to referred user
        db.reference(f"users/{referred_user_id}/referrals/referred_by").set(referrer_id)
        
        # Add to referrer's list
        db.reference(f"users/{referrer_id}/referrals/referrals_list/{referred_user_id}").set({
            "username": user.get("username"),
            "joined_at": int(time.time()),
            "status": "pending"
        })
        
        # Increment referred count
        referred_count = db.get_user(referrer_id).get("referrals", {}).get("referred_count", 0)
        db.reference(f"users/{referrer_id}/referrals/referred_count").set(referred_count + 1)
        
        return {
            "success": True,
            "message": f"✅ Linked to referrer successfully",
            "referrer_id": referrer_id
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error: {str(e)}",
            "referrer_id": None
        }


def get_referral_statistics(user_id: int) -> dict:
    """Get referral statistics for user"""
    try:
        user = db.get_user(user_id)
        if not user:
            return {}
        
        referrals = user.get("referrals", {})
        referred_users = referrals.get("referrals_list", {})
        
        # Count active vs pending
        active_count = 0
        pending_count = 0
        completed_25_tasks = 0
        
        for ref_user_id in referred_users.keys():
            ref_user = db.get_user(int(ref_user_id))
            if ref_user:
                if ref_user.get("deposit_status"):
                    active_count += 1
                else:
                    pending_count += 1
                
                tasks_completed = ref_user.get("earnings", {}).get("tasks_completed", 0)
                if tasks_completed >= REFERRAL_TASK_THRESHOLD:
                    completed_25_tasks += 1
        
        return {
            "total_referred": referrals.get("referred_count", 0),
            "active_referrals": active_count,
            "pending_referrals": pending_count,
            "qualified_for_bonus": completed_25_tasks,
            "bonus_awarded": referrals.get("bonus_awarded", False),
            "potential_earnings": completed_25_tasks * REFERRAL_BONUS_REFERRER
        }
    
    except Exception as e:
        print(f"❌ Error getting referral stats: {e}")
        return {}


def get_all_referrals(user_id: int) -> list:
    """Get list of all referred users with details"""
    try:
        user = db.get_user(user_id)
        if not user:
            return []
        
        referrals = user.get("referrals", {})
        referred_users_dict = referrals.get("referrals_list", {})
        
        result = []
        for ref_user_id, ref_info in referred_users_dict.items():
            ref_user = db.get_user(int(ref_user_id))
            if ref_user:
                tasks_completed = ref_user.get("earnings", {}).get("tasks_completed", 0)
                result.append({
                    "user_id": ref_user_id,
                    "username": ref_user.get("username"),
                    "status": "active" if ref_user.get("deposit_status") else "pending",
                    "tasks_completed": tasks_completed,
                    "bonus_eligible": tasks_completed >= REFERRAL_TASK_THRESHOLD,
                    "joined_at": ref_info.get("joined_at"),
                    "earnings": ref_user.get("earnings", {})
                })
        
        return result
    
    except Exception as e:
        print(f"❌ Error getting referrals: {e}")
        return []


def check_referral_bonus_trigger(referred_user_id: int) -> dict:
    """
    Check if referred user has completed 25 tasks and should get bonus.
    This is called after each task completion.
    Returns: {bonus_awarded: bool, referrer_bonus: float, referred_bonus: float}
    """
    try:
        referred_user = db.get_user(referred_user_id)
        if not referred_user:
            return {"bonus_awarded": False}
        
        # Check if bonus already awarded
        if referred_user.get("referrals", {}).get("bonus_awarded"):
            return {"bonus_awarded": False, "reason": "Bonus already awarded"}
        
        # Get referrer
        referrer_id = referred_user.get("referrals", {}).get("referred_by")
        if not referrer_id:
            return {"bonus_awarded": False, "reason": "No referrer"}
        
        # Check task threshold
        tasks_completed = referred_user.get("earnings", {}).get("tasks_completed", 0)
        if tasks_completed < REFERRAL_TASK_THRESHOLD:
            return {
                "bonus_awarded": False,
                "reason": f"Threshold not met ({tasks_completed}/{REFERRAL_TASK_THRESHOLD} tasks)"
            }
        
        # Award bonuses
        return award_referral_bonuses(referrer_id, referred_user_id)
    
    except Exception as e:
        print(f"❌ Error checking referral bonus trigger: {e}")
        return {"bonus_awarded": False, "error": str(e)}


def award_referral_bonuses(referrer_id: int, referred_user_id: int) -> dict:
    """
    Award referral bonuses to both referrer and referred user.
    Referrer: ₹100
    Referred: ₹20
    """
    try:
        referrer = db.get_user(referrer_id)
        referred_user = db.get_user(referred_user_id)
        
        if not referrer or not referred_user:
            return {"bonus_awarded": False, "error": "User not found"}
        
        # Check if already awarded
        if referred_user.get("referrals", {}).get("bonus_awarded"):
            return {"bonus_awarded": False, "error": "Bonus already awarded"}
        
        # Add balance to referrer
        referrer_balance = referrer.get("balance", 0)
        new_referrer_balance = referrer_balance + REFERRAL_BONUS_REFERRER
        db.reference(f"users/{referrer_id}/balance").set(new_referrer_balance)
        
        # Update referrer's referral bonus earnings
        referrer_ref_bonus = referrer.get("earnings", {}).get("referral_bonus", 0)
        db.reference(f"users/{referrer_id}/earnings/referral_bonus").set(
            referrer_ref_bonus + REFERRAL_BONUS_REFERRER
        )
        
        # Add balance to referred user
        referred_balance = referred_user.get("balance", 0)
        new_referred_balance = referred_balance + REFERRAL_BONUS_REFERRED
        db.reference(f"users/{referred_user_id}/balance").set(new_referred_balance)
        
        # Update referred user's referral bonus earnings
        referred_ref_bonus = referred_user.get("earnings", {}).get("referral_bonus", 0)
        db.reference(f"users/{referred_user_id}/earnings/referral_bonus").set(
            referred_ref_bonus + REFERRAL_BONUS_REFERRED
        )
        
        # Mark bonus as awarded
        db.reference(f"users/{referred_user_id}/referrals/bonus_awarded").set(True)
        
        # Log the bonus distribution
        db.reference("admin_logs/referral_bonuses").push({
            "referrer_id": referrer_id,
            "referred_user_id": referred_user_id,
            "referrer_bonus": REFERRAL_BONUS_REFERRER,
            "referred_bonus": REFERRAL_BONUS_REFERRED,
            "timestamp": int(time.time())
        })
        
        print(f"✅ Referral bonuses awarded: {referrer_id} +{REFERRAL_BONUS_REFERRER}, {referred_user_id} +{REFERRAL_BONUS_REFERRED}")
        
        return {
            "bonus_awarded": True,
            "referrer_id": referrer_id,
            "referrer_bonus": REFERRAL_BONUS_REFERRER,
            "referred_user_id": referred_user_id,
            "referred_bonus": REFERRAL_BONUS_REFERRED
        }
    
    except Exception as e:
        print(f"❌ Error awarding bonuses: {e}")
        return {"bonus_awarded": False, "error": str(e)}
