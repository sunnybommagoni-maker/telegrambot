from bot.services.news_agent import AIAgent
import logging

logging.basicConfig(level=logging.INFO)

def test_fail_safe():
    agent = AIAgent()
    
    # Simulate a model that FORGOT the ad slots
    bad_content = "This is paragraph one.\n\nThis is paragraph two.\n\nThis is paragraph three.\n\nThis is paragraph four.\n\nThis is paragraph five."
    
    fixed_content = agent.fix_ad_slots(bad_content)
    
    print("\n--- ORIGINAL CONTENT ---")
    print(bad_content)
    print("\n--- FIXED CONTENT ---")
    print(fixed_content)
    
    # Verification
    if "[AD_SLOT]" in fixed_content:
        print("\n✅ FAIL-SAFE SUCCESS: Ad slots injected.")
        slots = fixed_content.count("[AD_SLOT]")
        print(f"Total Slots: {slots}")
    else:
        print("\n❌ FAIL-SAFE FAILURE: No ad slots found.")

if __name__ == "__main__":
    test_fail_safe()
