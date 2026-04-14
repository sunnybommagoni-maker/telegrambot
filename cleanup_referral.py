import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "bot")))

from services import firebase as db

users = db.get_all_users()
fixed = 0
for uid, udata in users.items():
    if isinstance(udata, dict):
        referrals = udata.get("referrals", {})
        if isinstance(referrals, dict):
            code = referrals.get("referral_code")
            if code == "None" or code is None:
                # generate proper one
                new_code = db.create_referral_code(uid)
                print(f"Fixed {uid}: assigned new code {new_code}")
                fixed += 1

print(f"Cleanup complete. Fixed {fixed} users.")
