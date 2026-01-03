import os
import json
from dotenv import load_dotenv

# 1. REUSE YOUR EXISTING TOOLS
# We import the folder list from file_ops so we scan the exact same places
from tools.file_ops import load_documents_dynamically, TARGET_FOLDERS
from tools.knowledge_base import update_vector_store

load_dotenv()

# Location of the "Logbook" file
STATE_FILE = os.path.join(os.getcwd(), "data", ".ingest_state.json")

def get_current_file_state():
    """
    Scans the TARGET_FOLDERS from file_ops.py to create a timestamp fingerprint.
    """
    current_state = {}
    
    # Use the configuration from your existing file_ops.py
    for folder in TARGET_FOLDERS:
        if os.path.exists(folder):
            for root, _, files in os.walk(folder):
                for file in files:
                    # Track relevant files only
                    if file.endswith(('.pdf', '.txt', '.csv', '.docx', '.md')):
                        filepath = os.path.join(root, file)
                        current_state[filepath] = os.path.getmtime(filepath)
    return current_state

def ingest_knowledge_base():
    """
    The Smart Manager Logic:
    1. Check timestamps (Fast).
    2. If changed, call file_ops and knowledge_base (Slow).
    """
    print("--- [SMART SYNC] Checking for file updates... ---")
    
    # A. Get Fingerprints
    current_state = get_current_file_state()
    
    # B. Load Logbook
    saved_state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                saved_state = json.load(f)
        except:
            saved_state = {}

    # C. Compare
    if current_state == saved_state and current_state:
        return "✔ System is up-to-date. No ingestion needed."

    print("⚡ Changes detected. triggering update...")

    # D. WORK: Reuse your existing modules
    try:
        # 1. Supplier: Load files
        documents = load_documents_dynamically()
        
        if documents:
            # 2. Pantry: Update DB
            update_vector_store(documents)
            
            # 3. Logbook: Save the new state so we don't run again
            with open(STATE_FILE, 'w') as f:
                json.dump(current_state, f)
            
            return f"Success. Knowledge Base refreshed."
        else:
            return "Warning: Changes detected, but no valid documents found."
            
    except Exception as e:
        return f"Ingestion Error: {e}"

def main():
    # Helper for manual run
    print(ingest_knowledge_base())

if __name__ == "__main__":
    main()