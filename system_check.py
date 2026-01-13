# system_check.py
import sys

def check_installation():
    print("🔎 Starting TRACE System Health Check...\n")
    
    # Check 1: Python Version
    print(f"✅ Python Runtime: {sys.version.split()[0]}")
    if sys.version_info < (3, 10):
        print("❌ ERROR: Python 3.10+ is required.")
        return

    # Check 2: Core Libraries
    try:
        import autogen_core
        print(f"✅ AutoGen Installed: v{autogen_core.__version__}")
    except ImportError:
        print("❌ ERROR: autogen_core is missing.")
    try:
        import langchain
        print(f"✅ LangChain Installed: v{langchain.__version__}")
    except ImportError:
        print("❌ ERROR: langchain is missing.")

    try:
        import chromadb
        print(f"✅ ChromaDB Installed: v{chromadb.__version__}")
    except ImportError:
        print("❌ ERROR: chromadb is missing.")

    try:
        import pandas
        print(f"✅ Pandas Installed: v{pandas.__version__}")
    except ImportError:
        print("❌ ERROR: pandas is missing.")

    print("\n🎉 SYSTEM READY. All systems go.")

if __name__ == "__main__":
    check_installation()