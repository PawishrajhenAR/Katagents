import asyncio
import json
import logging
import re
from abc import ABC, abstractmethod

import httpx

from config import settings

logger = logging.getLogger(__name__)
LLM_TIMEOUT_SECONDS = 60


def _mock_json(prompt: str) -> str:
    lower = prompt.lower()
    if "classify" in lower or "classification" in lower:
        return json.dumps({"classification": "interested", "confidence": 0.8, "reason": "Mock classification"})
    if "subject" in lower or "email" in lower or "outreach email" in lower:
        return json.dumps({
            "subject": "Quick idea for your team",
            "body": (
                "Hi there,\n\n"
                "I noticed your company is doing great work. Would love to connect briefly "
                "and share a few ideas that might be relevant.\n\nBest regards"
            ),
        })
    return json.dumps({
        "summary": "Mock research summary for the prospect and their company.",
        "talking_points": [
            "Recent growth in their space",
            "Role likely focused on scaling outreach",
            "Good fit for a short intro call",
        ],
        "confidence": 0.7,
    })


def _retry_seconds_from_error(exc: Exception) -> float | None:
    match = re.search(r"retry in ([0-9.]+)s", str(exc), re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system: str = "") -> str: ...


class GeminiProvider(LLMProvider):
    async def generate(self, prompt: str, system: str = "") -> str:
        if settings.llm_mock or not settings.gemini_api_key:
            if not settings.llm_mock and not settings.gemini_api_key:
                logger.warning("GEMINI_API_KEY missing — using mock LLM responses")
            return _mock_json(prompt)

        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        try:
            response = await asyncio.wait_for(
                model.generate_content_async(full_prompt),
                timeout=LLM_TIMEOUT_SECONDS,
            )
            return response.text or ""
        except TimeoutError:
            logger.warning("Gemini request timed out; using mock response")
            return _mock_json(prompt)
        except Exception as exc:
            retry_in = _retry_seconds_from_error(exc)
            if retry_in:
                logger.warning(
                    "Gemini quota/rate limit (retry in ~%ss); using mock response. "
                    "Set LLM_MOCK=true to skip API calls, or enable billing / a new key.",
                    int(retry_in),
                )
            else:
                logger.warning("Gemini request failed (%s); using mock response", exc)
            return _mock_json(prompt)


class OpenAICompatProvider(LLMProvider):
    async def generate(self, prompt: str, system: str = "") -> str:
        if settings.llm_mock or not settings.openai_api_key:
            if not settings.llm_mock and not settings.openai_api_key:
                logger.warning("OPENAI_API_KEY missing — using mock LLM responses")
            return _mock_json(prompt)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=LLM_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{settings.openai_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json={"model": settings.openai_model, "messages": messages},
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.warning("OpenAI request failed (%s); using mock response", exc)
            return _mock_json(prompt)


class LLMService:
    def __init__(self):
        self._gemini = GeminiProvider()
        self._openai = OpenAICompatProvider()

    async def generate(self, prompt: str, system: str = "") -> str:
        provider = settings.llm_provider.lower()
        if provider == "openai":
            return await self._openai.generate(prompt, system)
        return await self._gemini.generate(prompt, system)

    async def generate_json(self, prompt: str, system: str = "") -> dict:
        text = await self.generate(prompt, system)
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            if text.endswith("```"):
                text = text[:-3]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}
