import os
import time
import json
import csv
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

        # Initialize LLM (Smart model for JSON structure)
        self.llm = ChatOllama(model="ministral-3:14b-cloud")
        
        # 1. Define the Parser Persona
        # We ask for a JSON list. This is the most reliable way to get structured data.
        template = """
        You are 'The Scribe'. Convert the Test Cases below into a JSON LIST.
        
        INPUT TEXT:
        {test_cases}
        
        INSTRUCTIONS:
        1. Parse the text into a list of objects.
        2. Combine all 'Steps' into a SINGLE string (separated by newlines).
        3. Do NOT use markdown formatting in the output. Just raw JSON.
        
        REQUIRED JSON STRUCTURE:
        [
            {{
                "feature": "Feature Name (or General)",
                "id": "TC_001",
                "scenario": "Title of the test",
                "pre_conditions": "Pre-conditions text",
                "steps": "1. Step one...\\n2. Step two...",
                "expected_result": "Expected Result text"
            }}
        ]
        """
        
        self.prompt = PromptTemplate(
            template=template,
            input_variables=["test_cases"]
        )
        
        self.chain = self.prompt | self.llm | StrOutputParser()

    def save(self, content):
        """
        Converts content to JSON -> Professional CSV.
        """
        if not content:
            return "Error: No content to save."

        try:
            print("[SCRIBE] Formatting data for Excel compatibility...")
            
            # 1. Get structured JSON from AI
            json_response = self.chain.invoke({"test_cases": content})
            
            # Clean up AI artifacts (markdown quotes)
            clean_json = json_response.replace("```json", "").replace("```", "").strip()
            
            # 2. Parse into Python List
            try:
                data_list = json.loads(clean_json)
            except json.JSONDecodeError:
                # If AI fails JSON, we save raw text to avoid losing data
                return self._save_raw_text(content)

            # 3. Define the Professional Headers (Matches typical Excel Templates)
            headers = [
                "Feature", 
                "Test Case ID", 
                "Scenario Name", 
                "Pre-Conditions", 
                "Test Steps", 
                "Expected Result", 
                "Status", 
                "Comments"
            ]

            # 4. Generate Filename
            filename = f"TestCases_{int(time.time())}.csv"
            filepath = os.path.join(self.output_dir, filename)

            # 5. Write to CSV with "Excel-Safe" Quoting
            # quoting=csv.QUOTE_ALL wraps EVERYTHING in quotes ("value").
            # This ensures that commas or newlines inside your steps don't break the columns.
            with open(filepath, "w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                
                # Write Header Row
                writer.writerow(headers)
                
                # Write Data Rows
                for item in data_list:
                    writer.writerow([
                        item.get("feature", "General"),
                        item.get("id", "TC_XX"),
                        item.get("scenario", ""),
                        item.get("pre_conditions", "N/A"),
                        # Force Excel-style newlines so steps appear stacked in one cell
                        item.get("steps", "").replace("\n", "\r\n"), 
                        item.get("expected_result", ""),
                        "Not Run",  # Default Status
                        ""          # Empty Comments column for manual use
                    ])
            
            return f"Success. Excel-ready file saved: {filepath}"
            
        except Exception as e:
            return f"Error saving file: {e}"

    def _save_raw_text(self, content):
        filename = f"raw_backup_{int(time.time())}.txt"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Formatting Error (JSON Failed). Saved raw text to: {filepath}"