import sys
import os
import unittest
import time
from langchain_core.messages import HumanMessage

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "src")
sys.path.append(src_path)

try:
    import config
except ImportError:
    print("Critical Error: Could not find config.py in src directory.")
    sys.exit(1)

class TestConfigStructure(unittest.TestCase):
    """
    Responsibilities: Verify the STATIC configuration dictionaries (Models, Temperatures).
    No API calls here.
    """

    def test_manager_settings_exist(self):
        self.assertIn("manager", config.TEMPERATURES)
        self.assertIn("manager", config.MODELS["ollama"])

    def test_auditor_settings_exist(self):
        self.assertIn("auditor", config.TEMPERATURES)
        self.assertIn("auditor", config.MODELS["ollama"])

    def test_auditor_strictness(self):
        """Responsibility: Ensure Auditor is set to 0.0 (Strict mode)."""
        self.assertEqual(config.TEMPERATURES["auditor"], 0.0)


class TestConfigErrorHandling(unittest.TestCase):
    """
    Responsibilities: Verify the system correctly REJECTS invalid inputs.
    """

    def setUp(self):
        self.original_provider = config.LLM_PROVIDER

    def tearDown(self):
        config.LLM_PROVIDER = self.original_provider

    def test_invalid_role_raises_value_error(self):
        """Responsibility: Ensure requesting a made-up role (e.g., 'janitor') fails gracefully."""
        with self.assertRaisesRegex(ValueError, "missing in"):
            config.get_llm("non_existent_role")

    def test_invalid_provider_raises_value_error(self):
        """Responsibility: Ensure setting an unknown provider (e.g., 'anthropic') fails gracefully."""
        config.LLM_PROVIDER = "invalid_provider_name"
        with self.assertRaises(ValueError):
            config.get_llm("manager")


class TestLiveConnections(unittest.TestCase):
    """
    Responsibilities: Verify LIVE connections to the AI providers.
    These are 'Integration Tests' that actually touch the network/local server.
    """

    def setUp(self):
        self.original_provider = config.LLM_PROVIDER

    def tearDown(self):
        config.LLM_PROVIDER = self.original_provider

    def _ping_provider(self, provider_name):
        """Helper to reduce code duplication."""
        config.LLM_PROVIDER = provider_name
        llm = config.get_llm("manager")
        message = "Ping"
        response = llm.invoke([HumanMessage(content=message)])
        return response.content.strip()

    def test_ollama_connectivity(self):
        """Responsibility: Ensure local Ollama instance is reachable."""
        try:
            reply = self._ping_provider("ollama")
            self.assertTrue(len(reply) > 0, "Ollama returned empty response")
        except Exception as e:
            self.fail(f"Ollama Connection Failed: {e}")

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Skipping: No OpenAI API Key found")
    def test_openai_connectivity(self):
        """Responsibility: Ensure OpenAI API is reachable (only if key exists)."""
        try:
            reply = self._ping_provider("openai")
            self.assertTrue(len(reply) > 0, "OpenAI returned empty response")
        except Exception as e:
            self.fail(f"OpenAI Connection Failed: {e}")

if __name__ == '__main__':
    unittest.main()