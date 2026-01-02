import sys
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class Auditor:
    def __init__(self):
        print("--- Initializing Auditor Agent ---")
        
        try:
            # 1. Initialize LLM
            self.llm = ChatOllama(model="llama3")

            # 2. Define the Strict Reviewer Persona
            template = """
            You are 'The Auditor', a Senior QA Lead. 
            Your goal is to ensure TRACEABILITY between the User Requirement and the Generated Test Cases.

            --- INPUTS ---
            User Requirement: "{requirement}"
            Generated Test Cases:
            "{test_cases}"
            --------------

            Analyze if the Test Cases fully cover the Requirement.
            
            Strictly output your response in this format:
            
            STATUS: [APPROVED or REJECTED]
            FEEDBACK: [If REJECTED, list specifically what is missing or wrong based on the requirement. If APPROVED, write "Looks good."]
            """
            
            # 3. Create the Chain
            prompt = PromptTemplate(
                template=template, 
                input_variables=["requirement", "test_cases"]
            )

            self.chain = prompt | self.llm | StrOutputParser()
            
        except Exception as e:
            print(f"Error setting up Auditor: {e}")
            raise e

    def review(self, requirement, test_cases_text):
        """
        Compares the generated tests against the original requirement.
        """
        if not requirement or not test_cases_text:
            return "Error: Missing requirements or test cases to review."
            
        try:
            print("Auditor is verifying traceability...")
            response = self.chain.invoke({
                "requirement": requirement,
                "test_cases": test_cases_text
            })
            return response
        except Exception as e:
            return f"Error: {e}"