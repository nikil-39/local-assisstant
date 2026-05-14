"""
AI Integration Module - Supports OpenAI, Google Gemini, Anthropic Claude,
and custom endpoints with automatic fallback to local responses.
"""

import os
import json
import logging
from abc import ABC, abstractmethod

from PyQt6.QtCore import QObject, pyqtSignal, QThread

logger = logging.getLogger("jarvis.ai")


class AIProvider(ABC):
    """Base class for AI providers."""

    @abstractmethod
    def chat(self, messages: list[dict], max_tokens: int = 500) -> str | None:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...


class OpenAIProvider(AIProvider):
    """OpenAI-compatible API provider (works with OpenAI, Azure, LM Studio, etc.)."""

    def __init__(self, api_key: str, base_url: str, model: str, proxy: str | None = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.proxy = proxy
        self._available = False
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            import httpx
            kwargs = {"timeout": 30.0, "verify": False}
            if self.proxy:
                kwargs["proxy"] = self.proxy
            self._client = httpx.Client(**kwargs)
            self._available = True
        except Exception as e:
            logger.warning(f"Failed to init OpenAI provider: {e}")
            self._available = False

    def chat(self, messages: list[dict], max_tokens: int = 500) -> str | None:
        if not self._available or not self._client:
            return None
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7,
            }
            resp = self._client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    def is_available(self) -> bool:
        return self._available


class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._available = False
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            import httpx
            self._client = httpx.Client(timeout=30.0)
            self._available = bool(self.api_key)
        except Exception as e:
            logger.warning(f"Failed to init Anthropic provider: {e}")

    def chat(self, messages: list[dict], max_tokens: int = 500) -> str | None:
        if not self._available or not self._client:
            return None
        try:
            # Convert from OpenAI format to Anthropic format
            system_msg = ""
            user_messages = []
            for m in messages:
                if m["role"] == "system":
                    system_msg = m["content"]
                else:
                    user_messages.append({"role": m["role"], "content": m["content"]})

            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            }
            payload = {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": max_tokens,
                "messages": user_messages,
            }
            if system_msg:
                payload["system"] = system_msg

            resp = self._client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return None

    def is_available(self) -> bool:
        return self._available


class GeminiProvider(AIProvider):
    """Google Gemini API provider."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._available = False
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            import httpx
            self._client = httpx.Client(timeout=30.0)
            self._available = bool(self.api_key)
        except Exception as e:
            logger.warning(f"Failed to init Gemini provider: {e}")

    def chat(self, messages: list[dict], max_tokens: int = 500) -> str | None:
        if not self._available or not self._client:
            return None
        try:
            # Build Gemini-format content
            contents = []
            system_instruction = None
            for m in messages:
                if m["role"] == "system":
                    system_instruction = m["content"]
                else:
                    role = "user" if m["role"] == "user" else "model"
                    contents.append({"role": role, "parts": [{"text": m["content"]}]})

            payload = {
                "contents": contents,
                "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7},
            }
            if system_instruction:
                payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            resp = self._client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None

    def is_available(self) -> bool:
        return self._available


class LocalFallback(AIProvider):
    """Offline fallback with canned responses."""

    RESPONSES = {
        "joke": [
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "There are 10 types of people: those who understand binary and those who don't.",
            "A SQL query walks into a bar, sees two tables, and asks... 'Can I JOIN you?'",
            "Why was the JavaScript developer sad? Because he didn't Node how to Express himself.",
        ],
        "greeting": "Hello! I'm Jarvis, your desktop assistant. I'm running in offline mode right now.",
        "weather": "I'm sorry, I can't check the weather in offline mode. Please configure an AI provider in settings.",
        "unknown": "I'm running in offline mode. I can still help with system commands like opening apps, searching the web, and managing files. For AI-powered responses, please configure an API key in settings.",
    }

    def __init__(self):
        self._joke_index = 0

    def chat(self, messages: list[dict], max_tokens: int = 500) -> str | None:
        last_msg = messages[-1]["content"].lower() if messages else ""
        if any(w in last_msg for w in ["joke", "funny", "laugh"]):
            joke = self.RESPONSES["joke"][self._joke_index % len(self.RESPONSES["joke"])]
            self._joke_index += 1
            return joke
        if any(w in last_msg for w in ["hello", "hi ", "hey", "greet"]):
            return self.RESPONSES["greeting"]
        if "weather" in last_msg:
            return self.RESPONSES["weather"]
        return self.RESPONSES["unknown"]

    def is_available(self) -> bool:
        return True


class AIWorker(QThread):
    """Runs AI inference on a background thread."""
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, provider: AIProvider, messages: list[dict], max_tokens: int = 500):
        super().__init__()
        self.provider = provider
        self.messages = messages
        self.max_tokens = max_tokens

    def run(self):
        try:
            result = self.provider.chat(self.messages, self.max_tokens)
            if result:
                self.response_ready.emit(result)
            else:
                self.error_occurred.emit("No response from AI provider.")
        except Exception as e:
            self.error_occurred.emit(str(e))


class AIManager(QObject):
    """Manages AI providers with automatic fallback chain."""

    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self.providers: list[AIProvider] = []
        self.conversation_history: list[dict] = []
        self.system_prompt = settings.get("system_prompt", "You are Jarvis, a helpful AI desktop assistant.")
        self._worker = None
        self._init_providers()

    def _init_providers(self):
        """Initialize providers in priority order based on available API keys."""
        provider_name = self.settings.get("provider", "openai")

        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if openai_key:
            self.providers.append(OpenAIProvider(
                api_key=openai_key,
                base_url=self.settings.get("openai_base_url", "https://api.openai.com/v1"),
                model=self.settings.get("openai_model", "gpt-4o-mini"),
            ))
            logger.info("OpenAI provider initialized")

        # Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        if anthropic_key:
            self.providers.append(AnthropicProvider(api_key=anthropic_key))
            logger.info("Anthropic provider initialized")

        # Gemini
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if gemini_key:
            self.providers.append(GeminiProvider(api_key=gemini_key))
            logger.info("Gemini provider initialized")

        # Always add local fallback last
        self.providers.append(LocalFallback())
        logger.info(f"AI manager ready with {len(self.providers)} providers (preferred: {provider_name})")

    def get_active_provider(self) -> AIProvider:
        """Get the first available provider."""
        for p in self.providers:
            if p.is_available():
                return p
        return self.providers[-1]  # fallback

    def ask(self, user_message: str):
        """Send a message to the AI asynchronously."""
        self.conversation_history.append({"role": "user", "content": user_message})

        # Keep history manageable
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-16:]

        messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history

        provider = self.get_active_provider()
        self._worker = AIWorker(provider, messages, self.settings.get("max_tokens", 500))
        self._worker.response_ready.connect(self._on_response)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def ask_sync(self, user_message: str) -> str:
        """Synchronous version for command processing."""
        self.conversation_history.append({"role": "user", "content": user_message})
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-16:]

        messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history
        provider = self.get_active_provider()
        result = provider.chat(messages, self.settings.get("max_tokens", 500))
        if result:
            self.conversation_history.append({"role": "assistant", "content": result})
            return result
        return "I couldn't generate a response. Please try again."

    def _on_response(self, text: str):
        self.conversation_history.append({"role": "assistant", "content": text})
        self.response_ready.emit(text)

    def _on_error(self, error: str):
        logger.error(f"AI error: {error}")
        self.error_occurred.emit(error)

    def clear_history(self):
        self.conversation_history.clear()
