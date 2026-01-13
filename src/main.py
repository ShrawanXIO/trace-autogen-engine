import sys
from dotenv import load_dotenv
from agents.manager import Manager

# Load environment variables
load_dotenv()

def get_smart_input():
    """
    Reads multi-line input smartly.
    - Allows blank lines inside the text (e.g., between paragraphs).
    - Submits AUTOMATICALLY when 3 consecutive empty lines are detected.
    - Stops immediately if user types 'exit' or 'quit'.
    """
    print("Paste your User Story & Scenarios below.")
    print("(Press Enter 3 times to finish. Type 'exit' to quit)")
    print("-" * 50)
    
    lines = []
    empty_streak = 0
    
    while True:
        try:
            line = input()
            
            # 1. Check for immediate exit
            if line.strip().lower() in ["exit", "quit"]:
                return "EXIT"

            # 2. Smart Silence Detection
            if not line.strip():
                # It's an empty line. Increase the streak.
                empty_streak += 1
            else:
                # Text found! Reset streak.
                empty_streak = 0
            
            # 3. Stop condition: 3 Empty lines in a row
            if empty_streak >= 3:
                break
                
            lines.append(line)
            
        except EOFError:
            break
    
    # Clean up the trailing empty lines before returning
    return "\n".join(lines).strip()

def main():
    print("Trace STLC Engine Starting...")
    
    try:
        manager = Manager()
        print("System Ready. (Manager is listening)")
    except Exception as e:
        print(f"Critical System Error: {e}")
        sys.exit(1)

    while True:
        print("\n" + "="*50)
        
        # Use the new Smart Input function
        user_input = get_smart_input()
        
        # Exit Condition
        if user_input == "EXIT":
            print("Exiting...")
            break

        # Ignore empty submissions (e.g. user just hit enter once)
        if not user_input:
            continue

        try:
            # Delegate to Manager
            response = manager.process_request(user_input)
            
            print("\n" + "-"*30)
            print("FINAL RESULT")
            print("-"*30)
            print(response)
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            continue
        except Exception as e:
            print(f"\n[ERROR] An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()