import sys
import os

# --- ROBUST PATH SETUP ---
# 1. Get current directory (tests/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 2. Go UP one level to root, then DOWN into src
src_path = os.path.join(current_dir, "..", "src")
# 3. Add to Python Path
sys.path.append(src_path)

from agents.archivist import Archivist

def test_archivist():
    print("--- 1. Starting Archivist Test ---")
    
    try:
        # Initialize the agent
        # This will now use config.py and connect to the Knowledge Base
        agent = Archivist()
        print("✅ Archivist initialized successfully.")
        
        # Test Query
        query = "What is the main topic of the document?"
        
        print(f"\n--- 2. Asking Question: '{query}' ---")
        response = agent.ask(query)
        
        print("\n--- 3. Response Received ---")
        print(response)
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")

if __name__ == "__main__":
    test_archivist()