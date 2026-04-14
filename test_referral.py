import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "bot")))

from services import firebase as db

user_id = 999999999
db.create_user(user_id, "TestUser", initial_balance=0)
code = db.create_referral_code(user_id)
print(f"Generated referral code: {code}")

user_id2 = db.get_user_by_referral_code(code)
print(f"Looked up user ID: {user_id2}")

if code:
    db.reference(f"referral_codes/{code}").delete()
db.reference(f"users/{user_id}").delete()
