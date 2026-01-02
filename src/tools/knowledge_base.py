import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

# 1. Calculate Root Directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VECTOR_STORE_PATH = os.path.join(BASE_DIR, "data", "vector_store")

# 2. Configuration
EMBEDDING_MODEL = "nomic-embed-text"

def update_vector_store(documents):
    """
    Takes a list of documents, chunks them, and updates the local Vector Store.
    Used by the ingestion script.
    """
    if not documents:
        print("No documents to process. Skipping vector store update.")
        return

    # Chunking
    print(f"--- Tool: Knowledge Base ---")
    print(f"Splitting {len(documents)} documents...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} text chunks.")

    # Embedding & Storage
    print(f"Updating Vector Store at: {VECTOR_STORE_PATH}")
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    
    Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings, 
        persist_directory=VECTOR_STORE_PATH
    )
    print("Success: Knowledge Base Updated.")

def get_retriever():
    """
    Returns the search interface (retriever) for the Vector Store.
    Used by the Agents to find answers.
    """
    if not os.path.exists(VECTOR_STORE_PATH):
        raise FileNotFoundError(f"Vector Store not found at {VECTOR_STORE_PATH}. Run ingestion first.")
        
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    
    vector_store = Chroma(
        persist_directory=VECTOR_STORE_PATH, 
        embedding_function=embeddings
    )
    
    # Return a retriever that looks for the top 3 most relevant chunks
    return vector_store.as_retriever(search_kwargs={"k": 3})