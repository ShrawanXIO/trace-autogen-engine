import sys
import os

# --- ROBUST PATH SETUP ---
# 1. Get current directory (tests/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 2. Go UP one level to root, then DOWN into src
src_path = os.path.join(current_dir, "..", "src")
# 3. Add to Python Path
sys.path.append(src_path)

from agents.auditor import Auditor

# Mock Brain to test Logic in Isolation
class MockArchivist:
    def ask(self, query):
        return "Documentation Rule: The system requires a password of at least 10 characters."

def run_test():
    print("--- Starting Auditor Test (Logic Audit) ---")

    try:
        mock_archivist = MockArchivist()
        # Initialize Auditor (Now uses config.py)
        auditor = Auditor(archivist_agent=mock_archivist)
        print("✅ Auditor initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return

    # --- SCENARIO 1: FAIL CASE ---
    print("\n[Scenario 1] Testing a Draft that violates Business Rules.")
    requirement = "Verify login with 5 character password."
    bad_draft = """
    Test Case ID: TC_01
    Title: Login Short Password
    Steps: Enter '12345', Click Login.
    Expected Result: Login Successful.
    """

    print(">>> Sending for Review...")
    result = auditor.review(requirement, bad_draft)
    
    # We expect REJECTED
    if "REJECTED" in result:
        print(f"✅ PASS: Auditor correctly REJECTED the bad draft.")
    else:
        print(f"❌ FAIL: Auditor approved a bad draft. Result: {result}")

    # --- SCENARIO 2: PASS CASE ---
    print("\n[Scenario 2] Testing a Draft that handles Negative Scenarios correctly.")
    good_draft = """
    Test Case ID: TC_01
    Title: Login Short Password
    Steps: Enter '12345', Click Login.
    Expected Result: System displays 'Password too short' error.
    """
    
    print(">>> Sending for Review...")
    result = auditor.review(requirement, good_draft)
    
    # We expect APPROVED
    if "APPROVED" in result:
        print(f"✅ PASS: Auditor correctly APPROVED the good draft.")
    else:
        print(f"❌ FAIL: Auditor rejected a good draft. Result: {result}")

if __name__ == "__main__":
    run_test()