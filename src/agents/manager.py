import sys
import os

# Ensure we can import from src/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

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
            # Using Ministral for smart parsing logic
            self.llm = ChatOllama(model="ministral-3:14b-cloud")
        except Exception as e:
            print(f"Error initializing team: {e}")
            sys.exit(1)

    def sync_knowledge(self):
        print("\n[MANAGER] Verifying Knowledge Base state...")
        ingest_knowledge_base()

    def analyze_input(self, full_text):
        """
        SMART PARSER:
        Separates 'Context' (Feature/Rules) from 'Tasks' (Scenarios).
        """
        print("[MANAGER] Analyzing input structure...")
        
        template = """
        You are a QA Lead. Analyze the input below.
        
        INPUT TEXT:
        "{input}"
        
        TASK:
        1. Identify "CONTEXT" (Feature Title, Background, Acceptance Criteria).
        2. Identify "TASKS" (The specific Scenarios or numbered list).
        
        OUTPUT FORMAT (Strictly):
        --- CONTEXT ---
        (Paste context here)
        --- TASKS ---
        (Paste strictly the list of scenarios here)
        """
        
        prompt = PromptTemplate(template=template, input_variables=["input"])
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            result = chain.invoke({"input": full_text})
            
            if "--- CONTEXT ---" in result and "--- TASKS ---" in result:
                parts = result.split("--- TASKS ---")
                context = parts[0].replace("--- CONTEXT ---", "").strip()
                tasks = parts[1].strip()
                return context, tasks
            else:
                return "General Requirement", full_text 
        except:
            return "General Requirement", full_text

    def classify_intent(self, user_input):
        if "?" in user_input and len(user_input) < 150:
            return "QUESTION"
        return "REQUIREMENT"

    def run_generation_workflow(self, user_input):
        print("\n[MANAGER] Starting Workflow...")

        # STEP 1: SMART PARSE (Splits Rules vs Scenarios)
        rules_text, scenarios_text = self.analyze_input(user_input)
        
        print(f"[MANAGER] Identified Context ({len(rules_text)} chars) and Scenarios.")

        # STEP 2: CONTEXT GATHERING
        print(f"[MANAGER] Gathering external knowledge...")
        # Ask Archivist about Rules (not Scenarios)
        db_context = self.archivist.ask(f"Find business rules for: {rules_text}")
        full_context = f"USER STORY CONTEXT:\n{rules_text}\n\nDATABASE RULES:\n{db_context}"

        # STEP 3: EXECUTION LOOP
        topic = scenarios_text
        feedback = ""
        previous_draft = ""
        attempt = 1
        
        while attempt <= 2:
            print(f"\n[Attempt {attempt}/2]")
            
            # Author generates ALL tests in one go
            draft = self.author.write(topic, context=full_context, feedback=feedback, previous_draft=previous_draft)
            previous_draft = draft

            # Auditor reviews ALL tests in one go
            review = self.auditor.review(topic, draft)
            
            if "STATUS: APPROVED" in review:
                print("\n[MANAGER] Quality Gate Passed.")
                # Scribe saves ONE file
                return self.scribe.save(draft)
            else:
                print(f"\n[MANAGER] Feedback Received. Refining...")
                feedback = review
                attempt += 1

        return "Error: Max attempts reached."

    def process_request(self, user_input):
        self.sync_knowledge()
        intent = self.classify_intent(user_input)
        
        if intent == "QUESTION":
            return f"Archivist Report: {self.archivist.ask(user_input)}"
        else:
            return self.run_generation_workflow(user_input)