import sys
from dotenv import load_dotenv
from agents.manager import Manager

# Load environment variables
load_dotenv()

def main():
    print("Trace STLC Engine Starting...")
    
    # 1. Initialize the Boss (Manager)
    # The Manager will automatically hire the Archivist, Author, Auditor, and Scribe.
    try:
        manager = Manager()
        print("System Ready. (Manager is listening)")
    except Exception as e:
        print(f"Critical System Error: {e}")
        sys.exit(1)

    # 2. The Simple Conversation Loop
    while True:
        print("\n" + "="*50)
        # Unified Input: No more 'ask/write' modes. Just type!
        user_input = input("Enter Scenario, Question, or 'exit': ")
        
        # Exit Condition
        if user_input.strip().lower() in ["exit", "quit"]:
            print("Exiting...")
            break

        if not user_input.strip():
            continue

        # 3. Delegate Everything to the Manager
        # The Manager will decide:
        #  - "Do I need to sync files?" (Smart Sync)
        #  - "Is this a question or a task?" (Intent Classification)
        #  - "Do I need to check for duplicates?" (Gatekeeper)
        response = manager.process_request(user_input)
        
        # 4. Show Result
        print("\n" + "-"*30)
        print("FINAL RESULT")
        print("-"*30)
        print(response)

if __name__ == "__main__":
    main()