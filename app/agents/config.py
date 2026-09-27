"""
Agent & Orchestrator Configuration
==================================
Centralized configuration for LLM provider, orchestrator limits, and runtime settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load .env file from project root
load_dotenv(PROJECT_ROOT / ".env")

# LLM Provider Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini" if LLM_PROVIDER == "openrouter" else "gpt-4o-mini")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1" if LLM_PROVIDER == "openrouter" else "")


# Orchestrator Execution Limits
MAX_STEPS = int(os.getenv("ORCHESTRATOR_MAX_STEPS", "8"))
MAX_TOOL_CALLS = int(os.getenv("ORCHESTRATOR_MAX_TOOL_CALLS", "5"))
MAX_RETRIES = int(os.getenv("ORCHESTRATOR_MAX_RETRIES", "1"))

# RAG Settings for Agent
RAG_TOP_K = int(os.getenv("ORCHESTRATOR_RAG_TOP_K", "4"))

# Conversation Memory Settings (Phase 7)
CONVERSATION_DB_PATH = os.getenv("CONVERSATION_DB_PATH", str(PROJECT_ROOT / "data" / "conversations.db"))
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))
