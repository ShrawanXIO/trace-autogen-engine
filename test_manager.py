import sys
import os
from unittest.mock import MagicMock, patch

# Add src to path so we can import the Manager
sys.path.append(os.path.join(os.getcwd(), "src"))

from agents.manager import Manager

def run_test():
    print("--- Starting Manager Logic Test (Simulation) ---")

    # We use 'patch' to replace real agents with Fake ones (Mocks)
    # This ensures we test the Manager's LOGIC, not the AI's creativity.
    with patch('agents.manager.Archivist') as MockArchivist, \
         patch('agents.manager.Author') as MockAuthor, \
         patch('agents.manager.Auditor') as MockAuditor, \
         patch('agents.manager.Scribe') as MockScribe, \
         patch('agents.manager.ingest_knowledge_base') as MockIngest, \
         patch('agents.manager.ChatOllama') as MockLLM:

        # 1. Setup the Simulation
        print("\n[Setup] Initializing Manager with Mock Team...")
        
        # Mock the Ingestion result
        MockIngest.return_value = "✔ System is up-to-date (Simulation)"
        
        # Initialize Manager (It will use our Mocks now)
        manager = Manager()

        # Force the Intent Classifier to be deterministic for this test
        # (So we don't need the real LLM running for this specific logic check)
        manager.classify_intent = MagicMock(side_effect=lambda x: "QUESTION" if "?" in x else "REQUIREMENT")

        # --- TEST 1: The "Research" Route ---
        print("\n" + "="*40)
        print("[TEST 1] User asks a Question (Research Mode)")
        
        # Set expected answer from Archivist
        manager.archivist.ask.return_value = "The password policy requires 10 characters."
        
        response = manager.process_request("What is the password policy?")
        
        print(f"Manager Response: {response}")
        if "Archivist Report" in response:
            print(">>> PASS: Manager correctly routed to Archivist.")
        else:
            print(">>> FAIL: Manager failed to route question.")

        # --- TEST 2: The "Duplicate" Check ---
        print("\n" + "="*40)
        print("[TEST 2] User submits a Duplicate Scenario")
        
        # Simulate Archivist finding a duplicate
        manager.archivist.ask.return_value = "FOUND_EXISTING: TC_001 Login"
        
        response = manager.process_request("Verify Login")
        
        print(f"Manager Response: {response}")
        if "Duplicate detected" in response:
            print(">>> PASS: Manager stopped the process correctly.")
        else:
            print(">>> FAIL: Manager did not catch the duplicate.")

        # --- TEST 3: The "Full Workflow" ---
        print("\n" + "="*40)
        print("[TEST 3] User submits a New Scenario (Full Generation)")
        
        # Simulate clean slate (No duplicates) + Context retrieval
        manager.archivist.ask.side_effect = ["NO_EXISTING_TESTS", "Context: Valid rules found."]
        
        # Simulate Author writing a draft
        manager.author.write.return_value = "DRAFT: Test Case 1..."
        
        # Simulate Auditor approving it
        manager.auditor.review.return_value = "STATUS: APPROVED"
        
        # Simulate Scribe saving it
        manager.scribe.save.return_value = "File Saved Successfully."

        response = manager.process_request("Verify Logout")
        
        if "Workflow Complete" in response and "File Saved" in response:
            print(">>> PASS: Manager orchestrated the full team successfully.")
        else:
            print(">>> FAIL: Workflow failed.")

if __name__ == "__main__":
    run_test()