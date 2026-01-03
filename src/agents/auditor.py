import sys
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class Auditor:
    def __init__(self, archivist_agent):
        print("--- Initializing Auditor Agent (with Knowledge Access) ---")
        
        try:
            self.archivist = archivist_agent
            self.llm = ChatOllama(model="llama3")

            # Updated Persona: Now includes "Reasoning First" instructions
            template = """
            You are 'The Auditor', a strict Senior QA Lead.
            
            --- SOURCES ---
            User Request: "{requirement}"
            System Docs: "{context}"
            Draft Test Cases: "{test_cases}"
            ---------------

            INSTRUCTIONS:
            1. Analyze the Draft against the User Request and System Docs.
            2. Identify any missing rules or negative scenarios.
            3. First, output your REASONING.
            4. Then, output your DECISION.

            FORMAT:

            --- ANALYSIS ---
            (Explain your logical check here. E.g., "The user asked for X, but the draft shows Y...")
            --- END ANALYSIS ---
            
            STATUS: [APPROVED or REJECTED]
            FEEDBACK: [Details]
            """
            
            self.prompt = PromptTemplate(
                template=template, 
                input_variables=["requirement", "context", "test_cases"]
            )

            self.chain = self.prompt | self.llm | StrOutputParser()
            
        except Exception as e:
            print(f"Error setting up Auditor: {e}")
            raise e

    def review(self, requirement, test_cases_text):
        if not requirement or not test_cases_text:
            return "Error: Missing inputs."
            
        try:
            print(f"Auditor is retrieving context for verification...")
            context_query = f"Business rules and constraints for: {requirement}"
            system_context = self.archivist.ask(context_query)
            
            # Execute LLM
            full_response = self.chain.invoke({
                "requirement": requirement,
                "context": system_context,
                "test_cases": test_cases_text
            })
            
            # PARSE: Separate Analysis from Decision
            # This logic enables the "Glass Box" transparency
            if "--- END ANALYSIS ---" in full_response:
                parts = full_response.split("--- END ANALYSIS ---")
                analysis = parts[0].replace("--- ANALYSIS ---", "").strip()
                decision_block = parts[1].strip()
                
                # Show the Chain of Thought to the User
                print(f"\n[AUDITOR'S ANALYSIS]\n{analysis}\n" + "-"*40)
                
                return decision_block
            else:
                # Fallback if LLM forgets the format
                return full_response
            
        except Exception as e:
            return f"Error: {e}"