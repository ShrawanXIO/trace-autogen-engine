import sys
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class Author:
    def __init__(self):
        print("--- Initializing Author Agent ---")
        
        try:
            # 1. Initialize LLM
            self.llm = ChatOllama(model="llama3")

            # 2. Define the Writer's Personality
            template = """
            You are 'The Author', a Senior QA Engineer.
            
            --- CONTEXT ---
            User Request: {topic}
            Previous Draft (if any):
            {previous_draft}
            
            Auditor Feedback (if any): 
            {feedback}
            --------------

            Instructions:
            1. If there is NO Previous Draft, write fresh test cases based on the Request.
            2. If there IS a Previous Draft + Feedback:
               - Locate the specific Test Case mentioned in the Feedback.
               - UPDATE ONLY that specific part (e.g., add the missing step, fix the result).
               - DO NOT change Test Cases that were already correct.
               - RETURN the full corrected set of test cases.

            Format exactly like this:
            Test Case ID: [ID]
            Title: [Title]
            Pre-conditions: [Pre-conditions]
            Steps:
            1. [Step 1]  | Step 1 Expected Result: [Expected Result]
            2. [Step 2]  | Step 2 Expected Result: [Expected Result]
            ...
            cleanup steps: [Cleanup]
            
            Generate or Update the Test Cases now:
            """
            
            prompt = PromptTemplate(
                template=template, 
                input_variables=["topic", "feedback", "previous_draft"]
            )

            self.chain = prompt | self.llm | StrOutputParser()
            
        except Exception as e:
            print(f"Error setting up Author: {e}")
            raise e

    def write(self, topic, feedback="", previous_draft=""):
        """
        Generates or Updates test cases.
        """
        if not topic:
            return "Please provide a topic."
            
        try:
            if feedback:
                print(f"Author is fixing specific errors in draft...")
            else:
                print(f"Author is writing about: {topic}...")

            # Invoke the chain with all three inputs
            response = self.chain.invoke({
                "topic": topic, 
                "feedback": feedback if feedback else "None",
                "previous_draft": previous_draft if previous_draft else "None"
            })
            return response
        except Exception as e:
            return f"Error: {e}"