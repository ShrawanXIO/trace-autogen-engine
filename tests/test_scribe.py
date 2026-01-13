import sys
import os
import csv
import unittest

# --- ROBUST PATH SETUP ---
# 1. Get current directory (tests/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 2. Go UP one level to root, then DOWN into src
src_path = os.path.join(current_dir, "..", "src")
# 3. Add to Python Path
sys.path.append(src_path)

from agents.scribe import Scribe

class TestScribe(unittest.TestCase):
    def test_scribe_flow(self):
        print("--- Starting Scribe Agent Test (Smart Excel Mode) ---")

        # 1. Initialize Scribe
        try:
            # Note: This will try to connect to Ollama ("ministral-3:14b-cloud")
            scribe = Scribe()
            print("✅ Scribe initialized successfully.")
        except Exception as e:
            print(f"❌ Failed to initialize Scribe. Is Ollama running? Error: {e}")
            return

        # 2. Simulate Input Data (Raw text from Author)
        dummy_content = """
        Test Case ID: TC_LOGIN_001
        Title: Verify User Login
        Pre-conditions: User is on the login page.
        Steps:
        1. Enter valid username.
        2. Enter valid password.
        3. Click the 'Login' button.
        Expected Result: 
        1. Username field accepts input.
        2. Password field is masked.
        3. User is redirected to the Dashboard.
        """

        print(f"\n[Test] Sending Raw Text to Scribe...")
        print(">>> Scribe is processing (Invoking LLM for JSON formatting)...")

        # 3. Execution
        # This might take a few seconds as it calls the local AI model
        result = scribe.save(dummy_content)

        print(f"\n[Result] {result}")

        # 4. Verification
        if "Success" in result:
            # Extract filepath from the result string
            # Expected format: "Success. Multi-Row Excel file saved: /path/to/file.csv"
            try:
                filepath = result.split(": ")[1].strip()
            except IndexError:
                print("❌ FAIL: Could not parse filepath from result string.")
                return

            if os.path.exists(filepath):
                print(f"✅ PASS: File created at {filepath}")
                
                # 5. Check Content Structure (Verify it's the new Excel format)
                try:
                    with open(filepath, 'r', encoding='utf-8-sig') as f:
                        reader = csv.reader(f)
                        headers = next(reader)
                        
                        # Verify Headers
                        expected_headers = ["ID", "Title", "Action", "Expected Result"]
                        if headers == expected_headers:
                            print(f"✅ PASS: CSV Headers match Smart Excel format.")
                        else:
                            print(f"⚠️ WARNING: CSV Headers look different: {headers}")

                        # Print Preview of data
                        print("\n--- CSV Content Preview (First 5 Lines) ---")
                        print(f"Row 1 (Headers): {headers}")
                        for i, row in enumerate(reader):
                            if i < 5: print(f"Row {i+2}: {row}")
                        print("-------------------------------------------")

                except Exception as e:
                    print(f"❌ FAIL: Could not read CSV file. Error: {e}")
            else:
                print(f"❌ FAIL: File not found on disk.")
        else:
            print(f"❌ FAIL: Scribe reported error.")

if __name__ == "__main__":
           # test_scribe_flow()
    unittest.main()