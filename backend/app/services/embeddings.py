from __future__ import annotations

import httpx

from app.config import settings


class Embedder:
    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        out = []
        for t in texts:
            out.append(await self.embed(t))
        return out


class GeminiEmbedder(Embedder):
    def __init__(self, api_key: str, model: str = "text-embedding-004"):
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._genai = genai
        self.model = model

    async def embed(self, text: str) -> list[float]:
        res = self._genai.embed_content(model=f"models/{self.model}", content=text)
        return list(res["embedding"])


class OllamaEmbedder(Embedder):
    def __init__(self, base_url: str, model: str = "nomic-embed-text"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            r.raise_for_status()
            return r.json()["embedding"]


def get_embedder() -> Embedder:
    if settings.embedding_provider == "ollama":
        return OllamaEmbedder(settings.ollama_base_url, settings.ollama_embedding_model)
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY not set; set EMBEDDING_PROVIDER=ollama or provide key")
    return GeminiEmbedder(settings.gemini_api_key, settings.gemini_embedding_model)
