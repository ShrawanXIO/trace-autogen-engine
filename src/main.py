import sys
from dotenv import load_dotenv
from agents.manager import Manager

# Load environment variables
load_dotenv()

def get_multiline_input():
    """
    Reads multiple lines from the user.
    - Stops reading immediately if user types 'exit' or 'quit'.
    - Stops reading and submits if user presses Enter on an empty line (Double Enter).
    """
    print("Paste your User Story & Scenarios below.")
    print("(Press Enter twice to submit. Type 'exit' on a new line to quit)")
    print("-" * 50)
    
    lines = []
    while True:
        try:
            line = input()
            
            # SMART CHECK: Instant Exit
            # If the user types 'exit' or 'quit', we stop immediately.
            if line.strip().lower() in ["exit", "quit"]:
                return "exit"

            # STOP CONDITION: Empty line (Double Enter)
            if not line:
                break
            
            lines.append(line)
            
        except EOFError:
            # Handle Ctrl+D or unexpected stream end
            break
    
    # Join all lines back into a single text block
    return "\n".join(lines).strip()

def main():
    print("Trace STLC Engine Starting...")
    
    # 1. Initialize the Boss (Manager)
    try:
        manager = Manager()
        print("System Ready. (Manager is listening)")
    except Exception as e:
        print(f"Critical System Error: {e}")
        sys.exit(1)

    # 2. The Conversation Loop
    while True:
        print("\n" + "="*50)
        
        # New "Smart" Input Function
        user_input = get_multiline_input()
        
        # Exit Condition
        # We check strictly against the specific keywords
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting...")
            break

        # If user just hit enter without typing anything, restart loop
        if not user_input:
            print("No input detected. Please try again.")
            continue

        # 3. Delegate to Manager
        try:
            response = manager.process_request(user_input)
            
            # 4. Show Result
            print("\n" + "-"*30)
            print("FINAL RESULT")
            print("-"*30)
            print(response)
            
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\nOperation cancelled by user.")
            continue
        except Exception as e:
            print(f"\n[ERROR] An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()