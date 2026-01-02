#
# Ingest Data Script
# This script dynamically loads documents from specified folders,
# splits them into chunks, generates embeddings using Ollama,
# and stores them in a Chroma vector store.
# to run the code python src/ingest_data.py
#
from dotenv import load_dotenv
from tools.file_ops import load_documents_dynamically
from tools.knowledge_base import update_vector_store

# Load environment variables
load_dotenv()

def main():
    print("--- Starting Data Ingestion Process ---")

    # 1. Call the "Supplier" (File Ops) to get documents
    documents = load_documents_dynamically()

    # 2. Call the "Pantry" (Knowledge Base) to store them
    if documents:
        update_vector_store(documents)
    else:
        print("\n No documents found. Process finished without updates.")

if __name__ == "__main__":
    main()