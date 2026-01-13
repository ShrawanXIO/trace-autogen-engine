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

class TestConfigIntegrity(unittest.TestCase):

    def setUp(self):
        # Preserve the original provider setting
        self.original_provider = config.LLM_PROVIDER

    def tearDown(self):
        # Restore the original provider setting
        config.LLM_PROVIDER = self.original_provider

    def test_configuration_structure(self):
        """
        Verifies that the configuration dictionaries (MODELS, TEMPERATURES)
        contain the necessary keys for the agents to function.
        """
        print("\n[Check 1] Verifying configuration structure...")
        
        required_roles = ["manager", "auditor", "author"]
        for role in required_roles:
            self.assertIn(role, config.TEMPERATURES, f"Missing Temperature setting for {role}")
            self.assertIn(role, config.MODELS["ollama"], f"Missing Ollama Model setting for {role}")

        # specific logic check: Auditor must be strict
        self.assertEqual(config.TEMPERATURES["auditor"], 0.0, "Auditor temperature must be 0.0 (strict).")
        print("Structure check passed.")

    def test_defensive_logic(self):
        """
        Verifies that the system raises specific errors when invalid
        roles or providers are requested.
        """
        print("[Check 2] Verifying defensive error handling...")
        
        # Test 1: Invalid Role request
        # We expect a ValueError containing "missing in" based on your config.py
        with self.assertRaisesRegex(ValueError, "missing in"):
            config.get_llm("non_existent_role")
            
        # Test 2: Invalid Provider request
        config.LLM_PROVIDER = "invalid_provider_name"
        with self.assertRaises(ValueError):
            config.get_llm("manager")
            
        print("Defensive logic check passed.")

    def test_ollama_power_flow(self):
        """
        Tests the full connection 'power flow' for Ollama.
        Selects provider -> Gets LLM -> Sends Message -> Verifies Response.
        """
        print("[Check 3] Testing Ollama connection flow...")
        self._verify_connection("ollama")

    def test_openai_power_flow(self):
        """
        Tests the full connection 'power flow' for OpenAI.
        Only runs if an API key appears to be present in the environment.
        """
        if os.getenv("OPENAI_API_KEY"):
            print("[Check 4] Testing OpenAI connection flow...")
            self._verify_connection("openai")
        else:
            print("[Check 4] Skipping OpenAI test (No API Key found).")

    def _verify_connection(self, provider):
        """
        Helper method to establish connection and verify data transmission.
        """
        config.LLM_PROVIDER = provider
        start_time = time.time()
        
        try:
            # 1. Configure and Connect
            llm = config.get_llm("manager")
            
            # 2. Send Data (The 'Power' Test)
            message = "If you are working, reply with 'I am working'."
            response = llm.invoke([HumanMessage(content=message)])
            reply = response.content.strip()
            
            duration = round(time.time() - start_time, 2)
            
            # 3. Validate Response
            if reply:
                print(f"   Success: {provider} responded in {duration}s.")
                print(f"   Response: '{reply}'")
            else:
                self.fail(f"   Failure: {provider} returned an empty response.")

        except Exception as e:
            error_msg = str(e)
            # Catch authentication errors specifically to give helpful feedback
            if "401" in error_msg or "Incorrect API key" in error_msg:
                print(f"   Authentication Failed: The OpenAI API key in .env is invalid.")
                print(f"   Tip: Ensure your .env file contains the actual key (sk-...), not Python code.")
            else:
                self.fail(f"   Connection failed for {provider}: {error_msg}")

if __name__ == '__main__':
    unittest.main(verbosity=2)