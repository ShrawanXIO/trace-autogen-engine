import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

# Load environment variables
load_dotenv()

# Define Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Folders to scan
TARGET_FOLDERS = [
    os.path.join(BASE_DIR, "data", "inputs", "ApplicationDocuments"),
    os.path.join(BASE_DIR, "data", "inputs", "Existingtestcases")
]

VECTOR_STORE_PATH = os.path.join(BASE_DIR, "data", "vector_store")

# Map file extensions to their specific Loaders
LOADER_MAPPING = {
    ".pdf": PyPDFLoader,
    ".csv": CSVLoader,
    ".txt": TextLoader,
    ".docx": Docx2txtLoader, 
    ".md": TextLoader
}

def load_documents_dynamically():
    all_documents = []
    
    print("--- Scanning Folders ---")
    
    for folder_path in TARGET_FOLDERS:
        print(f"\nChecking folder: {folder_path}")
        
        if not os.path.exists(folder_path):
            print(f"Directory not found: {folder_path}")
            continue
            
        # List all files in the directory
        try:
            files_in_folder = os.listdir(folder_path)
        except OSError as e:
            print(f"Error accessing directory: {e}")
            continue
        
        if not files_in_folder:
             print("Folder is empty.")
             continue

        for filename in files_in_folder:
            file_path = os.path.join(folder_path, filename)
            
            # Skip hidden files or directories
            if filename.startswith(".") or os.path.isdir(file_path):
                continue

            # Get extension
            ext = os.path.splitext(filename)[1].lower()

            if ext in LOADER_MAPPING:
                loader_class = LOADER_MAPPING[ext]
                print(f"Found {ext} file: {filename} -> Using {loader_class.__name__}")
                
                try:
                    loader = loader_class(file_path)
                    all_documents.extend(loader.load())
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
            else:
                print(f"Skipping unsupported file type: {filename}")

    return all_documents

def ingest_data():
    # 1. Load Files based on directory contents
    documents = load_documents_dynamically()

    if not documents:
        print("\nNo supported documents found in any folder. Exiting process.")
        return

    # 2. Split Text (Chunking)
    print(f"\nProcessing {len(documents)} document pages/rows...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} text chunks.")

    # 3. Embed & Store
    print("Generating Embeddings (Model: nomic-embed-text)...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    vector_store = Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings, 
        persist_directory=VECTOR_STORE_PATH
    )
    print(f"Vector Store successfully updated at: {VECTOR_STORE_PATH}")

if __name__ == "__main__":
    ingest_data()