import sys
import config
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class Author:
    def __init__(self):
        print("--- Initializing Author Agent ---")
        try:
            self.llm = config.get_llm("author")

            # CALIBRATED TEMPLATE: Respects Manager's IDs
            template = """
            You are 'The Author', a Senior QA Engineer.
            
            --- INPUT TASKS (Strict List) ---
            {topic}
            (Format: "ID: Scenario Name")
            
            --- RULES (Context) ---
            {context}
            
            INSTRUCTIONS:
            1. Read the "INPUT TASKS" list line by line.
            2. For EACH item, create a Test Case.
            3. **CRITICAL:** Use the ID provided exactly (e.g., TC_504 or TC_NEW_001). 
               - DO NOT invent new IDs.
            4. Use "RULES" to fill in the "Pre-conditions" and "Expected Results".
            5. Output ALL test cases in one single block.

            FORMAT:
            
            Test Case ID: [ID from Input]
            Title: [Scenario Name]
            Pre-conditions: ...
            Steps:
            1. ...
            Expected Result:
            1. ...
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
            print(f"Author is drafting tests...")
            return self.chain.invoke({
                "topic": topic,
                "context": context, 
                "feedback": feedback if feedback else "None",
                "previous_draft": previous_draft if previous_draft else "None"
            })
        except Exception as e:
            return f"Error: {e}"