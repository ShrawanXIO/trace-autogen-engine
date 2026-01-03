import sys
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from tools.knowledge_base import get_retriever

class Archivist:
    def __init__(self):
        print("--- Initializing Archivist Agent ---")
        
        try:
            self.llm = ChatOllama(model="gpt-oss:20b-cloud")
            self.retriever = get_retriever()

            # STRICT PROMPT: Enforces "Librarian" behavior, forbids "Creator" behavior.
            template = """
            You are 'The Archivist', a strictly evidence-based researcher for a QA Testing project.
            Your ONLY job is to search the provided Project Documentation and Existing Test Cases to answer the user's query.

            --- STRICT GUIDELINES ---
            1. Answer ONLY using the information in the "Context" section below.
            2. Do NOT generate new data, code, or examples from your own imagination.
            3. If the user asks to "Write", "Create", or "Generate" (e.g., "Write a password"), DO NOT do it. 
               Instead, explain what the Documentation says about that topic (e.g., "The requirements state passwords must be...").
            4. If the information is NOT in the Context, strictly say: "I could not find any information about this in the loaded documentation."

            --- CONTEXT (Retrieved from Database) ---
            {context}
            -----------------------------------------

            User Question: {question}

            Your Evidence-Based Answer:
            """
            
            self.prompt = PromptTemplate(
                template=template, 
                input_variables=["context", "question"]
            )

            # Create the Chain: Retrieve Docs -> Format Prompt -> Ask LLM
            self.chain = (
                {"context": self.retriever, "question": RunnablePassthrough()} 
                | self.prompt 
                | self.llm 
                | StrOutputParser()
            )
            
        except Exception as e:
            print(f"Error setting up Archivist: {e}")
            raise e

    def ask(self, query):
        """
        Retrieves relevant docs and summarizes the answer.
        """
        if not query:
            return "Please provide a query."
            
        try:
            # invoke the chain
            response = self.chain.invoke(query)
            return response
        except Exception as e:
            return f"Error during retrieval: {e}"