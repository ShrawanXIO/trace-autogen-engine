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

            # 3. Universal Conflict Resolution Logic
            template = """
            You are 'The Auditor', a strict Senior QA Lead.
            
            Your job is to validate Test Cases against the "Source of Truth" (System Documentation).
            
            --- INPUTS ---
            1. User Request: "{requirement}"
            2. System Documentation (Rules & Constraints):
            "{context}"
            3. Generated Test Cases (Draft):
            "{test_cases}"
            --------------

            --- VALIDATION LOGIC ---
            Analyze the "User Request" vs "System Documentation".
            
            SCENARIO A: The User Request is compliant with System Rules.
            -> Ensure the Test Case steps are accurate and the Expected Result is Success.

            SCENARIO B: The User Request VIOLATES a System Rule (e.g., missing field, invalid data, wrong status).
            -> CHECK: Does the Test Case incorrectly show "Success" or "Valid"?
            -> ACTION: IF yes, REJECT it. 
               - The Test Case MUST simulate the User's bad input (do not change the input).
               - BUT the Expected Result MUST be a "System Error" or "Validation Failure".
               - This is called a "Negative Test Case".

            --- OUTPUT FORMAT ---
            Strictly output in this format:
            
            STATUS: [APPROVED or REJECTED]
            FEEDBACK: [If REJECTED, explain the logical conflict. E.g., "The input X violates Rule Y. Therefore, the Expected Result must be an Error Message, not Success."]
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
        """
        1. Consults the Archivist for background info.
        2. Reviews the tests against that info using logic gates.
        """
        if not requirement or not test_cases_text:
            return "Error: Missing inputs."
            
        try:
            print(f"Auditor is checking constraints for: '{requirement}'...")
            
            # 1. RETRIEVAL STEP
            # We ask specifically for constraints/rules to help the logic gate
            context_query = f"List all business rules, constraints, and negative scenarios for: {requirement}"
            system_context = self.archivist.ask(context_query)
            
            # 2. REVIEW STEP
            response = self.chain.invoke({
                "requirement": requirement,
                "context": system_context,
                "test_cases": test_cases_text
            })
            return response
            
        except Exception as e:
            return f"Error: {e}"