import sys
import os

# --- ROBUST PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "src")
sys.path.append(src_path)

from agents.author import Author

def run_test():
    print("--- Starting Author Agent Test (ID Verification) ---")

    # 1. Initialize Author
    try:
        # Note: This connects to your real local Ollama instance
        author = Author()
        print("✅ Author initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize Author. Is Ollama running? Error: {e}")
        return

    # --- SCENARIO: ID ADHERENCE TEST ---
    # We provide a specific, weird ID to ensure the LLM isn't just guessing "TC_001"
    target_id = "TC_FIXED_888"
    scenario_name = "Verify logout works after session timeout"
    
    # The input format you enforced in author.py
    topic_input = f"{target_id}: {scenario_name}"
    context_input = "Users session timeout is set to 15 minutes."

    print(f"\n[Test] Sending Task: '{topic_input}'")
    print(">>> Author is writing...")

    # 2. Generate Draft
    draft = author.write(topic=topic_input, context=context_input)
    
    print("\n--- OUTPUT START ---")
    print(draft)
    print("--- OUTPUT END ---\n")

    # 3. Verify the ID exists exactly as sent
    expected_string = f"Test Case ID: {target_id}"
    
    if expected_string in draft:
        print(f"✅ PASS: Author respected the ID constraint. Found '{expected_string}'.")
    else:
        print(f"❌ FAIL: Author hallucinated the ID.")
        print(f"   Expected to find: '{expected_string}'")
        print(f"   Actual output might have used 'TC_001' or similar.")

if __name__ == "__main__":
    run_test()