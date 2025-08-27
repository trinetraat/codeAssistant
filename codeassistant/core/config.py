import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

HOME = Path.home()
APP_DIR = HOME / ".codeassistant"
SESS_DIR = APP_DIR / "sessions"
OUT_DIR  = APP_DIR / "outputs"
SESS_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_MODEL = os.getenv("CA_DEFAULT_MODEL", "gpt-5-mini")

# pricing per 1M tokens USD (edit if needed)
PRICING = {
    "gpt-4.1":      {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output":  1.60},
    # add others as needed:
    # "o4-mini":      {"input": 1.10, "output":  4.40},
    "gpt-5-mini": {"input": 0.25, "output":  2.00},
    "gpt-5": {"input": 1.25, "output":  10.00},
}

def get_api_env():
    load_dotenv(dotenv_path=Path.cwd()/".env", override=True)
    return {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY"),
        "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
    }