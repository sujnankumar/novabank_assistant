"""
Quick API Key Verification Script
=================================
Tests connectivity to OpenRouter / OpenAI using credentials in .env.
Usage:
    python scripts/test_llm_key.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 1. Load environment variables from .env
project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

provider = os.getenv("LLM_PROVIDER", "openrouter").lower()
model = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
api_key = os.getenv("LLM_API_KEY", "").strip()
base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1" if provider == "openrouter" else "")

print("=" * 65)
print("  NovaBank LLM API Key Validator")
print("=" * 65)
print(f"  Provider : {provider}")
print(f"  Model    : {model}")
print(f"  Base URL : {base_url or 'Default OpenAI URL'}")

if not api_key or "your_" in api_key:
    print("\n[!] LLM_API_KEY is missing or contains placeholder in .env!")
    sys.exit(1)

masked_key = api_key[:12] + "..." + api_key[-4:] if len(api_key) > 16 else "***"
print(f"  API Key  : {masked_key}")
print("-" * 65)
print(f"Connecting to {provider} and testing model '{model}'...")

from langchain_openai import ChatOpenAI

def test_model(model_name: str):
    kwargs = {
        "model": model_name,
        "api_key": api_key,
        "temperature": 0.0,
        "max_tokens": 50,
    }
    if base_url:
        kwargs["base_url"] = base_url

    if provider == "openrouter" or "openrouter" in base_url.lower():
        kwargs["default_headers"] = {
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "NovaBank AI Banking Assistant",
        }

    client = ChatOpenAI(**kwargs)
    res = client.invoke("Reply with exactly: 'API Key is working successfully!'")
    return res.content.strip()

try:
    reply = test_model(model)
    print("\n[SUCCESS] Your API key is VALID and active!")
    print("-" * 65)
    print(f"Model Response: {reply}")
    print("=" * 65)

except Exception as err:
    err_str = str(err)
    print("\n[NOTE] Primary model check returned:")
    print("-" * 65)
    print(err_str)
    print("-" * 65)

    if "402" in err_str or "Insufficient credits" in err_str:
        print("\n=> Your OpenRouter API key IS VALID, but your account currently has")
        print("   $0.00 credits for paid models like '" + model + "'.")
        print("\nLet's test with OpenRouter's free tier model to verify key authentication...")
        try:
            free_model = "nvidia/nemotron-3.5-lightning:free"
            reply = test_model(free_model)
            print(f"\n[SUCCESS] Key Authentication Verified with '{free_model}'!")
            print(f"Response: {reply}")
            print("\nOptions:")
            print(f"1. To use without adding money, update .env with:")
            print(f"   LLM_MODEL={free_model}")
            print("2. Or add credits at: https://openrouter.ai/settings/credits")
            print("   and continue using openai/gpt-4o-mini.")
        except Exception as free_err:
            print(f"[!] Free model test error: {free_err}")
    elif "401" in err_str:
        print("[!] 401 Unauthorized: Invalid API key. Please check your key on openrouter.ai.")
    elif "404" in err_str:
        print(f"[!] 404 Not Found: Model '{model}' not found on OpenRouter.")
