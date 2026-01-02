# import os
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_chroma import Chroma
# from langchain_ollama import OllamaEmbeddings

# # 1. Calculate Root Directory
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# VECTOR_STORE_PATH = os.path.join(BASE_DIR, "data", "vector_store")

# # 2. Configuration
# EMBEDDING_MODEL = "nomic-embed-text"

# def update_vector_store(documents):
#     """
#     Takes a list of documents, chunks them, and updates the local Vector Store.
#     Used by the ingestion script.
#     """
#     if not documents:
#         print("No documents to process. Skipping vector store update.")
#         return

#     # Chunking
#     print(f"--- Tool: Knowledge Base ---")
#     print(f"Splitting {len(documents)} documents...")
#     text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
#     chunks = text_splitter.split_documents(documents)
#     print(f"Created {len(chunks)} text chunks.")

#     # Embedding & Storage
#     print(f"Updating Vector Store at: {VECTOR_STORE_PATH}")
#     embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    
#     Chroma.from_documents(
#         documents=chunks, 
#         embedding=embeddings, 
#         persist_directory=VECTOR_STORE_PATH
#     )
#     print("Success: Knowledge Base Updated.")

# def get_retriever():

#     """
#     Returns the search interface (retriever) for the Vector Store.
#     Used by the Agents to find answers.
#     """
#     if not os.path.exists(VECTOR_STORE_PATH):
#         raise FileNotFoundError(f"Vector Store not found at {VECTOR_STORE_PATH}. Run ingestion first.")
        
#     embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    
#     vector_store = Chroma(
#         persist_directory=VECTOR_STORE_PATH, 
#         embedding_function=embeddings
#     )
    
#     # Return a retriever that looks for the top 3 most relevant chunks
#     return vector_store.as_retriever(search_kwargs={"k": 3})



import os
import sys
import shutil
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Calculate Root Directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VECTOR_STORE_PATH = os.path.join(BASE_DIR, "data", "vector_store")
EMBEDDING_MODEL = "nomic-embed-text"

def get_embedding_function():
    return OllamaEmbeddings(model=EMBEDDING_MODEL)

def get_db_sources(vector_store):
    """
    Retrieves a set of filenames currently stored in the Vector DB.
    """
    try:
        # Get metadata from the database to see what we have
        data = vector_store.get()
        if not data or not data['metadatas']:
            return set()
        
        # Extract 'source' from metadata
        existing_sources = {meta['source'] for meta in data['metadatas'] if 'source' in meta}
        return existing_sources
    except Exception:
        # If DB is empty or corrupt, return empty set
        return set()

def update_vector_store(documents):
    """
    Smart Update:
    1. Identifies NEW files and adds them (Incremental Update).
    2. Identifies DELETED files and asks user confirmation to remove them.
    """
    embedding_function = get_embedding_function()
    
    # Initialize DB (Connect to existing or create new)
    vector_store = Chroma(
        persist_directory=VECTOR_STORE_PATH, 
        embedding_function=embedding_function
    )

    # 1. IDENTIFY FILES ON DISK
    # Extract unique source paths from the loaded documents
    disk_sources = {doc.metadata['source'] for doc in documents}

    # 2. IDENTIFY FILES IN DATABASE
    db_sources = get_db_sources(vector_store)

    # 3. CALCULATE THE DELTA
    new_files = disk_sources - db_sources
    deleted_files = db_sources - disk_sources

    print("--- Sync Check ---")
    print(f"Existing in DB: {len(db_sources)}")
    print(f"Found on Disk:  {len(disk_sources)}")
    print(f"To Add:         {len(new_files)}")
    print(f"To Delete:      {len(deleted_files)}")
    print("-" * 20)

    # 4. HANDLE DELETIONS (With User Confirmation)
    if deleted_files:
        print("\n[!] The following files are in the DB but missing from disk:")
        for f in deleted_files:
            print(f" - {os.path.basename(f)}")
        
        confirm = input("\nDo you want to DELETE these from the database? (y/n): ").strip().lower()
        
        if confirm == 'y':
            print("Removing obsolete records...")
            # Delete where metadata 'source' matches the file path
            for file_path in deleted_files:
                vector_store._collection.delete(where={"source": file_path})
            print("Cleanup complete.")
        else:
            print("Skipping deletion. Old data remains.")

    # 5. HANDLE ADDITIONS (Incremental)
    if new_files:
        print(f"\nProcessing {len(new_files)} new files...")
        
        # Filter the original documents list to keep only the new ones
        docs_to_add = [doc for doc in documents if doc.metadata['source'] in new_files]
        
        # Split and Embed ONLY the new files
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(docs_to_add)
        
        if chunks:
            print(f"Adding {len(chunks)} new chunks to Vector Store...")
            vector_store.add_documents(chunks)
            print("Success: New data added.")
        else:
            print("Warning: New files were empty.")
    else:
        print("\nNo new files to add.")

def get_retriever():
    """
    Returns the search interface.
    """
    if not os.path.exists(VECTOR_STORE_PATH):
        raise FileNotFoundError("Vector Store not found. Run ingestion first.")
        
    vector_store = Chroma(
        persist_directory=VECTOR_STORE_PATH, 
        embedding_function=get_embedding_function()
    )
    return vector_store.as_retriever(search_kwargs={"k": 3})