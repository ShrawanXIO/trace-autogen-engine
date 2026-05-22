import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# --- Path Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "src")
sys.path.append(src_path)

# We import the classes, but we will mock them in the tests
from agents.author import Author
from agents.auditor import Auditor

class TestTraceFeedbackLoop(unittest.TestCase):
    """
    Unit tests for the Feedback Loop logic.
    Uses Mocks to simulate Agent behavior, ensuring tests are fast and deterministic.
    """

    def setUp(self):
        """
        Runs before EACH test. Sets up the mock agents.
        """
        # Patch the classes so we don't make real LLM calls
        self.patcher_author = patch('agents.author.Author')
        self.patcher_auditor = patch('agents.auditor.Auditor')
        
        # Start patches
        self.MockAuthorClass = self.patcher_author.start()
        self.MockAuditorClass = self.patcher_auditor.start()

        # Create instances from the mocked classes
        self.mock_author_instance = self.MockAuthorClass.return_value
        self.mock_auditor_instance = self.MockAuditorClass.return_value

    def tearDown(self):
        patch.stopall()

    def run_feedback_loop(self, max_attempts=2):
        """
        Helper method: Encapsulates the loop logic you provided.
        This allows us to reuse the logic across different test scenarios.
        """
        topic = "Registration Scenarios"
        context = "Requirements..."
        feedback = ""
        previous_draft = ""
        attempt = 1
        approved = False

        while attempt <= max_attempts:
            # 1. Author writes
            draft = self.mock_author_instance.write(topic, context, feedback, previous_draft)
            previous_draft = draft

            # 2. Auditor reviews
            review = self.mock_auditor_instance.review(context, draft)

            # 3. Decision
            if "STATUS: APPROVED" in review:
                approved = True
                break
            else:
                feedback = review.replace("STATUS: REJECTED", "").strip()
                attempt += 1
        
        return approved, attempt

    def test_loop_immediate_approval(self):
        """
        Responsibility: Verify the loop stops immediately if the first draft is good.
        """
        # --- Setup Behavior ---
        self.mock_author_instance.write.return_value = "Perfect Draft"
        self.mock_auditor_instance.review.return_value = "STATUS: APPROVED"

        # --- Execution ---
        is_approved, attempts = self.run_feedback_loop()

        # --- Assertion ---
        self.assertTrue(is_approved, "Should be approved.")
        self.assertEqual(attempts, 1, "Should finish in exactly 1 attempt.")

    def test_loop_correction_flow(self):
        """
        Responsibility: Verify the loop retries exactly once if the first draft is rejected.
        """
        # --- Setup Behavior (Sequence of events) ---
        # Author: Returns "Bad Draft" first, then "Fixed Draft"
        self.mock_author_instance.write.side_effect = ["Bad Draft", "Fixed Draft"]
        
        # Auditor: Returns "REJECTED" first, then "APPROVED"
        self.mock_auditor_instance.review.side_effect = ["STATUS: REJECTED Fix bugs", "STATUS: APPROVED"]

        # --- Execution ---
        is_approved, attempts = self.run_feedback_loop()

        # --- Assertion ---
        self.assertTrue(is_approved, "Should eventually be approved.")
        self.assertEqual(attempts, 2, "Should have taken 2 attempts (1 retry).")

    def test_loop_failure_max_attempts(self):
        """
        Responsibility: Verify the loop stops and reports failure after max attempts.
        """
        # --- Setup Behavior ---
        # Always bad
        self.mock_author_instance.write.return_value = "Bad Draft"
        self.mock_auditor_instance.review.return_value = "STATUS: REJECTED"

        # --- Execution ---
        is_approved, attempts = self.run_feedback_loop(max_attempts=2)

        # --- Assertion ---
        self.assertFalse(is_approved, "Should NOT be approved.")
        self.assertGreater(attempts, 2, "Should have exhausted attempts (counter increments before exit).")

if __name__ == "__main__":
    unittest.main()