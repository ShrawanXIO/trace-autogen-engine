import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(os.path.join(os.getcwd(), "src"))

try:
    import langchain_core.prompts      # noqa: F401
    import langchain_core.output_parsers  # noqa: F401
    import langchain_ollama             # noqa: F401
except ImportError:
    pass

_ollama_up = False
try:
    import requests
    _ollama_up = requests.get("http://localhost:11434", timeout=2).status_code == 200
except Exception:
    pass

INTEGRATION_SKIP = "Integration test requires a running Ollama instance"

REQUIREMENT = """
Create test cases for a 'Registration Page'.
It MUST include:
1. Valid email format check.
2. Password strength validation (min 8 chars, 1 symbol).
3. A 'Terms of Service' checkbox that must be checked.
"""


class MockArchivist:
    def ask(self, query):
        return "Rule: Password must be at least 8 characters with 1 symbol."


class TestFeedbackLoopUnit(unittest.TestCase):
    """
    Unit tests for the Author -> Auditor feedback loop logic.
    All LLM calls are mocked - no Ollama required.
    """

    def _make_author(self, responses):
        from agents.author import Author
        author = Author()
        author.chain = MagicMock()
        author.chain.invoke.side_effect = responses
        return author

    def _make_auditor(self, responses):
        from agents.auditor import Auditor
        auditor = Auditor(archivist_agent=MockArchivist())
        auditor.chain = MagicMock()
        auditor.chain.invoke.side_effect = responses
        return auditor

    @patch("agents.author.ChatOllama")
    @patch("agents.auditor.ChatOllama")
    def test_loop_stops_on_first_approval(self, MockAuditorLLM, MockAuthorLLM):
        author = self._make_author(["TC_01: Valid email test"])
        auditor = self._make_auditor([
            "--- ANALYSIS ---\nAll good.\n--- END ANALYSIS ---\nSTATUS: APPROVED\nFEEDBACK: None"
        ])

        draft = author.write(REQUIREMENT, context="")
        review = auditor.review(REQUIREMENT, draft)

        self.assertIn("STATUS: APPROVED", review)
        self.assertEqual(author.chain.invoke.call_count, 1)
        self.assertEqual(auditor.chain.invoke.call_count, 1)

    @patch("agents.author.ChatOllama")
    @patch("agents.auditor.ChatOllama")
    def test_loop_retries_on_rejection_then_approves(self, MockAuditorLLM, MockAuthorLLM):
        author = self._make_author([
            "TC_01: Initial draft",
            "TC_01: Revised draft with fix"
        ])
        auditor = self._make_auditor([
            "--- ANALYSIS ---\nMissing TOS check.\n--- END ANALYSIS ---\nSTATUS: REJECTED\nFEEDBACK: Add TOS checkbox test.",
            "--- ANALYSIS ---\nAll scenarios covered.\n--- END ANALYSIS ---\nSTATUS: APPROVED\nFEEDBACK: None"
        ])

        feedback = ""
        previous_draft = ""
        approved = False

        for attempt in range(1, 4):
            draft = author.write(REQUIREMENT, context="", feedback=feedback, previous_draft=previous_draft)
            previous_draft = draft
            review = auditor.review(REQUIREMENT, draft)

            if "STATUS: APPROVED" in review:
                approved = True
                break
            feedback = review

        self.assertTrue(approved)
        self.assertEqual(author.chain.invoke.call_count, 2)
        self.assertEqual(auditor.chain.invoke.call_count, 2)

    @patch("agents.author.ChatOllama")
    @patch("agents.auditor.ChatOllama")
    def test_feedback_is_passed_to_author_on_retry(self, MockAuditorLLM, MockAuthorLLM):
        rejection_feedback = "STATUS: REJECTED\nFEEDBACK: Add TOS checkbox test."
        author = self._make_author(["Draft 1", "Draft 2"])
        auditor = self._make_auditor([
            "--- ANALYSIS ---\n\n--- END ANALYSIS ---\n" + rejection_feedback,
            "--- ANALYSIS ---\n\n--- END ANALYSIS ---\nSTATUS: APPROVED"
        ])

        feedback = ""
        previous_draft = ""

        for _ in range(3):
            draft = author.write(REQUIREMENT, context="", feedback=feedback, previous_draft=previous_draft)
            previous_draft = draft
            review = auditor.review(REQUIREMENT, draft)
            if "STATUS: APPROVED" in review:
                break
            feedback = review

        # On the second author call, feedback must be the rejection message
        second_call_args = author.chain.invoke.call_args_list[1][0][0]
        self.assertIn("REJECTED", second_call_args["feedback"])

    @patch("agents.author.ChatOllama")
    @patch("agents.auditor.ChatOllama")
    def test_loop_exits_after_max_attempts(self, MockAuditorLLM, MockAuthorLLM):
        max_attempts = 3
        author = self._make_author(["Draft"] * max_attempts)
        auditor = self._make_auditor([
            "--- ANALYSIS ---\n\n--- END ANALYSIS ---\nSTATUS: REJECTED\nFEEDBACK: Still wrong."
        ] * max_attempts)

        attempts = 0
        for attempt in range(1, max_attempts + 1):
            draft = author.write(REQUIREMENT, context="", feedback="", previous_draft="")
            review = auditor.review(REQUIREMENT, draft)
            attempts += 1
            if "STATUS: APPROVED" in review:
                break

        self.assertEqual(attempts, max_attempts)


@unittest.skipUnless(_ollama_up, INTEGRATION_SKIP)
class TestFeedbackLoopIntegration(unittest.TestCase):
    """Integration tests - require a running Ollama instance."""

    @classmethod
    def setUpClass(cls):
        from unittest.mock import MagicMock
        if isinstance(sys.modules.get("langchain_ollama"), MagicMock):
            raise unittest.SkipTest("langchain_ollama is stubbed by another test module")
        from agents.author import Author
        from agents.auditor import Auditor
        cls.author = Author()
        cls.auditor = Auditor(archivist_agent=MockArchivist())

    def test_full_loop_produces_non_empty_output(self):
        feedback = ""
        previous_draft = ""
        final_draft = ""

        for attempt in range(1, 4):
            draft = self.author.write(REQUIREMENT, context="", feedback=feedback, previous_draft=previous_draft)
            previous_draft = draft
            review = self.auditor.review(REQUIREMENT, draft)

            if "STATUS: APPROVED" in review:
                final_draft = draft
                break
            feedback = review

        if not final_draft:
            final_draft = previous_draft

        self.assertIsInstance(final_draft, str)
        self.assertGreater(len(final_draft), 50)


if __name__ == "__main__":
    unittest.main(verbosity=2)
