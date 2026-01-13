import sys
import os

# Robust Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "src")
sys.path.append(src_path)

from agents.author import Author
from agents.auditor import Auditor
# We need a dummy archivist for the Auditor
class MockArchivist:
    def ask(self, q): return "No specific legacy rules."

def run_feedback_loop():
    print("--- 🚀 Starting Trace STLC Feedback Loop ---")
    
    author = Author()
    auditor = Auditor(archivist_agent=MockArchivist())
    
    topic = "Registration Page Scenarios"
    context = """
    REQUIREMENTS:
    1. Valid email format check.
    2. Password strength validation (min 8 chars).
    """
    
    print(f"\n📋 User Requirement:\n{context}\n")
    print("-" * 60)

    feedback = ""
    previous_draft = ""
    attempt = 1
    max_attempts = 2 # Keep it short for testing

    while attempt <= max_attempts:
        print(f"\n🔄 Attempt #{attempt} in progress...")
        
        # Keyword arguments are safer
        draft_test_cases = author.write(topic, context=context, feedback=feedback, previous_draft=previous_draft)
        print("\n📝 Author Draft Generated.")
        
        previous_draft = draft_test_cases

        review_result = auditor.review(context, draft_test_cases)
        
        if "STATUS: APPROVED" in review_result:
            print("\n✅ Auditor Decision: APPROVED")
            print("Feedback: Looks good.")
            break
        else:
            print("\n❌ Auditor Decision: REJECTED")
            print(f"Auditor Feedback (Snippet): {review_result[:100]}...")
            
            feedback = review_result.replace("STATUS: REJECTED", "").strip()
            attempt += 1
            
    print("\n--- End of Test Loop ---")

if __name__ == "__main__":
    run_feedback_loop()