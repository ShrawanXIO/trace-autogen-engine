import sys
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class Author:
    def __init__(self):
        print("--- Initializing Author Agent ---")
        try:
            self.llm = ChatOllama(model="ministral-3:14b-cloud")

            template = """
            You are 'The Author', a Senior QA Engineer.
            
            --- INPUTS ---
            SCENARIOS TO AUTOMATE (The Task):
            "{topic}"
            
            BUSINESS RULES & CONTEXT (The Truth):
            "{context}"
            
            FEEDBACK: {feedback}
            PREVIOUS DRAFT: {previous_draft}
            ----------------

            INSTRUCTIONS:
            1. Read the "SCENARIOS TO AUTOMATE" list.
            2. For EACH scenario in that list, create a Test Case.
            3. Use "BUSINESS RULES" to fill in the "Pre-conditions" and "Expected Results".
            4. If Feedback exists, fix the errors without rewriting valid tests.
            5. Output ALL test cases in one single block.

            FORMAT:
            
            --- THOUGHTS ---
            * (Strategy: "Mapping Scenario 1 to Rule X...")
            --- END THOUGHTS ---

            Test Case ID: [TC_01]
            Title: [Scenario Name]
            Pre-conditions: [Derived from Rules]
            Steps:
            1. [Step]
            Expected Result: [Result]
            
            Test Case ID: [TC_02]
            ...
            """
            
            self.prompt = PromptTemplate(
                template=template, 
                input_variables=["topic", "context", "feedback", "previous_draft"]
            )

            self.chain = self.prompt | self.llm | StrOutputParser()
            
        except Exception as e:
            print(f"Error setting up Author: {e}")
            raise e

    def write(self, topic, context, feedback="", previous_draft=""):
        if not topic: return "Please provide a topic."
        try:
            mode = "Refining" if feedback else "Drafting"
            print(f"Author is {mode}...")
            
            full_response = self.chain.invoke({
                "topic": topic,
                "context": context, 
                "feedback": feedback if feedback else "None",
                "previous_draft": previous_draft if previous_draft else "None"
            })

            if "--- END THOUGHTS ---" in full_response:
                parts = full_response.split("--- END THOUGHTS ---")
                thought = parts[0].replace("--- THOUGHTS ---", "").strip()
                content = parts[1].strip()
                print(f"\n[AUTHOR STRATEGY]\n{thought}\n" + "-"*40)
                return content
            else:
                return full_response
        except Exception as e:
            return f"Error: {e}"