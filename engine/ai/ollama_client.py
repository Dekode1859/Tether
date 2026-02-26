from typing import Optional
import httpx

OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "llama3"


class LLMClient:
    """Client for interacting with local Ollama LLM."""

    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL):
        self.host = host
        self.model = model
        self._client = None

    def _get_client(self):
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(timeout=120.0)
        return self._client

    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Send a query to Ollama."""
        client = self._get_client()

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        if system_prompt:
            payload["system"] = system_prompt

        response = client.post(f"{self.host}/api/generate", json=payload)
        response.raise_for_status()

        result = response.json()
        return result.get("response", "")

    async def query_async(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Async wrapper for query."""
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.query, prompt, system_prompt)

    def is_available(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            client = self._get_client()
            response = client.get(f"{self.host}/api/tags")
            return response.status_code == 200
        except Exception:
            return False
