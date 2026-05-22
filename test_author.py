import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(os.path.join(os.getcwd(), "src"))

# Pre-import real langchain submodules so later test files that stub them
# (with `if _mod not in sys.modules`) do not replace the real packages.
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


class TestAuthorUnit(unittest.TestCase):
    """Unit tests - fully mocked, no Ollama required."""

    @patch("agents.author.ChatOllama")
    def setUp(self, MockLLM):
        from agents.author import Author
        self.MockLLM = MockLLM
        self.mock_llm_instance = MockLLM.return_value
        self.agent = Author()

    def _set_response(self, text):
        self.agent.chain = MagicMock()
        self.agent.chain.invoke.return_value = text

    def test_write_returns_content_when_no_thoughts_section(self):
        self._set_response("Test Case ID: TC_01\nTitle: Login\nExpected Result: Success")
        result = self.agent.write("Login scenario", context="Some rules")
        self.assertIn("TC_01", result)

    def test_write_strips_thoughts_section(self):
        self._set_response(
            "--- THOUGHTS ---\nStrategy notes here\n--- END THOUGHTS ---\n"
            "Test Case ID: TC_01\nTitle: Login"
        )
        result = self.agent.write("Login scenario", context="Some rules")
        self.assertNotIn("THOUGHTS", result)
        self.assertIn("TC_01", result)

    def test_write_passes_feedback_and_previous_draft(self):
        self._set_response("Test Case ID: TC_01")
        self.agent.write(
            "Login scenario",
            context="Some rules",
            feedback="Add cleanup step",
            previous_draft="Old draft"
        )
        call_kwargs = self.agent.chain.invoke.call_args[0][0]
        self.assertEqual(call_kwargs["feedback"], "Add cleanup step")
        self.assertEqual(call_kwargs["previous_draft"], "Old draft")

    def test_write_defaults_none_feedback_to_literal_none(self):
        self._set_response("Test Case ID: TC_01")
        self.agent.write("Login scenario", context="rules")
        call_kwargs = self.agent.chain.invoke.call_args[0][0]
        self.assertEqual(call_kwargs["feedback"], "None")

    def test_write_empty_topic_returns_guidance(self):
        result = self.agent.write("", context="rules")
        self.assertIn("provide a topic", result.lower())

    def test_write_with_feedback_invokes_chain_once(self):
        self._set_response("TC_01: Revised test")
        result = self.agent.write("topic", context="rules", feedback="Fix step 2")
        self.agent.chain.invoke.assert_called_once()
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


@unittest.skipUnless(_ollama_up, INTEGRATION_SKIP)
class TestAuthorIntegration(unittest.TestCase):
    """Integration tests - require a running Ollama instance."""

    @classmethod
    def setUpClass(cls):
        from unittest.mock import MagicMock
        if isinstance(sys.modules.get("langchain_ollama"), MagicMock):
            raise unittest.SkipTest("langchain_ollama is stubbed by another test module")
        from agents.author import Author
        cls.agent = Author()

    def test_first_draft_returns_non_empty_string(self):
        result = self.agent.write("Login with invalid password", context="")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 50)

    def test_feedback_revision_returns_non_empty_string(self):
        draft = self.agent.write("Login with invalid password", context="")
        revised = self.agent.write(
            "Login with invalid password",
            context="",
            feedback="Add a cleanup step to clear browser cache.",
            previous_draft=draft
        )
        self.assertIsInstance(revised, str)
        self.assertGreater(len(revised), 50)


if __name__ == "__main__":
    unittest.main(verbosity=2)
