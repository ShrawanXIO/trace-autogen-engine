import sys
import os
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Guard: skip the entire module if the vector store doesn't exist or
# Ollama is unreachable — prevents CI failures when infra is not running.
VECTOR_STORE_PATH = os.path.join(os.path.dirname(__file__), "data", "vector_store")
_infra_available = os.path.exists(VECTOR_STORE_PATH)

try:
    import langchain_chroma  # noqa: F401
    _packages_available = True
except ImportError:
    _packages_available = False

try:
    import requests
    _ollama_up = requests.get("http://localhost:11434", timeout=2).status_code == 200
except Exception:
    _ollama_up = False

SKIP_REASON = (
    "Integration test requires: ChromaDB vector store on disk, "
    "langchain-chroma package installed, and a running Ollama instance"
)
_can_run = _infra_available and _packages_available and _ollama_up


@unittest.skipUnless(_can_run, SKIP_REASON)
class TestArchivistIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from agents.archivist import Archivist
        cls.agent = Archivist()

    def test_initializes_successfully(self):
        self.assertIsNotNone(self.agent)

    def test_returns_string_response(self):
        response = self.agent.ask("What is the main topic of the document?")
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

    def test_empty_query_returns_guidance(self):
        response = self.agent.ask("")
        self.assertIn("provide a query", response.lower())

    def test_unknown_topic_does_not_hallucinate(self):
        response = self.agent.ask("Tell me about quantum teleportation protocols")
        self.assertIn("could not find", response.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
