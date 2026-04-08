import time
import secrets
import services.firebase as fb

def generate_reward_token(user_id: int, task_id: str, reward_amount: float) -> str:
    """
    Generate a secure token for claiming a reward via the website.
    Stored in Firebase with an expiry (30 mins).
    """
    token = secrets.token_urlsafe(16)
    fb.db.reference(f"reward_tokens/{token}").set({
        "user_id": user_id,
        "task_id": task_id,
        "reward_amount": reward_amount,
        "expiry": int(time.time()) + (30 * 60) # 30 mins
    })
    return token

def verify_and_claim_token(token: str) -> dict:
    """
    Verify the token and return reward details.
    Deletes the token after use.
    """
    token_ref = fb.db.reference(f"reward_tokens/{token}")
    data = token_ref.get()
    
    if not data:
        return {"success": False, "message": "❌ Invalid or expired reward token."}
    
    if int(time.time()) > data.get("expiry", 0):
        token_ref.delete()
        return {"success": False, "message": "❌ Reward token has expired."}
    
    # Delete token to prevent double-claiming
    token_ref.delete()
    
    return {
        "success": True,
        "user_id": data.get("user_id"),
        "task_id": data.get("task_id"),
        "reward_amount": data.get("reward_amount")
    }
