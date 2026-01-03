import os
import time
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class Scribe:
    def __init__(self):
        print("--- Initializing Scribe Agent ---")
        
        # Ensure output directory exists
        self.output_dir = os.path.join(os.getcwd(), "data", "outputs")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Initialize LLM for formatting
        self.llm = ChatOllama(model="ministral-3:14b-cloud")
        
        # Define the Formatter Persona
        # It takes the 'Human Readable' text and turns it into 'Machine Readable' CSV
        template = """
        You are 'The Scribe'. Your job is to format Test Cases into a clean CSV string.
        
        Input Text:
        {test_cases}
        
        Instructions:
        1. Extract the Test Case ID, Title, Pre-conditions, Steps, and Expected Result.
        2. Format output strictly as CSV (Comma Separated Values).
        3. Header row MUST be: "ID,Title,Pre-conditions,Steps,Expected Result".
        4. Wrap fields in quotes if they contain commas.
        5. Do NOT include any intro text or markdown (like ```csv). Just the raw CSV data.
        """
        
        self.prompt = PromptTemplate(
            template=template,
            input_variables=["test_cases"]
        )
        
        self.chain = self.prompt | self.llm | StrOutputParser()

    def save(self, content):
        """
        Converts content to CSV and saves it to a file.
        """
        if not content:
            return "Error: No content to save."

        try:
            print("Scribe is formatting data for Excel...")
            csv_content = self.chain.invoke({"test_cases": content})
            
            # Clean up potential markdown formatting from LLM
            csv_content = csv_content.replace("```csv", "").replace("```", "").strip()

            # Generate Filename with Timestamp
            filename = f"test_cases_{int(time.time())}.csv"
            filepath = os.path.join(self.output_dir, filename)

            # Write to file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(csv_content)
            
            return f"Success. File saved to: {filepath}"
            
        except Exception as e:
            return f"Error saving file: {e}"