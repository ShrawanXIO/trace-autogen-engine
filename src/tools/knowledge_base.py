import os
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VECTOR_STORE_PATH = os.path.join(BASE_DIR, "data", "vector_store")
EMBEDDING_MODEL = "nomic-embed-text"

def get_embedding_function():
    return OllamaEmbeddings(model=EMBEDDING_MODEL)

def get_db_sources(vector_store):
    """Returns the set of source file paths currently stored in the vector DB."""
    try:
        data = vector_store.get()
        if not data or not data['metadatas']:
            return set()
        return {meta['source'] for meta in data['metadatas'] if 'source' in meta}
    except Exception:
        return set()

def _delete_by_source(vector_store, file_path):
    """Deletes all chunks for a given source file using the public ChromaDB API."""
    results = vector_store.get(where={"source": file_path})
    ids_to_delete = results.get("ids", [])
    if ids_to_delete:
        vector_store.delete(ids=ids_to_delete)

def update_vector_store(documents, interactive=True):
    """
    Smart incremental sync:
    1. Adds chunks for NEW files only.
    2. Removes chunks for DELETED files - asks confirmation when interactive=True,
       skips silently when interactive=False (automated/pipeline mode).
    """
    embedding_function = get_embedding_function()
    vector_store = Chroma(
        persist_directory=VECTOR_STORE_PATH,
        embedding_function=embedding_function
    )

    disk_sources = {doc.metadata['source'] for doc in documents}
    db_sources = get_db_sources(vector_store)

    new_files = disk_sources - db_sources
    deleted_files = db_sources - disk_sources

    print("--- Sync Check ---")
    print(f"Existing in DB: {len(db_sources)}")
    print(f"Found on Disk:  {len(disk_sources)}")
    print(f"To Add:         {len(new_files)}")
    print(f"To Delete:      {len(deleted_files)}")
    print("-" * 20)

    # HANDLE DELETIONS
    if deleted_files:
        print("\n[!] The following files are in the DB but missing from disk:")
        for f in deleted_files:
            print(f" - {os.path.basename(f)}")

        should_delete = True
        if interactive:
            confirm = input("\nDo you want to DELETE these from the database? (y/n): ").strip().lower()
            should_delete = (confirm == 'y')

        if should_delete:
            print("Removing obsolete records...")
            for file_path in deleted_files:
                _delete_by_source(vector_store, file_path)
            print("Cleanup complete.")
        else:
            print("Skipping deletion. Old data remains.")

    # HANDLE ADDITIONS
    if new_files:
        print(f"\nProcessing {len(new_files)} new files...")
        docs_to_add = [doc for doc in documents if doc.metadata['source'] in new_files]
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
    """Returns the ChromaDB retriever (top-3 results)."""
    if not os.path.exists(VECTOR_STORE_PATH):
        raise FileNotFoundError("Vector Store not found. Run ingestion first.")
    vector_store = Chroma(
        persist_directory=VECTOR_STORE_PATH,
        embedding_function=get_embedding_function()
    )
    return vector_store.as_retriever(search_kwargs={"k": 3})