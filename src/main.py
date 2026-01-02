import sys
from dotenv import load_dotenv
from agents.archivist import Archivist
from agents.author import Author

# Load environment variables
load_dotenv()

def main():
    print("Trace STLC Engine Starting...")
    
    # Initialize Agents
    try:
        archivist = Archivist()
        author = Author()
        print("System Ready.")
    except Exception as e:
        print(f"Error initializing agents: {e}")
        sys.exit(1)

    # Main Conversation Loop
    while True:
        print("\n--------------------------------------------------")
        mode = input("Select Mode (ask/write) or 'exit': ").strip().lower()

        if mode in ["exit", "quit"]:
            print("Exiting...")
            break

        if mode not in ["ask", "write"]:
            print("Invalid mode. Please type 'ask' or 'write'.")
            continue

        user_input = input(f"Enter Request for {mode}: ")
        
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting...")
            break

        if not user_input.strip():
            continue

        print("Processing...")

        if mode == "ask":
            response = archivist.ask(user_input)
            print(f"\nArchivist: {response}")
        
        elif mode == "write":
            response = author.write(user_input)
            print(f"\nAuthor:\n{response}")

if __name__ == "__main__":
    main()