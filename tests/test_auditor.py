import sys
import os
import unittest
from unittest.mock import MagicMock, patch
# [CRITICAL IMPORT] Required for LangChain mocks
from langchain_core.messages import AIMessage

# --- ROBUST PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "src")
sys.path.append(src_path)

from agents.auditor import Auditor

# --- MOCK ARCHIVIST ---
class MockArchivist:
    """Fake Archivist to satisfy the Auditor's dependency."""
    def ask(self, query):
        return "Rule: System requires valid login credentials."

class TestAuditorGuardrails(unittest.TestCase):
    """
    Tests the Auditor's role as the system 'Guardrail'.
    Responsibility: Ensure the Author only writes what was asked, nothing more, nothing less.
    """

    def setUp(self):
        """Runs before EACH test. Sets up the mock Auditor."""
        self.patcher_llm = patch('agents.auditor.config.get_llm')
        self.mock_get_llm = self.patcher_llm.start()

        # Create Mock LLM
        self.mock_llm_instance = MagicMock()
        self.mock_get_llm.return_value = self.mock_llm_instance

        # Initialize Auditor
        self.auditor = Auditor(archivist_agent=MockArchivist())

    def tearDown(self):
        patch.stopall()

    def test_01_approve_matching_scenario(self):
        """
        RESPONSIBILITY: VALIDATION
        If the Author's output matches the User's input scenario perfectly,
        the Auditor should APPROVE it.
        """
        user_scenario = "Verify valid login with correct username and password."
        author_draft = "Title: Verify valid login..."

        # [FIX] Set return value for BOTH direct calls and .invoke()
        valid_response = AIMessage(content="STATUS: APPROVED")
        self.mock_llm_instance.return_value = valid_response
        self.mock_llm_instance.invoke.return_value = valid_response

        # --- ACTION ---
        result = self.auditor.review(user_scenario, author_draft)

        # --- ASSERTION ---
        self.assertIn("APPROVED", result)
        print("✅ [Test 1] Auditor APPROVED a correct match.")

    def test_02_reject_wrong_id(self):
        """
        RESPONSIBILITY: ID COMPLIANCE
        If the Author hallucinated a new ID, the Auditor MUST reject it.
        """
        user_scenario = "TC_LEGACY_500: Verify Search Functionality"
        bad_draft = "Test Case ID: TC_NEW_001..."

        # [FIX] Set return value for BOTH direct calls and .invoke()
        msg = "STATUS: REJECTED\nReason: ID Mismatch. Expected TC_LEGACY_500, found TC_NEW_001."
        reject_response = AIMessage(content=msg)
        self.mock_llm_instance.return_value = reject_response
        self.mock_llm_instance.invoke.return_value = reject_response

        # --- ACTION ---
        result = self.auditor.review(user_scenario, bad_draft)

        # --- ASSERTION ---
        self.assertIn("REJECTED", result)
        self.assertIn("ID Mismatch", result)
        print("✅ [Test 2] Auditor REJECTED an incorrect Test Case ID.")

    def test_03_reject_hallucinated_negative_scenario(self):
        """
        RESPONSIBILITY: SCOPE CREEP (NO HALLUCINATIONS)
        The Auditor MUST reject extra unrequested work.
        """
        user_scenario = "Verify Login Success."
        hallucinated_draft = "Title: Verify Login Success... Title: Verify Invalid Login..."

        # [FIX] Set return value for BOTH direct calls and .invoke()
        msg = "STATUS: REJECTED\nReason: Hallucination detected. Draft includes scenarios not requested by the user."
        reject_response = AIMessage(content=msg)
        self.mock_llm_instance.return_value = reject_response
        self.mock_llm_instance.invoke.return_value = reject_response

        # --- ACTION ---
        result = self.auditor.review(user_scenario, hallucinated_draft)

        # --- ASSERTION ---
        self.assertIn("REJECTED", result)
        self.assertIn("Hallucination", result)
        print("✅ [Test 3] Auditor REJECTED unrequested negative scenarios.")

if __name__ == "__main__":
    unittest.main(verbosity=2)