import sys
import os

# Add 'src' to the python path so we can import the agent
sys.path.append(os.path.join(os.getcwd(), "src"))

from agents.archivist import Archivist

def run_test():
    print("--- Starting Archivist Test ---")
    
    try:
        # 1. Initialize
        print("1. Initializing Agent... (This uses Llama3)")
        agent = Archivist()
        print("✅ Success: Agent Initialized.")
        
        # 2. Ask a Question (RAG Check)
        query = "What are the test requirements?"
        print(f"\n2. Sending Query: '{query}'")
        print("   Thinking...")
        
        response = agent.ask(query)
        
        print("\n--- Agent Response ---")
        print(response)
        print("----------------------")
        print("✅ Test Complete.")

    except Exception as e:
        print(f"\n❌ Test Failed: {e}")

if __name__ == "__main__":
    run_test()