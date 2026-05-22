import os
import sys
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
load_dotenv()

#  MASTER SWITCH: "ollama" or "openai"
LLM_PROVIDER = "ollama" 

if LLM_PROVIDER not in ["ollama", "openai"]:
    print(f"CRITICAL ERROR: LLM_PROVIDER '{LLM_PROVIDER}' is invalid. Must be 'ollama' or 'openai'.")
    sys.exit(1)

# MODEL MAPPING (The Brains)
MODELS = {
    "ollama": {
        "manager": "ministral-3:14b-cloud",  # Fast orchestrator
        "archivist": "ministral-3:14b-cloud", # Fast retrieval
        "author": "ministral-3:14b-cloud",    # Good creative writing
        "auditor": "gemma3:27b-cloud",        # High IQ logic checker
        "scribe": "ministral-3:14b-cloud"     # JSON formatting
    },
    "openai": {
        "manager": "gpt-4o",
        "archivist": "gpt-4o-mini",
        "author": "gpt-4o",
        "auditor": "gpt-4o",
        "scribe": "gpt-4o-mini"
    }
}

TEMPERATURES = {
    "manager": 0.1,    # Precise instruction following
    "archivist": 0.0,  # Exact retrieval only
    "author": 0.7,     # CREATIVE: Needs to write human-like steps
    "auditor": 0.0,    # STRICT: Logic checking must be robotic
    "scribe": 0.0      # STRICT: JSON formatting must not fail
}
# If using OpenAI, set key here or in Environment Variables
##OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-proj-...")

def get_llm(role):
    """
    Returns the connection. Fails loud if configs are missing.
    """
    if not role:
        raise ValueError("Error: 'role' is required for get_llm.")

    # A. Validate Configuration Exists
    if role not in TEMPERATURES:
        raise ValueError(f"Error: Role '{role}' missing in TEMPERATURES config.")
    
    provider_models = MODELS.get(LLM_PROVIDER)
    
    # --- FIX: Check if provider exists before checking role ---
    if provider_models is None:
        raise ValueError(f"Error: LLM_PROVIDER '{LLM_PROVIDER}' is not defined in MODELS config.")

    if role not in provider_models:
        raise ValueError(f"Error: Role '{role}' missing in MODELS['{LLM_PROVIDER}'] config.")

    # B. Get Settings
    model_name = provider_models[role]
    temp = TEMPERATURES[role]

    # C. Connect
    if LLM_PROVIDER == "openai":
        # Only import OpenAI if we are actually using it
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError("Error: Run 'pip install langchain-openai' to use OpenAI.")

        # We keep os.getenv here ONLY for the key (Security Best Practice)
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Error: OPENAI_API_KEY is missing in .env file.")
            
        return ChatOpenAI(model=model_name, api_key=api_key, temperature=temp)

    else:
        # Default to Ollama
        print(f"   [SYSTEM] Connecting {role.upper()} -> {model_name} (Temp: {temp})")
        return ChatOllama(model=model_name, temperature=temp)