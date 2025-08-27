import os, sys
from openai import OpenAI

def make_client_or_die():
    try:
        # Works for OpenAI or Azure OpenAI if env vars are set appropriately
        return OpenAI()
    except Exception as e:
        print(f"❌ OpenAI client init failed: {e}")
        sys.exit(1)