import sys
import os

# Add the project root to sys.path so we can import services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import services.firebase as fb

def reset_database():
    print("⚠️  Starting Surface Hub Database Reset...")
    
    nodes_to_clear = [
        "users",
        "deposits",
        "withdraws",
        "withdrawal_requests",
        "content",
        "tasks",
        "user_tasks",
        "user_offers",
        "admin_logs",
        "broadcast_queue",
        "referral_codes"
    ]
    
    for node in nodes_to_clear:
        try:
            print(f"🔄 Clearing {node}...")
            fb.db.reference(node).delete()
            print(f"✅ Cleared {node}")
        except Exception as e:
            print(f"❌ Error clearing {node}: {e}")
            
    print("\n✨ Database Reset Complete! Ready for fresh start.")

if __name__ == "__main__":
    confirm = input("Are you sure you want to WIPE EVERYTHING? (yes/no): ")
    if confirm.lower() == "yes":
        reset_database()
    else:
        print("Operation cancelled.")
