import sys
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class Author:
    def __init__(self):
        print("--- Initializing Author Agent ---")
        
        try:
            self.llm = ChatOllama(model="llama3")

            # Updated Persona: Now strictly uses provided Context & Style Guide
            template = """
            You are 'The Author', a Senior QA Engineer.
            
            --- INPUTS ---
            1. User Request: {topic}
            2. PROJECT CONTEXT (App Docs & Similar Tests):
            "{context}"
            3. Previous Draft (if any): {previous_draft}
            4. Auditor Feedback (if any): {feedback}
            --------------

            INSTRUCTIONS:
            1. READ the "Project Context" first. You MUST follow the business rules found there.
            2. If the Context contains similar test cases, use them as a style guide (Few-Shot Learning).
            3. First, perform a Chain of Thought analysis to plan your tests.
            4. Then, write the Test Cases.

            FORMAT:
            
            --- THOUGHT PROCESS ---
            (Explain your reasoning here. Which rules are you testing? How are you handling negative scenarios?)
            --- END THOUGHTS ---

            Test Case ID: [ID]
            Title: [Title]
            Pre-conditions: [Pre-conditions]
            Steps:
            1. [Step 1]  | Step 1 Expected Result: [Expected Result]
            2. [Step 2]  | Step 2 Expected Result: [Expected Result]
            ...
            cleanup steps: [Cleanup]
            """
            
            # We added 'context' to the input_variables list
            self.prompt = PromptTemplate(
                template=template, 
                input_variables=["topic", "context", "feedback", "previous_draft"]
            )

            self.chain = self.prompt | self.llm | StrOutputParser()
            
        except Exception as e:
            print(f"Error setting up Author: {e}")
            raise e

    # Updated signature: Now accepts 'context'
    def write(self, topic, context, feedback="", previous_draft=""):
        """
        Generates test cases using specific Project Context.
        """
        if not topic:
            return "Please provide a topic."
            
        try:
            if feedback:
                print(f"Author is fixing specific errors in draft...")
            else:
                print(f"Author is writing test cases for: {topic}...")

            # Execute LLM with the new 'context' variable
            full_response = self.chain.invoke({
                "topic": topic,
                "context": context, 
                "feedback": feedback if feedback else "None",
                "previous_draft": previous_draft if previous_draft else "None"
            })

            # PARSE: Separate Thoughts from Content for cleaner output
            if "--- END THOUGHTS ---" in full_response:
                parts = full_response.split("--- END THOUGHTS ---")
                thought_process = parts[0].replace("--- THOUGHT PROCESS ---", "").strip()
                clean_content = parts[1].strip()
                
                # Print thoughts to console for transparency
                print(f"\n[AUTHOR'S THOUGHTS]\n{thought_process}\n" + "-"*40)
                
                return clean_content
            else:
                # Fallback if LLM ignores the separator
                return full_response

        except Exception as e:
            return f"Error: {e}"