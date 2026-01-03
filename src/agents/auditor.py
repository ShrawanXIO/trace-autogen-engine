import sys
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class Auditor:
    def __init__(self, archivist_agent):
        print("--- Initializing Auditor Agent ---")
        try:
            self.archivist = archivist_agent
            self.llm = ChatOllama(model="gemma3:27b-cloud")

            template = """
            You are 'The Auditor'.
            
            CONSTRAINT: The User's list of Scenarios is FINAL. Do not suggest adding new test cases.
            YOUR JOB: Verify accuracy of the generated steps against the Acceptance Criteria.

            User Input (Source of Truth): "{requirement}"
            Draft Test Cases: "{test_cases}"
            
            INSTRUCTIONS:
            1. Check if the Author created a test for every Scenario listed in the input.
            2. Check if the "Expected Results" match the "Acceptance Criteria".
            3. IGNORE formatting preferences. Focus on Logic.
            4. If REJECTING, provide the EXACT text correction.

            FORMAT:
            
            --- ANALYSIS ---
            * (Scope: "Author covered all 5 provided scenarios...")
            * (Accuracy: "Steps match acceptance criteria...")
            --- END ANALYSIS ---
            
            STATUS: [APPROVED or REJECTED]
            FEEDBACK: (If REJECTED, "Change Test Case 2 Expected Result to...")
            """
            
            self.prompt = PromptTemplate(
                template=template, 
                input_variables=["requirement", "test_cases"]
            )

            self.chain = self.prompt | self.llm | StrOutputParser()
            
        except Exception as e:
            print(f"Error setting up Auditor: {e}")
            raise e

    def review(self, requirement, test_cases_text):
        if not requirement or not test_cases_text: return "Error: Missing inputs."
        try:
            print(f"Auditor is reviewing...")
            full_response = self.chain.invoke({
                "requirement": requirement,
                "test_cases": test_cases_text
            })
            
            if "--- END ANALYSIS ---" in full_response:
                parts = full_response.split("--- END ANALYSIS ---")
                analysis = parts[0].replace("--- ANALYSIS ---", "").strip()
                decision = parts[1].strip()
                print(f"\n[AUDITOR CHECK]\n{analysis}\n" + "-"*40)
                return decision
            else:
                return full_response
        except Exception as e:
            return f"Error: {e}"