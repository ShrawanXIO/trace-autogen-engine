import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(os.path.join(os.getcwd(), "src"))

_ollama_up = False
try:
    import requests
    _ollama_up = requests.get("http://localhost:11434", timeout=2).status_code == 200
except Exception:
    pass

INTEGRATION_SKIP = "Integration test requires a running Ollama instance"

DUMMY_DRAFT = """
Test Case ID: TC_001
Title: Verify Login Success
Pre-conditions: User has valid account
Steps:
1. Enter username
2. Enter password
3. Click Login
Expected Result: Dashboard loads

Test Case ID: TC_002
Title: Verify Login Failure
Pre-conditions: User is on login page
Steps:
1. Enter invalid username
2. Click Login
Expected Result: Error message appears
"""

EXPECTED_CSV = (
    'ID,Title,Pre-conditions,Steps,Expected Result\n'
    'TC_001,Verify Login Success,User has valid account,"1. Enter username 2. Enter password 3. Click Login",Dashboard loads\n'
    'TC_002,Verify Login Failure,User is on login page,"1. Enter invalid username 2. Click Login",Error message appears'
)


class TestScribeUnit(unittest.TestCase):
    """Unit tests - fully mocked, no Ollama required."""

    @patch("agents.scribe.ChatOllama")
    def setUp(self, MockLLM):
        from agents.scribe import Scribe
        self.scribe = Scribe()
        self.scribe.chain = MagicMock()

    def tearDown(self):
        # Clean up any files written during tests
        output_dir = os.path.join(os.getcwd(), "data", "outputs")
        for f in os.listdir(output_dir) if os.path.exists(output_dir) else []:
            if f.startswith("test_cases_") and f.endswith(".csv"):
                try:
                    os.remove(os.path.join(output_dir, f))
                except OSError:
                    pass

    def test_save_creates_csv_file_on_disk(self):
        self.scribe.chain.invoke.return_value = EXPECTED_CSV
        result = self.scribe.save(DUMMY_DRAFT)
        self.assertIn("Success", result)
        filepath = result.split(": ", 1)[1].strip()
        self.assertTrue(os.path.exists(filepath), f"File not found: {filepath}")

    def test_csv_file_contains_header_row(self):
        self.scribe.chain.invoke.return_value = EXPECTED_CSV
        result = self.scribe.save(DUMMY_DRAFT)
        filepath = result.split(": ", 1)[1].strip()
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("ID,Title,Pre-conditions,Steps,Expected Result", content)

    def test_markdown_fences_are_stripped(self):
        self.scribe.chain.invoke.return_value = "```csv\n" + EXPECTED_CSV + "\n```"
        result = self.scribe.save(DUMMY_DRAFT)
        filepath = result.split(": ", 1)[1].strip()
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("```", content)

    def test_empty_content_returns_error(self):
        result = self.scribe.save("")
        self.assertIn("Error", result)

    def test_output_directory_is_created_if_missing(self):
        output_dir = os.path.join(os.getcwd(), "data", "outputs")
        self.assertTrue(os.path.exists(output_dir))


@unittest.skipUnless(_ollama_up, INTEGRATION_SKIP)
class TestScribeIntegration(unittest.TestCase):
    """Integration tests - require a running Ollama instance."""

    @classmethod
    def setUpClass(cls):
        from agents.scribe import Scribe
        cls.scribe = Scribe()

    def test_save_produces_valid_csv_file(self):
        result = self.scribe.save(DUMMY_DRAFT)
        self.assertIn("Success", result)
        filepath = result.split(": ", 1)[1].strip()
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        # Header may be quoted ("ID","Title",...) or unquoted (ID,Title,...) depending on the LLM
        self.assertRegex(content, r'"?ID"?,\s*"?Title"?')


if __name__ == "__main__":
    unittest.main(verbosity=2)
