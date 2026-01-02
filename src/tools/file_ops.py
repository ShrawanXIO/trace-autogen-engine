import os
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, TextLoader, Docx2txtLoader

# 1. Calculate the Root Directory so we always know where 'data/' is
# (We go up 3 levels: file_ops.py -> tools -> src -> ROOT)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 2. Define the folders we want to scan
TARGET_FOLDERS = [
    os.path.join(BASE_DIR, "data", "inputs", "ApplicationDocuments"),
    os.path.join(BASE_DIR, "data", "inputs", "Existingtestcases")
]

# 3. Map file extensions to the correct LangChain Loader
LOADER_MAPPING = {
    ".pdf": PyPDFLoader,
    ".csv": CSVLoader,
    ".txt": TextLoader,
    ".docx": Docx2txtLoader, 
    ".md": TextLoader
}

def load_documents_dynamically():
    """
    Scans the specific data folders and returns a list of loaded LangChain documents.
    """
    all_documents = []
    
    print("--- Tool: Scanning Folders ---")
    
    for folder_path in TARGET_FOLDERS:
        print(f"Checking: {folder_path}")
        
        if not os.path.exists(folder_path):
            print(f"Directory not found: {folder_path}")
            continue
            
        try:
            files_in_folder = os.listdir(folder_path)
        except OSError as e:
            print(f"Error accessing directory: {e}")
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
                try:
                    loader = loader_class(file_path)
                    all_documents.extend(loader.load())
                    print(f"  -> Loaded: {filename}")
                except Exception as e:
                    print(f"  -> Error loading {filename}: {e}")

    return all_documents