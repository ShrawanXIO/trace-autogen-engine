import sys
import os

# Ensure we can import from src/ (the parent directory)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from agents.archivist import Archivist
from agents.author import Author
from agents.auditor import Auditor
from agents.scribe import Scribe

# Import the Smart Ingestion Tool
from ingest_data import ingest_knowledge_base

class Manager:
    def __init__(self):
        print("--- Initializing Manager Agent (Team Lead) ---")
        try:
            self.archivist = Archivist()
            self.author = Author()
            self.auditor = Auditor(archivist_agent=self.archivist)
            self.scribe = Scribe()
            self.llm = ChatOllama(model="llama3")
        except Exception as e:
            print(f"Error initializing team: {e}")
            sys.exit(1)

    def sync_knowledge(self):
        """
        Triggers the Smart Sync.
        The ingest_data script handles the logic of checks vs. updates.
        """
        print("\n[MANAGER] Verifying Knowledge Base state...")
        # This call is now "smart" - it only updates if files changed
        status = ingest_knowledge_base()
        print(f"[MANAGER] Status: {status}")

    def classify_intent(self, user_input):
        template = """
        Analyze the user input and determine the Intent.
        Input: "{input}"
        
        Options:
        1. QUESTION (User asks for info/rules/status).
        2. REQUIREMENT (User provides a scenario/story to write tests for).
        
        Return ONLY one word: "QUESTION" or "REQUIREMENT".
        """
        prompt = PromptTemplate(template=template, input_variables=["input"])
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            return chain.invoke({"input": user_input}).strip().upper()
        except:
            return "REQUIREMENT"

    def run_generation_workflow(self, user_requirement):
        print("\n[MANAGER] Starting Workflow...")

        # 1. GATEKEEPER CHECK (Duplicates)
        print(f"[MANAGER] Asking Archivist to check for duplicates...")
        duplication_query = f"""
        Check database for EXISTING test cases strictly covering: "{user_requirement}".
        Output "FOUND_EXISTING: [ID] [Title]" OR "NO_EXISTING_TESTS".
        """
        check_result = self.archivist.ask(duplication_query)
        
        if "FOUND_EXISTING" in check_result:
            return f"Duplicate detected. Stopping.\n{check_result.replace('FOUND_EXISTING:', 'Reference:')}"

        # 2. CONTEXT GATHERING (Docs & Style)
        print(f"[MANAGER] Gathering context for Author...")
        context_query = f"Find functional rules and style examples for: {user_requirement}"
        context = self.archivist.ask(context_query)

        # 3. PRODUCTION LOOP (Author -> Auditor)
        topic = user_requirement
        feedback = ""
        previous_draft = ""
        attempt = 1
        max_attempts = 3

        while attempt <= max_attempts:
            print(f"\n[Attempt {attempt}/{max_attempts}]")
            
            # Author works
            draft = self.author.write(topic, context=context, feedback=feedback, previous_draft=previous_draft)
            previous_draft = draft

            # Auditor reviews
            review = self.auditor.review(topic, draft)
            
            if "STATUS: APPROVED" in review:
                print("\n[MANAGER] Quality Gate Passed.")
                print("[MANAGER] Handing off to Scribe...")
                save_status = self.scribe.save(draft)
                return f"Workflow Complete.\n{draft}\n\n{save_status}"
            else:
                print("\n[MANAGER] Quality Gate Failed. Sending back to Author.")
                print(f"Feedback: {review}")
                feedback = review
                attempt += 1

        return "Error: Max attempts reached. Content could not be approved."

    def process_request(self, user_input):
        """
        Main entry point.
        """
        # STEP 1: Smart Sync (Fast check or Full update)
        self.sync_knowledge()

        # STEP 2: Determine Intent
        intent = self.classify_intent(user_input)
        
        if "QUESTION" in intent:
            print(f"[MANAGER] Intent detected: RESEARCH")
            return f"Archivist Report: {self.archivist.ask(user_input)}"
        else:
            print(f"[MANAGER] Intent detected: WORK ORDER")
            return self.run_generation_workflow(user_input)