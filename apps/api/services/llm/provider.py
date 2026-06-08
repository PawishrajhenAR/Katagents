import json
from abc import ABC, abstractmethod

import httpx

from config import settings


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system: str = "") -> str: ...


class GeminiProvider(LLMProvider):
    async def generate(self, prompt: str, system: str = "") -> str:
        if not settings.gemini_api_key:
            return self._mock_response(prompt)

        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = await model.generate_content_async(full_prompt)
        return response.text or ""

    def _mock_response(self, prompt: str) -> str:
        if "classify" in prompt.lower() or "classification" in prompt.lower():
            return json.dumps({"classification": "interested", "confidence": 0.8, "reason": "Mock classification"})
        if "subject" in prompt.lower() or "email" in prompt.lower():
            return json.dumps({
                "subject": "Quick idea for your team",
                "body": "Hi there,\n\nI noticed your company is doing great work. Would love to connect.\n\nBest regards",
            })
        return json.dumps({"summary": "Mock research summary for the prospect.", "confidence": 0.7})


class OpenAICompatProvider(LLMProvider):
    async def generate(self, prompt: str, system: str = "") -> str:
        if not settings.openai_api_key:
            return GeminiProvider()._mock_response(prompt)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.openai_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={"model": "gpt-4o-mini", "messages": messages},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]


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
