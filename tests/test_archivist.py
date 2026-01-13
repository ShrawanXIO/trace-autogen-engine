import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# --- ROBUST PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "src")
sys.path.append(src_path)

from agents.archivist import Archivist

class TestArchivistLogic(unittest.TestCase):
    """
    Tests the CORE LOGIC of the Archivist.
    We mock the 'Retriever' (Database Connection) to ensure we test the logic,
    not the actual files on disk.
    """

    def setUp(self):
        """Runs before EACH test."""
        # 1. Patch Config
        self.patcher_config = patch('agents.archivist.config')
        self.patcher_config.start()
        
        # 2. Patch 'get_retriever'
        self.patcher_get_retriever = patch('agents.archivist.get_retriever')
        self.mock_get_retriever = self.patcher_get_retriever.start()

        # 3. Setup the Mock Retriever Instance
        self.mock_retriever_instance = MagicMock()
        self.mock_get_retriever.return_value = self.mock_retriever_instance

        # Initialize the Agent
        self.agent = Archivist()

    def tearDown(self):
        patch.stopall()

    def test_01_initialization(self):
        """Responsibility: Verify the Archivist starts up and connects to (Mock) DB."""
        self.assertIsNotNone(self.agent, "Archivist failed to initialize.")
        self.assertIsNotNone(self.agent.retriever, "Archivist did not load the retriever.")
        print("✅ [Test 1] Archivist initialized.")

    def test_02_fetch_existing_data(self):
        """Responsibility: If the System finds data, return it explicitly."""
        # --- SETUP ---
        mock_doc = MagicMock()
        mock_doc.page_content = "The password policy requires 10 characters."
        
        # Tell Mock DB to return a document
        self.mock_retriever_instance.invoke.return_value = [mock_doc]

        # --- ACTION ---
        response = self.agent.ask("What is the password policy?")

        # --- ASSERTION ---
        self.assertEqual(response, "The password policy requires 10 characters.")
        print("✅ [Test 2] Archivist correctly returned existing data.")

    def test_03_handle_missing_data(self):
        """Responsibility: If data is NOT in archives, explicitly say 'Test case not found'."""
        # --- SETUP ---
        # Tell Mock DB to return EMPTY list (Nothing found)
        self.mock_retriever_instance.invoke.return_value = []

        # --- ACTION ---
        response = self.agent.ask("Verify Login with Google")

        # --- ASSERTION ---
        expected_msg = "Test case not found in the archives."
        
        self.assertEqual(response, expected_msg, 
            f"FAIL: Expected '{expected_msg}' but got '{response}'")
        
        print(f"✅ [Test 3] Archivist correctly responded: '{response}'")

if __name__ == "__main__":
    unittest.main(verbosity=2)