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

# Reasoning-style models (e.g. gpt-5-tp): use only max_completion_tokens; do not send temperature or max_tokens.
# Comma-separated deployment names, or empty to treat no model as reasoning.
AZURE_OPENAI_REASONING_MODELS = os.getenv("AZURE_OPENAI_REASONING_MODELS", "gpt-5-tp").strip().lower().split(",")
AZURE_OPENAI_REASONING_MODELS = [m.strip() for m in AZURE_OPENAI_REASONING_MODELS if m.strip()]
