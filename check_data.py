import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db
import json

load_dotenv()

# Initialize Firebase
cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': os.getenv("FIREBASE_URL")
    })

def check_content():
    ref = db.reference("content")
    data = ref.get() or {}
    print(f"Total News Items: {len(data)}")
    
    for cid, item in list(data.items())[:2]:
        content = item.get("content", "")
        print(f"\n--- Item {cid} ---")
        print(f"Has [AD_SLOT]: {'[AD_SLOT]' in content}")
        if '[AD_SLOT]' not in content:
            print("Snippet:", content[:200])

if __name__ == "__main__":
    check_content()
