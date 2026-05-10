import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level up from this file)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError(
        "GEMINI_API_KEY not found. Please set it in your .env file."
    )

# Use a supported Gemini model from the Google API.
# `gemini-1.5-flash` is not available on the configured API version.
GEMINI_MODEL = "models/gemini-2.5-flash"

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "invoices.csv"
DB_PATH = PROJECT_ROOT / "data" / "audit.db"
