
# import sys
# from langchain_ollama import ChatOllama
# # 1. New Imports for Modern Chains
# #from langchain_community.chains import ConversationalRetrievalChain
# from langchain_classic.chains import ConversationalRetrievalChain
# from langchain_core.prompts import ChatPromptTemplate
# from tools.knowledge_base import get_retriever

# class Archivist:
#     def __init__(self):
#         print("--- Initializing Archivist Agent ---")
        
#         try:
#             # 2. Initialize LLM
#             self.llm = ChatOllama(model="llama3")

#             # 3. Get the Retriever Tool
#             self.retriever = get_retriever()

#             # 4. Define the Prompt (Updated for Chat Models)
#             # In modern chains, we use ChatPromptTemplate.
#             # It MUST have a placeholder for "{context}" and "{input}".
#             system_prompt = (
#                 "You are a technical assistant. "
#                 "Use the context below to answer the question. "
#                 "If you don't know, say so."
#                 "\n\n"
#                 "{context}"
#             )
            
#             prompt = ChatPromptTemplate.from_messages(
#                 [
#                     ("system", system_prompt),
#                     ("human", "{input}"),
#                 ]
#             )

#             # 5. Create the Modern Chain
#             # Use a conversational retrieval chain (avoids unresolved imports)
#             self.rag_chain = ConversationalRetrievalChain.from_llm(
#                 self.llm, self.retriever, return_source_documents=False
#             )
            
#         except Exception as e:
#             print(f"Error setting up Archivist: {e}")
#             raise e

#     def ask(self, query):
#         if not query: return "Please provide a valid question."
#         try:
#             # 6. Execute the chain
#             response = self.rag_chain.invoke(query)
#             return response or "No answer generated."
            
#         except Exception as e:
#             return f"Error: {e}"
        

# *

import sys
from langchain_ollama import ChatOllama
# 1. Correct standard imports (requires 'pip install langchain')
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from tools.knowledge_base import get_retriever

class Archivist:
    def __init__(self):
        print("--- Initializing Archivist Agent ---")
        
        try:
            # 2. Initialize LLM
            self.llm = ChatOllama(model="llama3")

            # 3. Get the Retriever Tool
            self.retriever = get_retriever()

            # 4. Define the Prompt
            # We explicitly tell the system: "The user's question will be in the variable {input}"
            system_prompt = (
                "You are a technical assistant. "
                "Use the context below to answer the question. "
                "If you don't know, say so."
                "\n\n"
                "{context}"
            )
            
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    ("human", "{input}"),
                ]
            )

            # 5. Create the Modern Chain
            # This chain combines the docs and the prompt
            question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
            
            # This chain manages the retrieval and passing of data
            self.rag_chain = create_retrieval_chain(self.retriever, question_answer_chain)
            
        except Exception as e:
            print(f"Error setting up Archivist: {e}")
            raise e

    def ask(self, query):
        if not query: return "Please provide a valid question."
        try:
            # 6. Execute the chain
            # We pass {"input": query} to match the "{input}" variable in the prompt above.
            response = self.rag_chain.invoke({"input": query})
            
            # The answer is always stored in the 'answer' key for this chain type
            return response.get("answer", "No answer generated.")
            
        except Exception as e:
            return f"Error: {e}"