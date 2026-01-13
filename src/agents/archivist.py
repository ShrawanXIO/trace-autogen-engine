import sys
import config
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools.knowledge_base import get_retriever

class Archivist:
    def __init__(self):
        print("--- Initializing Archivist Agent (Expert in Legacy & Specs) ---")
        self.llm = config.get_llm("archivist")
        
        # Connect to Vector Store
        try:
            self.retriever = get_retriever()
            print("[ARCHIVIST] Connected to Knowledge Base.")
        except Exception as e:
            print(f"[ARCHIVIST] Warning: Knowledge Base unavailable. {e}")
            self.retriever = None

    def ask(self, query):
        """Standard doc retrieval for Manager's context gathering."""
        if not self.retriever:
            return "No Knowledge Base connection."
        
        try:
            # 1. Fetch Documents
            docs = self.retriever.invoke(query)
            
            # 2. CHECK: Did we find anything?
            if not docs:
                # Explicitly state that the test case/info was not found
                return "Test case not found in the archives."
            
            # 3. Return content if found
            return "\n\n".join([doc.page_content for doc in docs])
            
        except Exception as e:
            return f"Error retrieving data: {e}"

    def analyze_scenario(self, scenario, context):
        """
        Performs the Dual-Check:
        1. Legacy Check: Is there an existing test ID matching the FUNCTIONALITY?
        2. Validation Check: Does it align with Functional Specs?
        """
        if not self.retriever:
            return f"[NEW] | TC_NEW | {scenario}"

        # --- STEP 1: RETRIEVE LEGACY DATA ---
        legacy_query = f"legacy test case id and description for scenario: {scenario}"
        try:
            legacy_docs = self.retriever.invoke(legacy_query)
            if not legacy_docs:
                 legacy_data = "Test case not found in the archives."
            else:
                 legacy_data = "\n".join([doc.page_content for doc in legacy_docs])
        except:
            legacy_data = "Error retrieving legacy tests."

        # --- STEP 2: RETRIEVE FUNCTIONAL SPECS ---
        spec_query = f"functional requirement business rule for: {scenario} context: {context}"
        try:
            spec_docs = self.retriever.invoke(spec_query)
            spec_data = "\n".join([doc.page_content for doc in spec_docs])
        except:
            spec_data = "No specific requirements found."

        # --- STEP 3: SYNTHESIS (Strict Semantic Matching) ---
        template = """
        You are the Archivist. Your job is to prevent rework.
        Determine if an EXISTING Test Case covers the NEW Scenario EXACTLY.
        
        NEW SCENARIO: "{scenario}"
        CONTEXT: "{context}"
        
        RETRIEVED LEGACY DATA (Existing Tests):
        {legacy_data}
        
        RETRIEVED SPECS (Requirements):
        {spec_data}
        
        STRICT MATCHING RULES:
        1. **Compare Functionality:** Do not just look for an ID. Read the description.
           - If Legacy Data is "Verify Login" but New Scenario is "Search Book", this is a MISMATCH. Output [NEW].
           - If Legacy Data says "Test case not found", this is a MISMATCH. Output [NEW].
           - Only output [MATCH] if the logic is identical.
        
        2. **Ignore Requirements:** IDs like "3.1.1", "REQ-01", "Page 5" are NOT Test Cases. Ignore them.
        
        3. **Decision Format:**
           - Exact Functional Match (e.g. TC_005 covers Search)? -> Output: [MATCH] | TC_005 | {scenario}
           - Different Logic or No ID found? -> Output: [NEW] | TC_NEW | {scenario}
        
        OUTPUT (Strictly one line):
        """
        
        prompt = PromptTemplate(
            template=template, 
            input_variables=["scenario", "context", "legacy_data", "spec_data"]
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            result = chain.invoke({
                "scenario": scenario,
                "context": context,
                "legacy_data": legacy_data,
                "spec_data": spec_data
            }).strip()

            # --- PYTHON SAFETY GUARDRAIL ---
            if "[MATCH]" in result:
                parts = result.split("|")
                if len(parts) > 1:
                    found_id = parts[1].strip().upper()
                    if found_id[0].isdigit(): 
                        return f"[NEW] | TC_NEW | {scenario}"
                    if len(found_id) > 20 and " " in found_id:
                         return f"[NEW] | TC_NEW | {scenario}"
            
            return result

        except Exception as e:
            return f"[NEW] | TC_NEW | {scenario}"

    def reconcile_scenarios(self, context, new_scenarios_text):
        print(f"[ARCHIVIST] Verifying {len(new_scenarios_text.splitlines())} scenarios against Legacy Data & Specs...")
        results = []
        scenarios = [s.strip() for s in new_scenarios_text.split('\n') if s.strip()]
        for scen in scenarios:
            result = self.analyze_scenario(scen, context)
            results.append(result)
        return "\n".join(results)