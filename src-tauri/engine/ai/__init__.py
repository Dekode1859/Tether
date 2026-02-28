from .ollama_client import LLMClient, OLLAMA_MODEL
from .prompts import (
    SYSTEM_PROMPT,
    ENTITY_EXTRACTION_PROMPT,
    ASK_VAULT_PROMPT,
)

__all__ = [
    "LLMClient",
    "OLLAMA_MODEL",
    "SYSTEM_PROMPT",
    "ENTITY_EXTRACTION_PROMPT",
    "ASK_VAULT_PROMPT",
]
