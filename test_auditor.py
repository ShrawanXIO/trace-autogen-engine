import sys
import os
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.join(os.getcwd(), "src"))

_ollama_up = False
try:
    import requests
    _ollama_up = requests.get("http://localhost:11434", timeout=2).status_code == 200
except Exception:
    pass

INTEGRATION_SKIP = "Integration test requires a running Ollama instance"


class MockArchivist:
    def ask(self, query):
        return "Documentation Rule: The system requires a password of at least 10 characters."


class TestAuditorUnit(unittest.TestCase):
    """Unit tests - fully mocked, no Ollama required."""

    def setUp(self):
        from agents.auditor import Auditor
        self.auditor = Auditor(archivist_agent=MockArchivist())
        # Replace the chain with a controllable mock
        self.auditor.chain = MagicMock()

    def _set_response(self, text):
        self.auditor.chain.invoke.return_value = text

    def test_approved_decision_is_returned(self):
        self._set_response(
            "--- ANALYSIS ---\nAll scenarios covered.\n--- END ANALYSIS ---\n"
            "STATUS: APPROVED\nFEEDBACK: Looks good."
        )
        result = self.auditor.review("Verify login", "TC_01: Login test")
        self.assertIn("STATUS: APPROVED", result)

    def test_rejected_decision_is_returned(self):
        self._set_response(
            "--- ANALYSIS ---\nExpected result is wrong.\n--- END ANALYSIS ---\n"
            "STATUS: REJECTED\nFEEDBACK: Change expected result to show error message."
        )
        result = self.auditor.review("Verify login", "TC_01: Login test")
        self.assertIn("STATUS: REJECTED", result)
        self.assertIn("FEEDBACK", result)

    def test_analysis_section_is_stripped_from_output(self):
        self._set_response(
            "--- ANALYSIS ---\nInternal reasoning.\n--- END ANALYSIS ---\n"
            "STATUS: APPROVED"
        )
        result = self.auditor.review("requirement", "draft")
        self.assertNotIn("ANALYSIS", result)
        self.assertNotIn("Internal reasoning", result)

    def test_missing_inputs_returns_error(self):
        result = self.auditor.review("", "some draft")
        self.assertIn("Error", result)

    def test_review_passes_correct_inputs_to_chain(self):
        self._set_response("STATUS: APPROVED")
        self.auditor.review("Login requirement", "TC_01 draft")
        call_kwargs = self.auditor.chain.invoke.call_args[0][0]
        self.assertEqual(call_kwargs["requirement"], "Login requirement")
        self.assertEqual(call_kwargs["test_cases"], "TC_01 draft")


@unittest.skipUnless(_ollama_up, INTEGRATION_SKIP)
class TestAuditorIntegration(unittest.TestCase):
    """Integration tests - require a running Ollama instance."""

    @classmethod
    def setUpClass(cls):
        from agents.auditor import Auditor
        cls.auditor = Auditor(archivist_agent=MockArchivist())

    def test_bad_draft_is_rejected(self):
        requirement = "Verify login with 5 character password."
        bad_draft = (
            "Test Case ID: TC_01\n"
            "Title: Login Short Password\n"
            "Steps: Enter '12345', Click Login.\n"
            "Expected Result: Login Successful."
        )
        result = self.auditor.review(requirement, bad_draft)
        self.assertIn("REJECTED", result)

    def test_correct_draft_is_approved(self):
        requirement = "Verify login with 5 character password."
        good_draft = (
            "Test Case ID: TC_01\n"
            "Title: Login Short Password\n"
            "Steps: Enter '12345', Click Login.\n"
            "Expected Result: System displays 'Password too short' error."
        )
        result = self.auditor.review(requirement, good_draft)
        self.assertIn("APPROVED", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
