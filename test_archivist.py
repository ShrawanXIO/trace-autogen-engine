import sys
import os

# Add 'src' to the python path so we can find the agents folder
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.archivist import Archivist

def test_archivist():
    print("--- 1. Starting Archivist Test ---")
    
    try:
        # Initialize the agent
        agent = Archivist()
        print("✅ Archivist initialized successfully.")
        
        # Define a test query
        # (Change this to something actually in your PDF/knowledge base for a real test)
        query = "What is the main topic of the document?"
        
        print(f"\n--- 2. Asking Question: '{query}' ---")
        response = agent.ask(query)
        
        print("\n--- 3. Response Received ---")
        print(response)
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")

if __name__ == "__main__":
    test_archivist()