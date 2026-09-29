import asyncio
import json
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.openai_api_key = settings.OPENAI_API_KEY
        self.openai_model = settings.OPENAI_MODEL
        self.ollama_base_url = settings.OLLAMA_BASE_URL
        self.ollama_model = settings.OLLAMA_MODEL

    async def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Generate a complete textual response synchronously/asynchronously from the configured LLM.
        """
        if self.provider == "openai" and self.openai_api_key:
            return await self._call_openai(prompt, system_instruction)
        elif self.provider == "ollama":
            return await self._call_ollama(prompt, system_instruction)
        else:
            return await self._call_mock(prompt, system_instruction)

    async def generate_stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Yields tokens/chunks as they are generated for real-time frontend streaming.
        """
        if self.provider == "openai" and self.openai_api_key:
            async for chunk in self._stream_openai(prompt, system_instruction):
                yield chunk
        elif self.provider == "ollama":
            async for chunk in self._stream_ollama(prompt, system_instruction):
                yield chunk
        else:
            async for chunk in self._stream_mock(prompt, system_instruction):
                yield chunk

    # ==========================================
    # OpenAI Provider
    # ==========================================
    async def _call_openai(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.openai_model,
            "messages": messages,
            "temperature": settings.OPENAI_TEMPERATURE
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _stream_openai(self, prompt: str, system_instruction: Optional[str] = None) -> AsyncGenerator[str, None]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.openai_model,
            "messages": messages,
            "temperature": settings.OPENAI_TEMPERATURE,
            "stream": True
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            json_obj = json.loads(data_str)
                            delta = json_obj["choices"][0]["delta"]
                            if "content" in delta:
                                yield delta["content"]
                        except Exception:
                            continue

    # ==========================================
    # Ollama Provider (Local Model)
    # ==========================================
    async def _call_ollama(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        url = f"{self.ollama_base_url}/api/chat"
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json()["message"]["content"]
        except Exception as e:
            logger.warning(f"Ollama call failed ({e}). Falling back to mock response.")
            return await self._call_mock(prompt, system_instruction)

    async def _stream_ollama(self, prompt: str, system_instruction: Optional[str] = None) -> AsyncGenerator[str, None]:
        url = f"{self.ollama_base_url}/api/chat"
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": True
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk_data = json.loads(line)
                            content = chunk_data.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue
        except Exception as e:
            logger.warning(f"Ollama stream failed ({e}). Falling back to mock stream.")
            async for chunk in self._stream_mock(prompt, system_instruction):
                yield chunk

    # ==========================================
    # Mock Provider (Zero dependency & Immediate testing)
    # ==========================================
    async def _call_mock(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        await asyncio.sleep(0.3)
        return (
            "Com base nas seções identificadas do relatório geofísico, observa-se que as camadas sedimentares "
            "analisadas apresentam variações significativas de resistividade e velocidade intervalar. "
            "Os horizontes refletores sugerem potenciais zonas de interesse geológico para prospecção, "
            "com conformidade estratigráfica confirmada pelos dados dos ensaios de sísmica de reflexão."
        )

    async def _stream_mock(self, prompt: str, system_instruction: Optional[str] = None) -> AsyncGenerator[str, None]:
        simulated_text = (
            "Com base nas seções identificadas do relatório geofísico, observa-se que as camadas sedimentares "
            "analisadas apresentam variações significativas de resistividade e velocidade intervalar. "
            "Os horizontes refletores sugerem potenciais zonas de interesse geológico para prospecção, "
            "com conformidade estratigráfica confirmada pelos dados dos ensaios de sísmica de reflexão."
        )
        words = simulated_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.04)


llm_service = LLMService()
