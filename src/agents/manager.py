import sys
import os
import json

# Ensure we can import from src/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
# Agent Imports 
from agents.archivist import Archivist
from agents.author import Author
from agents.auditor import Auditor
from agents.scribe import Scribe
from ingest_data import ingest_knowledge_base

class Manager:
    def __init__(self):
        print("--- Initializing Manager Agent (Team Lead) ---")
        try:
            self.archivist = Archivist()
            self.author = Author()
            self.auditor = Auditor(archivist_agent=self.archivist)
            self.scribe = Scribe()
            # Fast model for decision making
            self.llm = ChatOllama(model="ministral-3:14b-cloud")
        except Exception as e:
            print(f"Error initializing team: {e}")
            sys.exit(1)

    def sync_knowledge(self):
        print("\n[MANAGER] Verifying Knowledge Base state...")
        status = ingest_knowledge_base()
        print(f"[MANAGER] Status: {status}")

    def analyze_input(self, full_text):
        """
        Splits the User Input into 'Rules' (Context) and 'Scenarios' (Tasks).
        """
        print("[MANAGER] Parsing User Input (separating Rules from Scenarios)...")
        
        template = """
        You are a Data parser. Analyze the input text below.
        
        INPUT TEXT:
        "{input}"
        
        INSTRUCTIONS:
        1. Extract the "Rules/Context" (Feature Description, Background, Acceptance Criteria).
        2. Extract the "Scenarios" (The numbered list or specific test scenarios).
        
        FORMAT OUTPUT strictly as:
        --- RULES ---
        (Paste rules here)
        --- SCENARIOS ---
        (Paste scenarios here)
        """
        
        prompt = PromptTemplate(template=template, input_variables=["input"])
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            result = chain.invoke({"input": full_text})
            
            # Simple string parsing
            rules = ""
            scenarios = ""
            
            if "--- RULES ---" in result and "--- SCENARIOS ---" in result:
                parts = result.split("--- SCENARIOS ---")
                rules = parts[0].replace("--- RULES ---", "").strip()
                scenarios = parts[1].strip()
            else:
                # Fallback: Treat everything as scenarios
                rules = "General Requirement"
                scenarios = full_text
                
            return rules, scenarios
        except Exception as e:
            print(f"Parsing Error: {e}")
            return full_text, full_text

    def classify_intent(self, user_input):
        template = """
        Analyze the user input and determine the Intent.
        Input: "{input}"
        
        Options:
        1. QUESTION (User asks for info/rules).
        2. REQUIREMENT (User provides a scenario/story).
        
        Return ONLY one word: "QUESTION" or "REQUIREMENT".
        """
        prompt = PromptTemplate(template=template, input_variables=["input"])
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            return chain.invoke({"input": user_input}).strip().upper()
        except:
            return "REQUIREMENT"

    def run_generation_workflow(self, user_input):
        print("\n[MANAGER] Starting Workflow...")

        # STEP 0: INTELLIGENT PARSING
        # We separate the input so we don't confuse the agents.
        rules_text, scenarios_text = self.analyze_input(user_input)
        
        print(f"\n[MANAGER] Identified Task:")
        print(f"   - Context Source: {len(rules_text)} chars")
        print(f"   - Scenarios to Write: \n{scenarios_text[:100]}...")

        # STEP 1: DUPLICATION CHECK (Using ONLY Scenarios)
        print(f"\n[MANAGER] Asking Archivist to check for duplicates...")
        # We only check if these specific SCENARIOS exist. We don't care if the Feature exists.
        duplication_query = f"Check database for EXISTING test cases strictly covering these scenarios: {scenarios_text}"
        check_result = self.archivist.ask(duplication_query)
        
        if "FOUND_EXISTING" in check_result:
             return f"Duplicate detected. Stopping.\n{check_result}"

        # STEP 2: CONTEXT GATHERING (Using ONLY Rules)
        print(f"\n[MANAGER] Gathering context for Author...")
        # We ask Archivist to find docs matching the Feature/Criteria
        context_query = f"Find standard business rules and style guides related to: {rules_text}"
        retrieved_docs = self.archivist.ask(context_query)
        
        # We combine the User's Rules + Retrieved Docs into one "Master Context"
        full_context = f"USER PROVIDED RULES:\n{rules_text}\n\nSYSTEM DOCS:\n{retrieved_docs}"

        # STEP 3: PRODUCTION LOOP
        topic = scenarios_text  # Author focuses on Scenarios
        feedback = ""
        previous_draft = ""
        attempt = 1
        max_attempts = 2 # Synergized limit

        while attempt <= max_attempts:
            print(f"\n[Attempt {attempt}/{max_attempts}]")
            
            # Author works on 'topic' (Scenarios) using 'full_context' (Rules)
            draft = self.author.write(topic, context=full_context, feedback=feedback, previous_draft=previous_draft)
            previous_draft = draft

            # Auditor checks the Draft against the Scenarios
            review = self.auditor.review(topic, draft)
            
            if "STATUS: APPROVED" in review:
                print("\n[MANAGER] Quality Gate Passed.")
                print("[MANAGER] Handing off to Scribe...")
                # Scribe saves the SINGLE file containing ALL scenarios
                save_status = self.scribe.save(draft)
                return f"Workflow Complete.\n\n{save_status}"
            else:
                print("\n[MANAGER] Quality Gate Failed. Sending back to Author.")
                print(f"Feedback: {review}")
                feedback = review
                attempt += 1

        return "Error: Max attempts reached. Content could not be approved."

    def process_request(self, user_input):
        self.sync_knowledge()
        intent = self.classify_intent(user_input)
        
        if "QUESTION" in intent:
            print(f"[MANAGER] Intent detected: RESEARCH")
            return f"Archivist Report: {self.archivist.ask(user_input)}"
        else:
            print(f"[MANAGER] Intent detected: WORK ORDER")
            return self.run_generation_workflow(user_input)