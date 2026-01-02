import sys
import os

# Add 'src' to python path
sys.path.append(os.path.join(os.getcwd(), "src"))

from agents.author import Author

def run_test():
    print("--- Starting Author Interactive Test ---")
    try:
        # Initialize
        agent = Author()
        
        # --- STEP 1: First Draft ---
        topic = "Login with invalid password"
        print(f"\n1. Writing First Draft for: '{topic}'...")
        
        draft = agent.write(topic)
        
        print("\n--- Draft Output ---")
        print(draft)
        print("--------------------")

        # --- STEP 2: Revision (The New Feature) ---
        feedback = "You missed the cleanup step. Please add 'Clear browser cache' to the cleanup steps for all test cases."
        print(f"\n2. Sending Feedback: '{feedback}'...")
        
        # We pass the OLD draft so the agent can fix it
        revised_content = agent.write(topic, feedback=feedback, previous_draft=draft)
        
        print("\n--- Revised Output ---")
        print(revised_content)
        print("----------------------")
        
        if "Clear browser cache" in revised_content:
            print("✅ Success: Author successfully applied the feedback.")
        else:
            print("⚠️ Warning: Feedback might not have been applied perfectly.")

    except Exception as e:
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    run_test()