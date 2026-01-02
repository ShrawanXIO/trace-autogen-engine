import sys
from dotenv import load_dotenv
from agents.archivist import Archivist

# Load environment variables
load_dotenv()

def main():
    print("--- Trace STLC Engine Starting ---")
    
    # 1. Initialize the Agent
    try:
        print("Initializing Archivist Agent...")
        bot = Archivist()
        print("Archivist is ready. Type 'exit' to quit.\n")
    except Exception as e:
        print(f"Error initializing agent: {e}")
        sys.exit(1)

    print("-" * 50)

    # 2. Start the Conversation Loop
    while True:
        try:
            user_input = input("\nUser: ")
            
            # Exit conditions
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting...")
                break
            
            if not user_input.strip():
                continue

            print("Archivist is thinking...")
            
            # 3. Ask the Agent
            response = bot.ask(user_input)
            
            print(f"\nArchivist: {response}")
            print("-" * 50)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()