import sys
import os

# Add src to python path
sys.path.append(os.path.join(os.getcwd(), "src"))

from agents.author import Author
from agents.auditor import Auditor

def run_feedback_loop():
    print("--- 🚀 Starting Trace STLC Feedback Loop ---")
    
    # 1. Initialize Agents
    author = Author()
    auditor = Auditor()
    
    # 2. Define the Requirement
    # We purposefully make it complex to see if the Author misses details initially
    requirement = """
    Create test cases for a 'Registration Page'.
    It MUST include:
    1. Valid email format check.
    2. Password strength validation (min 8 chars, 1 symbol).
    3. A 'Terms of Service' checkbox that must be checked.
    """
    
    print(f"\n📋 User Requirement:\n{requirement}\n")
    print("-" * 60)

    # 3. Start the Loop
    topic = requirement
    feedback = ""
    previous_draft = ""  # Start empty
    attempt = 1
    max_attempts = 3
    final_test_cases = ""

    while attempt <= max_attempts:
        print(f"\n🔄 Attempt #{attempt} in progress...")
        
        # A. Author Writes (Passing previous_draft ensures updates, not rewrites)
        draft_test_cases = author.write(topic, feedback, previous_draft)
        print("\n📝 Author Draft Generated.")
        
        # Update previous_draft so the next loop sees the latest version
        previous_draft = draft_test_cases

        # B. Auditor Reviews
        review_result = auditor.review(requirement, draft_test_cases)
        
        # C. Check Decision
        if "STATUS: APPROVED" in review_result:
            print("\n✅ Auditor Decision: APPROVED")
            print("Feedback: Looks good.")
            final_test_cases = draft_test_cases
            break
        else:
            print("\n❌ Auditor Decision: REJECTED")
            print(f"Auditor Feedback:\n{review_result}")
            
            # Feed the review back into the loop
            feedback = review_result
            attempt += 1
            
            if attempt > max_attempts:
                print("\n⚠️ Max attempts reached. Saving current version.")
                final_test_cases = draft_test_cases
    
    print("-" * 60)
    print("\n🏆 Final Approved Output:\n")
    print(final_test_cases)
    print("\n--- End of Test Loop ---")

if __name__ == "__main__":
    run_feedback_loop()