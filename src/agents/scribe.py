import os
import time
import json
import csv
import re
import config
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class Scribe:
    def __init__(self):
        print("--- Initializing Scribe Agent ---")
        
        self.output_dir = os.path.join(os.getcwd(), "data", "outputs")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Smart Model for JSON parsing
        self.llm = config.get_llm("scribe")
        
        # Global Headers matching your requirement
        self.CSV_HEADERS = ["ID", "Title", "Action", "Expected Result"]

        # Prompt: Request Lists for Steps/Results so we can print them line-by-line
        template = """
        You are 'The Scribe'. Convert the Test Cases below into a JSON List.
        
        INPUT TEXT:
        {test_cases}
        
        INSTRUCTIONS:
        1. "title_merged": Combine Feature + Scenario + Main Result.
        2. "steps": MUST be a JSON Array of strings. ["1. Step one", "2. Step two"]
        3. "step_expected_results": MUST be a JSON Array of strings (1-to-1 match with steps).
        4. "pre_conditions": A string (bullet points or text).
        5. "cleanup": A string.
        
        REQUIRED JSON STRUCTURE:
        [
            {{
                "id": "TC_001",
                "title_merged": "Feature - Scenario - Result",
                "pre_conditions": "User is on page...",
                "steps": ["1. Step one", "2. Step two"],
                "step_expected_results": ["1. Result one", "2. Result two"],
                "cleanup": "Cleanup actions..."
            }}
        ]
        """
        
        self.prompt = PromptTemplate(template=template, input_variables=["test_cases"])
        self.chain = self.prompt | self.llm | StrOutputParser()

    def save(self, content):
        if not content: return "Error: No content."

        try:
            print("[SCRIBE] Generating Multi-Row Excel format...")
            json_response = self.chain.invoke({"test_cases": content})
            
            # --- FIX: Extract JSON from chatty LLM response ---
            match = re.search(r'\[.*\]', json_response, re.DOTALL)
            if match:
                clean_json = match.group(0)
            else:
                clean_json = json_response.replace("```json", "").replace("```", "").strip()
            # --------------------------------------------------

            try:
                data_list = json.loads(clean_json)
            except json.JSONDecodeError:
                print("[ERROR] JSON Parsing failed. Saving text backup.")
                return self._save_raw_text(content)

            filename = f"TestCases_{int(time.time())}.csv"
            filepath = os.path.join(self.output_dir, filename)

            # Write to CSV with strict quoting
            # encoding='utf-8-sig' ensures Excel opens it correctly
            with open(filepath, "w", newline='', encoding="utf-8-sig") as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                
                # 1. Global Header
                writer.writerow(self.CSV_HEADERS)
                
                # 2. Loop through Test Cases
                for tc in data_list:
                    # ROW 1: ID & Title
                    writer.writerow([
                        tc.get("id", "TC_XX"),
                        tc.get("title_merged", "Untitled"),
                        "", 
                        ""
                    ])
                    
                    # ROW 2: Pre-conditions
                    pre = tc.get("pre_conditions", "N/A")
                    writer.writerow(["", "", f"Pre-conditions:\n{pre}", ""])

                    # ROWS 3 to N: Steps & Results (Side by Side)
                    steps = tc.get("steps", [])
                    results = tc.get("step_expected_results", [])
                    
                    # Ensure alignment
                    max_len = max(len(steps), len(results))
                    
                    for i in range(max_len):
                        s_text = steps[i] if i < len(steps) else ""
                        r_text = results[i] if i < len(results) else ""
                        writer.writerow(["", "", s_text, r_text])
                        
                    # ROW LAST: Cleanup
                    cleanup = tc.get("cleanup", "N/A")
                    writer.writerow(["", "", f"Cleanup:\n{cleanup}", ""])
            
            return f"Success. Multi-Row Excel file saved: {filepath}"
            
        except Exception as e:
            return f"Error saving file: {e}"

    def _save_raw_text(self, content):
        filename = f"raw_backup_{int(time.time())}.txt"
        with open(os.path.join(self.output_dir, filename), "w", encoding="utf-8") as f:
            f.write(content)
        return f"formatting Error. Backup saved to: {filename}"