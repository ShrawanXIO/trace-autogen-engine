import sys
import os
from unittest.mock import MagicMock, patch

# Add src to path so we can import the Manager
# Go up one level from 'tests' to reach 'src'
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "src")
sys.path.append(src_path)

from agents.manager import Manager

def run_test():
    print("--- Starting Manager Logic Test (Aligned with New Code) ---")

    # We patch 'config' to prevent real connections
    # We patch the agents to test Manager logic in isolation
    with patch('agents.manager.Archivist') as MockArchivist, \
         patch('agents.manager.Author') as MockAuthor, \
         patch('agents.manager.Auditor') as MockAuditor, \
         patch('agents.manager.Scribe') as MockScribe, \
         patch('agents.manager.ingest_knowledge_base') as MockIngest, \
         patch('agents.manager.config') as MockConfig:

        # --- SETUP ---
        print("\n[Setup] Initializing Manager with Mock Team...")
        manager = Manager()
        
        # Mock the "Smart Parser" to avoid needing the LLM for simple parsing
        manager.analyze_input_smartly = MagicMock(return_value=("Test Context", ["Scenario 1"]))

        # ====================================================
        # TEST 1: The "Research" Route (Question Handling)
        # ====================================================
        print("\n" + "="*40)
        print("[TEST 1] User asks a Question (Research Mode)")
        
        # Setup: Archivist gives a direct answer
        manager.archivist.ask.return_value = "The password policy requires 10 characters."
        
        # Execution
        response = manager.process_request("What is the password policy?")
        
        # Verification: Check if the ANSWER is present (not the label "Archivist Report")
        print(f"Manager Response: {response}")
        if "password policy" in response:
            print(">>> PASS: Manager correctly routed question to Archivist.")
        else:
            print(">>> FAIL: Manager output did not contain the expected answer.")

        # ====================================================
        # TEST 2: The "Duplicate" Handling (Reconciliation Mode)
        # ====================================================
        print("\n" + "="*40)
        print("[TEST 2] User submits a Duplicate Scenario")
        
        # Setup: Archivist finds a legacy match (TC_001)
        # The Manager should USE this ID, not create TC_NEW
        manager.archivist.analyze_scenario.return_value = "[MATCH] | TC_001 | Verify Login"
        
        # CRITICAL FIX: Auditor MUST approve, or the loop will crash the test
        manager.auditor.review.return_value = "STATUS: APPROVED"
        
        # Setup: Scribe just confirms save
        manager.scribe.save.return_value = "File Saved: TC_001.csv"

        # Execution
        manager.process_request("Verify Login")
        
        # Verification: Did the Author receive 'TC_001' in the prompt?
        # We peek inside the Mock to see what arguments it was called with
        args, _ = manager.author.write.call_args
        sent_topic = args[0] # The first argument passed to author.write
        
        print(f"Sent to Author: {sent_topic}")
        
        if "TC_001" in sent_topic:
            print(">>> PASS: Manager preserved the Legacy ID (TC_001).")
        else:
            print(f">>> FAIL: Manager generated a NEW ID. Expected TC_001.")

        # ====================================================
        # TEST 3: The "Full Workflow" (New Scenario)
        # ====================================================
        print("\n" + "="*40)
        print("[TEST 3] User submits a New Scenario (Full Generation)")
        
        # Setup: Archivist says it is NEW
        manager.archivist.analyze_scenario.return_value = "[NEW] | TC_NEW | Verify Logout"
        
        # Setup: Reset Auditor to Approve
        manager.auditor.review.return_value = "STATUS: APPROVED"
        
        # Setup: Scribe returns a success message
        expected_scribe_msg = "Success: Test Cases Saved to Excel."
        manager.scribe.save.return_value = expected_scribe_msg

        # Execution
        response = manager.process_request("Verify Logout")
        
        # Verification
        if response == expected_scribe_msg:
            print(">>> PASS: Workflow completed and returned Scribe's message.")
        else:
            print(f">>> FAIL: Workflow return mismatch. Got: {response}")

if __name__ == "__main__":
    run_test()