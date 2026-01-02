import sys
from dotenv import load_dotenv
from agents.archivist import Archivist
from agents.author import Author
from agents.auditor import Auditor

# Load environment variables
load_dotenv()

def run_generation_loop(author, auditor, user_requirement):
    """
    Orchestrates the collaboration between Author and Auditor.
    It loops until the Auditor approves or max attempts are reached.
    """
    print("\n--- Starting Automatic Review Loop ---")
    
    topic = user_requirement
    feedback = ""
    previous_draft = ""
    attempt = 1
    max_attempts = 3

    while attempt <= max_attempts:
        print(f"\n[Attempt {attempt}/{max_attempts}]")
        
        # 1. Author Writes
        # We pass previous_draft so the author knows what to fix in subsequent loops
        draft = author.write(topic, feedback, previous_draft)
        
        # Store this draft for the next loop (if needed)
        previous_draft = draft

        # 2. Auditor Reviews
        # The Auditor will consult the Archivist internally to check against documentation
        review_result = auditor.review(topic, draft)
        
        # 3. Check Decision
        if "STATUS: APPROVED" in review_result:
            print("\n✅ Auditor Decision: APPROVED")
            return draft
        else:
            print("\n❌ Auditor Decision: REJECTED")
            print(f"Feedback: {review_result}")
            
            # Use the review as feedback for the next loop
            feedback = review_result
            attempt += 1

    print("\n⚠️ Max attempts reached. Returning best available version.")
    return previous_draft

def main():
    print("Trace STLC Engine Starting...")
    
    # Initialize Agents
    try:
        # 1. Create Archivist (The Knowledge)
        archivist = Archivist()
        
        # 2. Create Author (The Writer)
        author = Author()
        
        # 3. Create Auditor (The Reviewer)
        # We pass the archivist so the Auditor can check facts
        auditor = Auditor(archivist_agent=archivist)
        
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
            # Simple Research Mode
            response = archivist.ask(user_input)
            print(f"\nArchivist: {response}")
        
        elif mode == "write":
            # Smart Generation Loop (Author + Auditor + Archivist)
            final_content = run_generation_loop(author, auditor, user_input)
            
            print("\n" + "="*30)
            print("🏆 FINAL OUTPUT")
            print("="*30)
            print(final_content)

if __name__ == "__main__":
    main()