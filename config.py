"""Azure OpenAI config loaded from environment (.env)."""
import os
from pathlib import Path

# Load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "06c6e66af3fd464585238158c630be45")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://rschtech-np-eastus2.openai.azure.com/")
AZURE_OPENAI_VERSION = os.getenv("AZURE_OPENAI_VERSION", "2025-04-01-preview")
AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-4")
