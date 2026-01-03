import sys
from dotenv import load_dotenv
from agents.archivist import Archivist
from agents.author import Author
from agents.auditor import Auditor
from agents.scribe import Scribe

# Load environment variables
load_dotenv()

def run_generation_loop(archivist, author, auditor, user_requirement):
    print("\n--- Starting Generation Workflow ---")
    
    # ---------------------------------------------------------
    # STEP 1: DUPLICATION CHECK (The Gatekeeper)
    # ---------------------------------------------------------
    print(f"\n[ARCHIVIST] Checking for existing test cases for: '{user_requirement}'...")
    
    # We force the Archivist to reply with a specific signal if tests exist
    duplication_query = f"""
    Check the database for any EXISTING test cases that strictly cover this scenario: "{user_requirement}".
    
    - If you find a match, output ONLY: "FOUND_EXISTING: [ID] - [Title]"
    - If you find NO match, output ONLY: "NO_EXISTING_TESTS"
    """
    
    duplication_check = archivist.ask(duplication_query)
    
    # DECISION LOGIC
    if "FOUND_EXISTING" in duplication_check:
        print("\n[SYSTEM] Duplicate Scenario Detected.")
        print(f"The Archivist found existing tests. Author will NOT run.\n")
        print(duplication_check.replace("FOUND_EXISTING:", "Existing Test Case:"))
        return None  # Exit the loop immediately, returning Nothing (so Scribe doesn't save)

    print("[ARCHIVIST] No duplicates found. Proceeding to generation.")

    # ---------------------------------------------------------
    # STEP 2: CONTEXT GATHERING (For the Author)
    # ---------------------------------------------------------
    # Now we ask Archivist for "Requirements" and "Reference Examples" (Style Guide)
    print(f"\n[ARCHIVIST] Gathering context (Docs & Reference Tests)...")
    
    context_query = f"""
    1. Find the Functional Requirements and Business Rules for: "{user_requirement}".
    2. Find ONE existing test case to serve as a formatting example (Style Guide).
    """
    project_context = archivist.ask(context_query)
    print(f"[INFO] Context passed to Author.")

    # ---------------------------------------------------------
    # STEP 3: AUTHOR & AUDITOR LOOP
    # ---------------------------------------------------------
    topic = user_requirement
    feedback = ""
    previous_draft = ""
    attempt = 1
    max_attempts = 3

    while attempt <= max_attempts:
        print(f"\n[Attempt {attempt}/{max_attempts}]")
        
        # Author Writes (using the Context found in Step 2)
        draft = author.write(topic, context=project_context, feedback=feedback, previous_draft=previous_draft)
        previous_draft = draft

        # Auditor Reviews
        review_result = auditor.review(topic, draft)
        
        if "STATUS: APPROVED" in review_result:
            print("\n[AUDITOR] Decision: APPROVED")
            return draft
        else:
            print("\n[AUDITOR] Decision: REJECTED")
            print(f"Feedback: {review_result}")
            feedback = review_result
            attempt += 1

    print("\nWarning: Max attempts reached. Returning best available version.")
    return previous_draft

def main():
    print("Trace STLC Engine Starting...")
    
    try:
        # Initialize Agents
        archivist = Archivist()
        author = Author()
        auditor = Auditor(archivist_agent=archivist)
        scribe = Scribe()
        print("System Ready.")
    except Exception as e:
        print(f"Error initializing agents: {e}")
        sys.exit(1)

    while True:
        print("\n--------------------------------------------------")
        mode = input("Select Mode (ask/write) or 'exit': ").strip().lower()

        if mode in ["exit", "quit"]:
            print("Exiting...")
            break

        if mode not in ["ask", "write"]:
            print("Invalid mode.")
            continue

        user_input = input(f"Enter Request for {mode}: ")
        
        if not user_input.strip():
            continue

        if mode == "ask":
            response = archivist.ask(user_input)
            print(f"\nArchivist: {response}")
        
        elif mode == "write":
            # The loop now handles the duplication check internally
            # Note: We now pass 'archivist' as the first argument
            final_content = run_generation_loop(archivist, author, auditor, user_input)
            
            # We only print/save if actual content was returned (i.e., not a duplicate)
            if final_content:
                print("\n" + "="*30)
                print("FINAL OUTPUT")
                print("="*30)
                print(final_content)
                
                print("\nSaving to disk...")
                save_status = scribe.save(final_content)
                print(save_status)

if __name__ == "__main__":
    main()