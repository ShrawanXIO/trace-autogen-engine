import sys
import config
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class Auditor:
    def __init__(self, archivist_agent):
        print("--- Initializing Auditor Agent ---")
        try:
            self.archivist = archivist_agent
            self.llm = config.get_llm("auditor")

            template = """
            You are 'The Auditor'.
            
            YOUR GOAL: Verify Test Cases against the User Story.
            
            INPUTS:
            1. User Requirements: "{requirement}"
            2. Draft Test Cases: "{test_cases}"
            
            AUDIT RULES:
            1. **Check Coverage:** Did the Author create a test for every Scenario?
            
            2. **Legacy vs. New Logic (CRITICAL):**
               - **EXISTING IDs (e.g., TC_006, TC_102):** These are Legacy/Approved. 
                 -> CHECK: Does the Title match the Scenario? 
                 -> ACTION: If yes, **APPROVE automatically**. Do not critique the steps.
               
               - **NEW IDs (e.g., TC_NEW_001):** These are Unverified.
                 -> CHECK: Do the Steps & Results match the Acceptance Criteria?
                 -> ACTION: Critique strictly. REJECT if logic is missing or wrong.
            
            3. **Avoid Nitpicking:** Do not reject for minor wording ("Button disabled" vs "Button hidden"). Reject only for Logic Failures.

            FORMAT:
            
            --- ANALYSIS ---
            * (Coverage: "All 10 scenarios covered.")
            * (Legacy Checks: "TC_006 is existing data. Skipped step verification.")
            * (New Checks: "TC_NEW_001 logic aligns with AC...")
            --- END ANALYSIS ---
            
            STATUS: [APPROVED or REJECTED]
            FEEDBACK: (Only if REJECTED. Be specific.)
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