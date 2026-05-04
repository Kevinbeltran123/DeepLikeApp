"""Async HTTP client for Ollama's REST API.

Wraps /api/generate (used by pipeline mode) and /api/tags (used by health check).
Multi-agent and mono-agent modes go through langchain_ollama.ChatOllama instead,
since LangChain expects its own message types.
"""

import json
from typing import AsyncIterator

import httpx

from app.config import get_settings


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None):
        settings = get_settings()
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.llm_model
        self.timeout = settings.llm_timeout_seconds

    async def stream_generate(
        self,
        prompt: str,
        temperature: float = 0.1,
        top_p: float = 0.9,
        repeat_penalty: float = 1.1,
    ) -> AsyncIterator[str]:
        """Stream tokens from Ollama's /api/generate endpoint."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "repeat_penalty": repeat_penalty,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done"):
                        return

    async def list_models(self) -> list[str]:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]

    async def is_reachable(self) -> bool:
        try:
            await self.list_models()
            return True
        except Exception:
            return False
