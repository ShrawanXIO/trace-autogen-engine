import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "src")
sys.path.append(src_path)

from agents.manager import Manager

# Define a Test Class (Discoverable by Test Explorer)
class TestManagerLogic(unittest.TestCase):

    def setUp(self):
        """Runs before every test. Sets up the patches."""
        # Create a patcher for every dependency
        self.patcher_archivist = patch('agents.manager.Archivist')
        self.patcher_author = patch('agents.manager.Author')
        self.patcher_auditor = patch('agents.manager.Auditor')
        self.patcher_scribe = patch('agents.manager.Scribe')
        self.patcher_ingest = patch('agents.manager.ingest_knowledge_base')
        self.patcher_config = patch('agents.manager.config')

        # Start patches and store mocks
        self.MockArchivist = self.patcher_archivist.start()
        self.MockAuthor = self.patcher_author.start()
        self.MockAuditor = self.patcher_auditor.start()
        self.MockScribe = self.patcher_scribe.start()
        self.MockIngest = self.patcher_ingest.start()
        self.MockConfig = self.patcher_config.start()

        # Initialize Manager
        self.manager = Manager()
        # Mock the "Smart Parser"
        self.manager.analyze_input_smartly = MagicMock(return_value=("Test Context", ["Scenario 1"]))

    def tearDown(self):
        """Runs after every test. Stops the patches."""
        patch.stopall()

    def test_research_route_question_handling(self):
        """TEST 1: User asks a Question (Research Mode)"""
        # Setup
        self.manager.archivist.ask.return_value = "The password policy requires 10 characters."
        
        # Execution
        response = self.manager.process_request("What is the password policy?")
        
        # Assertion
        self.assertIn("password policy", response, "Manager output should contain the archivist's answer.")

    def test_duplicate_scenario_handling(self):
        """TEST 2: User submits a Duplicate Scenario"""
        # Setup
        self.manager.archivist.analyze_scenario.return_value = "[MATCH] | TC_001 | Verify Login"
        self.manager.auditor.review.return_value = "STATUS: APPROVED"
        self.manager.scribe.save.return_value = "File Saved: TC_001.csv"

        # Execution
        self.manager.process_request("Verify Login")
        
        # Verification
        args, _ = self.manager.author.write.call_args
        sent_topic = args[0]
        
        # Assertion
        self.assertIn("TC_001", sent_topic, "Manager should preserve the Legacy ID (TC_001).")

    def test_full_workflow_new_scenario(self):
        """TEST 3: User submits a New Scenario (Full Generation)"""
        # Setup
        self.manager.archivist.analyze_scenario.return_value = "[NEW] | TC_NEW | Verify Logout"
        self.manager.auditor.review.return_value = "STATUS: APPROVED"
        expected_msg = "Success: Test Cases Saved to Excel."
        self.manager.scribe.save.return_value = expected_msg

        # Execution
        response = self.manager.process_request("Verify Logout")
        
        # Assertion
        self.assertEqual(response, expected_msg, "Workflow return mismatch.")

if __name__ == "__main__":
    unittest.main()