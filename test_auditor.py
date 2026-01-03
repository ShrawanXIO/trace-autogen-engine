import sys
import os

# Add 'src' to python path so we can find the agents
sys.path.append(os.path.join(os.getcwd(), "src"))

from agents.auditor import Auditor

# --- 1. Mock the Archivist (The Brain) ---
# This simulates the Knowledge Base without needing the real database.
class MockArchivist:
    def ask(self, query):
        # We force a specific Business Rule to exist for this test
        return "Documentation Rule: The system requires a password of at least 10 characters."

def run_test():
    print("--- Starting Auditor Test (Logic & Chain of Thought) ---")

    # Initialize Auditor with our Mock Brain
    try:
        mock_archivist = MockArchivist()
        auditor = Auditor(archivist_agent=mock_archivist)
    except Exception as e:
        print(f"Failed to initialize: {e}")
        return

    # --- SCENARIO 1: The "Lazy" Test Case (Should Fail) ---
    print("\n[Scenario 1] Testing a Draft that violates Business Rules.")
    print("Context: Rule = Min 10 chars. Draft uses 5 chars but expects Success.")
    
    requirement = "Verify login with 5 character password."
    
    # This draft is WRONG because it expects 'Success' for a short password
    bad_draft = """
    Test Case ID: TC_01
    Title: Login Short Password
    Steps: Enter '12345', Click Login.
    Expected Result: Login Successful.
    """

    print("\n>>> Sending for Review...")
    result = auditor.review(requirement, bad_draft)
    
    print("\n>>> Final Decision:")
    print(result)

    # --- SCENARIO 2: The "Smart" Test Case (Should Pass) ---
    print("\n" + "="*60)
    print("\n[Scenario 2] Testing a Draft that handles Negative Scenarios correctly.")
    print("Context: Rule = Min 10 chars. Draft uses 5 chars and expects Error Message.")
    
    good_draft = """
    Test Case ID: TC_01
    Title: Login Short Password
    Steps: Enter '12345', Click Login.
    Expected Result: System displays 'Password too short' error.
    """
    
    print("\n>>> Sending for Review...")
    result = auditor.review(requirement, good_draft)
    
    print("\n>>> Final Decision:")
    print(result)

if __name__ == "__main__":
    run_test()