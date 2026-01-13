import sys
import os
import re
import config

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
        print("[MANAGER] Verifying Knowledge Base State...")
        ingest_knowledge_base()
        
        self.archivist = Archivist()
        self.author = Author()
        self.auditor = Auditor(archivist_agent=self.archivist)
        self.scribe = Scribe()
        self.llm = config.get_llm("manager")

        # --- SMART PARSER PROMPT ---
        self.parser_template = """
        You are the QA Manager. Parse the user input into structured data.
        
        INPUT TEXT:
        {input_text}
        
        INSTRUCTIONS:
        1. Identify the **Context** (Feature, Description, AC).
        2. Identify the **List of Scenarios**.
           - Handle typos like "Senerios".
           - **CRITICAL:** Ignore empty lines and whitespace.
           - **CRITICAL:** Extract only the actual scenario text lines.
           - Do not summarize. If there are 19 actual scenarios, list all 19.
        
        OUTPUT FORMAT STRICTLY:
        --- CONTEXT ---
        (Context text here)
        --- TASKS ---
        (Scenario 1)
        (Scenario 2)
        ...
        """
        self.parser_prompt = PromptTemplate(template=self.parser_template, input_variables=["input_text"])
        self.parser_chain = self.parser_prompt | self.llm | StrOutputParser()

    def analyze_input_smartly(self, text):
        print("[MANAGER] Using AI to parse input structure...")
        try:
            response = self.parser_chain.invoke({"input_text": text})
            context = "General Context"
            tasks = []
            if "--- TASKS ---" in response:
                parts = response.split("--- TASKS ---")
                context = parts[0].replace("--- CONTEXT ---", "").strip()
                raw_tasks = parts[1].strip()
                tasks = [line.strip() for line in raw_tasks.split('\n') if line.strip()]
            else:
                print("[MANAGER] Warning: AI parsing fallback. Using raw split.")
                tasks = [line.strip() for line in text.split('\n') if line.strip()]
            return context, tasks
        except Exception as e:
            print(f"[MANAGER] Parsing error: {e}")
            return "Context", []

    def run_generation_workflow(self, user_input):
        print("\n[MANAGER] Starting Workflow...")

        # 1. PARSE
        context_rules, scenario_list = self.analyze_input_smartly(user_input)
        print(f"[MANAGER] Identified {len(scenario_list)} valid scenarios.")
        
        if not scenario_list:
            return "Error: No scenarios found to process."

        # 2. RECONCILE
        print(f"[MANAGER] Verifying Scenarios against Vector Store...")
        
        clean_task_list = []
        new_counter = 1
        
        for scenario in scenario_list:
            # FIX: Use correct function 'analyze_scenario' and pass Context
            decision_str = self.archivist.analyze_scenario(scenario, context_rules)
            
            final_id = ""
            final_desc = scenario 
            
            if "[MATCH]" in decision_str:
                parts = decision_str.split("|")
                if len(parts) > 1:
                    final_id = parts[1].strip()
                    print(f"✅ Match: {final_id} covers '{scenario[:30]}...'")
                else:
                    final_id = f"TC_NEW_{new_counter:03d}"
                    new_counter += 1
            else:
                final_id = f"TC_NEW_{new_counter:03d}"
                new_counter += 1
                
            clean_task_list.append(f"{final_id}: {final_desc}")

        # 3. COMPILE MASTER LIST
        topic_for_author = "\n".join(clean_task_list)
        print(f"\n[MANAGER] Handing off {len(clean_task_list)} tasks to Author.")

        # 4. ACTIVE RESOLUTION LOOP
        full_context = f"RULES/AC:\n{context_rules}"
        feedback = ""
        previous_draft = ""
        
        attempt = 1
        max_attempts = 3 
        
        while attempt <= max_attempts:
            print(f"\n[Attempt {attempt}/{max_attempts}] Authoring...")
            
            # Manager Directive: Force Author to focus on feedback if it exists
            if feedback:
                print(f"[MANAGER] Instructing Author to fix Auditor feedback...")
                manager_directive = f"AUDITOR REJECTED DRAFT. FIX: {feedback}"
            else:
                manager_directive = ""

            draft = self.author.write(
                topic_for_author, 
                context=full_context, 
                feedback=manager_directive, 
                previous_draft=previous_draft
            )
            previous_draft = draft

            # Auditor Review
            review = self.auditor.review(topic_for_author, draft)
            
            if "STATUS: APPROVED" in review:
                print("[MANAGER] Quality Gate Passed. Synergy Achieved.")
                return self.scribe.save(draft)
            else:
                print(f"[MANAGER] Feedback Received.")
                feedback = review.replace("STATUS: REJECTED", "").strip()
                attempt += 1

        # 5. NO RUBBER STAMPING
        # If we fail 3 times, we return the error. We do NOT save bad data.
        return f"CRITICAL FAILURE: The team could not resolve the Auditor's requirements after {max_attempts} attempts. Please check if your Requirements are clear.\nFeedback: {feedback[:150]}..."

    def _validate_input(self, user_input):
        """Internal Guardrail: Filters out greetings and noise."""
        cleaned = user_input.strip().lower()
        greetings = ["hi", "hello", "hey", "greetings", "test", "start", "demo"]
        
        if cleaned in greetings:
            return False, "Greeting detected. No functional requirement provided.", "GREETING"
            
        if len(cleaned) < 12:
            return False, "Input is too short/vague to generate robust tests.", "INVALID_FORMAT"

        return True, "Valid Input", "VALID_WORK"

    def process_request(self, user_input):
        is_valid, reason, context_type = self._validate_input(user_input)
        if not is_valid:
            return {
                "status": "rejected", 
                "message": f"⚠️ **Guardrail Active:** {reason}\n\n*Please provide a full User Story.*",
                "preview": None,
                "file_path": None
            }

        if "?" in user_input or "what is" in user_input.lower():
            print("[MANAGER] Detected Question. Routing to Archivist...")
            # Wrap this in the dictionary format for the UI
            answer = self.archivist.ask(user_input)
            return {
                "status": "success",
                "message": "Archivist retrieved information.",
                "preview": answer,
                "file_path": None
            }

        return self.run_generation_workflow(user_input)