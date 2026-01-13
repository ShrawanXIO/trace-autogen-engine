import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage 

# --- ROBUST PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "src")
sys.path.append(src_path)

from agents.author import Author

class TestAuthorIDCompliance(unittest.TestCase):

    def setUp(self):
        self.patcher_llm = patch('agents.author.config.get_llm')
        self.mock_get_llm = self.patcher_llm.start()
        
        # Create the Mock LLM
        self.mock_llm_instance = MagicMock()
        self.mock_get_llm.return_value = self.mock_llm_instance
        
        # Initialize Author
        self.author = Author()

    def tearDown(self):
        patch.stopall()

    def test_prompt_construction_includes_id(self):
        """
        Responsibility: Verify the Author sends the correct ID to the LLM.
        """
        # [FIX 1] Set return value on the Mock OBJECT, not just .invoke
        # LangChain treats Mocks as functions and calls them directly via __call__
        self.mock_llm_instance.return_value = AIMessage(content="Draft Created.")
        
        # Also set it on invoke just to be safe (coverage for both paths)
        self.mock_llm_instance.invoke.return_value = AIMessage(content="Draft Created.")

        target_id = "TC_FIXED_888"
        
        # Action
        self.author.write(topic=f"{target_id}: Logout", context="Ctx")

        # [FIX 2] Inspect call_args on the instance itself (for __call__)
        # If the code used .invoke(), mock_llm_instance.invoke.call_args would work.
        # Since it likely used __call__, we check the instance.
        if self.mock_llm_instance.call_args:
            args, _ = self.mock_llm_instance.call_args
        else:
            # Fallback: Check if .invoke was called
            args, _ = self.mock_llm_instance.invoke.call_args

        sent_data = str(args) 

        self.assertIn(target_id, sent_data, 
                      "FAIL: The specific ID was not found in the prompt sent to the LLM.")

    def test_output_passthrough(self):
        """
        Responsibility: Verify the Author returns the LLM's text.
        """
        target_id = "TC_FIXED_888"
        expected_output = f"Test Case ID: {target_id}\nStep 1: Click Logout..."
        
        # [FIX] Set return value on the Mock OBJECT (handling __call__)
        valid_response = AIMessage(content=expected_output)
        self.mock_llm_instance.return_value = valid_response
        self.mock_llm_instance.invoke.return_value = valid_response

        # Action
        draft = self.author.write(topic=f"{target_id}: Logout", context="Ctx")

        # Assertion
        self.assertIn(target_id, draft, "FAIL: Author output dropped the ID.")
        self.assertEqual(draft, expected_output, "FAIL: Output didn't match the LLM response.")

if __name__ == "__main__":
    unittest.main(verbosity=2)