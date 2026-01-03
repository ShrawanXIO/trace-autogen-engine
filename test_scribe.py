import sys
import os

# Add 'src' to python path to find the agents
sys.path.append(os.path.join(os.getcwd(), "src"))

from agents.scribe import Scribe

def run_test():
    print("--- Starting Scribe Isolation Test ---")

    # 1. Initialize Scribe
    try:
        scribe = Scribe()
    except Exception as e:
        print(f"Failed to initialize Scribe: {e}")
        return

    # 2. Simulate raw content from the Author
    # This is how the text looks before formatting
    dummy_content = """
    Here are the test cases you asked for:

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

    print("\n[Input] Raw Text provided to Scribe:")
    print(dummy_content)
    print("-" * 30)

    # 3. Request Save
    print("\n[Action] Scribe is processing and saving...")
    result = scribe.save(dummy_content)
    
    print(f"\n[Result] {result}")

    # 4. Verification Check
    # We check if the file actually exists in data/outputs
    if "Success" in result:
        # Extract filepath from the result string
        filepath = result.split(": ")[1].strip()
        
        if os.path.exists(filepath):
            print(f"Verified: File actually exists on disk at {filepath}")
            
            # Optional: Read the first few lines to check CSV format
            with open(filepath, 'r') as f:
                print("\n--- File Content Preview ---")
                print(f.read())
                print("----------------------------")
        else:
            print("Error: The Scribe said success, but I cannot find the file.")

if __name__ == "__main__":
    run_test()