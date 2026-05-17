"""
AI Integration Module - Supports OpenAI, Google Gemini, Anthropic Claude,
and custom endpoints with automatic fallback to local responses.
"""

import os
import re
import json
import logging
import difflib
from datetime import datetime
from pathlib import Path
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
            self._client = httpx.Client(timeout=30.0, trust_env=False)
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


class OllamaProvider(AIProvider):
    """Local Ollama provider (offline, no API key required)."""

    def __init__(self, model: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._available = False
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            import httpx
            # Bypass any system proxy for localhost — proxy env vars like HTTP_PROXY
            # often have invalid ports (e.g. ':*') that cause httpx to crash.
            self._client = httpx.Client(
                timeout=120.0,
                proxy=None,
                trust_env=False,  # ignore HTTP_PROXY / HTTPS_PROXY env vars
            )
            resp = self._client.get(f"{self.base_url}/api/tags", timeout=5.0)
            if resp.status_code == 200:
                available_models = [m["name"] for m in resp.json().get("models", [])]
                base_name = self.model.split(":")[0]
                if any(self.model == m or m.startswith(base_name) for m in available_models):
                    self._available = True
                    logger.info(f"Ollama provider ready: {self.model}")
                else:
                    logger.warning(f"Ollama model '{self.model}' not found. Available: {available_models}")
        except Exception as e:
            logger.warning(f"Ollama not reachable: {e}")

    def chat(self, messages: list[dict], max_tokens: int = 500) -> str | None:
        if not self._available or not self._client:
            return None
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.3},
            }
            resp = self._client.post(f"{self.base_url}/api/chat", json=payload, timeout=120.0)
            resp.raise_for_status()
            return resp.json()["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
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
    # Emitted after speech correction: (original_raw_text, corrected_text)
    speech_corrected = pyqtSignal(str, str)

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self.providers: list[AIProvider] = []
        self.conversation_history: list[dict] = []
        self.system_prompt = settings.get("system_prompt", "You are Jarvis, a helpful AI desktop assistant.")
        self._worker = None
        self._rephrase_worker = None
        # Dedicated fast local model for STT correction (avoids blocking large model)
        self._correction_provider: AIProvider | None = None
        # Persistent corrections cache — sectioned by domain
        # File: config/stt_corrections.json
        # Sections: "webpage", "apps", "briefing", "general"
        self._corrections_cache_path = Path(__file__).parent.parent / "config" / "stt_corrections.json"
        # Append-only audit log: every attempt with success/failure flag
        self._corrections_log_path = Path(__file__).parent.parent / "config" / "stt_corrections_log.jsonl"
        self._corrections_cache: dict[str, str] = self._load_corrections_cache()
        self._general_cache: dict[str, str] = self._load_general_cache()
        self._init_providers()

    def _init_providers(self):
        """Initialize providers in priority order. Ollama first (local), then cloud, then fallback."""

        # ── Ollama (local, no API key needed) ───────────────────────────
        if self.settings.get("ollama_enabled", True):
            ollama_model = self.settings.get("ollama_model", "qwen2.5:32b")
            ollama_url = self.settings.get("ollama_base_url", "http://localhost:11434")
            ollama = OllamaProvider(model=ollama_model, base_url=ollama_url)
            if ollama.is_available():
                self.providers.append(ollama)
                logger.info(f"Ollama provider initialized: {ollama_model}")

            # Separate fast model for STT correction
            correction_model = self.settings.get("ollama_correction_model", "llama3.1:8b")
            if correction_model != ollama_model:
                correction_ollama = OllamaProvider(model=correction_model, base_url=ollama_url)
                if correction_ollama.is_available():
                    self._correction_provider = correction_ollama
                    logger.info(f"STT correction provider: {correction_model}")
            if self._correction_provider is None and ollama.is_available():
                self._correction_provider = ollama

        # ── OpenAI ──────────────────────────────────────────────────────
        openai_key = os.getenv("OPENAI_API_KEY", "") or self.settings.get("openai_api_key", "")
        if openai_key:
            self.providers.append(OpenAIProvider(
                api_key=openai_key,
                base_url=self.settings.get("openai_base_url", "https://api.openai.com/v1"),
                model=self.settings.get("openai_model", "gpt-4o-mini"),
            ))
            logger.info("OpenAI provider initialized")

        # ── Anthropic ───────────────────────────────────────────────────
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "") or self.settings.get("anthropic_api_key", "")
        if anthropic_key:
            self.providers.append(AnthropicProvider(api_key=anthropic_key))
            logger.info("Anthropic provider initialized")

        # ── Google Gemini ───────────────────────────────────────────────
        gemini_key = os.getenv("GEMINI_API_KEY", "") or self.settings.get("gemini_api_key", "")
        if gemini_key:
            self.providers.append(GeminiProvider(api_key=gemini_key))
            logger.info("Gemini provider initialized")
            if self._correction_provider is None:
                self._correction_provider = self.providers[-1]

        # ── Always add local fallback last ───────────────────────────────
        self.providers.append(LocalFallback())
        logger.info(f"AI manager ready with {len(self.providers)} providers")

    def get_active_provider(self) -> AIProvider:
        """Get the first available provider."""
        for p in self.providers:
            if p.is_available():
                return p
        return self.providers[-1]  # fallback

    # Keywords/phrases that should NEVER be "corrected" by AI — they are valid commands.
    _PASSTHROUGH_PATTERNS = re.compile(
        r"\b("
        r"briefing|newspaper|morning briefing|give briefing"
        r"|visit\s+web\s*page"
        r"|open\s+\w+|launch\s+\w+|start\s+\w+|close\s+\w+"
        r"|search\s+|google\s+"
        r"|screenshot|take a screenshot"
        r"|volume\s+(up|down|mute|\d+)|set volume|mute|unmute"
        r"|what time|what date|what day|what is the time"
        r"|system info|battery|cpu|memory|disk|ip address"
        r"|help|exit|quit|bye|goodbye"
        r"|hello|hi|hey|good morning|good afternoon|good evening"
        r"|tell me a joke|joke"
        r"|clear history|lock screen|lock pc"
        r"|play music|pause music|stop music"
        r"|list processes|show tasks"
        r"|weather"
        r")\b",
        re.IGNORECASE,
    )

    def _is_clear_command(self, text: str) -> bool:
        """Return True if text already matches a known command — no AI correction needed."""
        return bool(self._PASSTHROUGH_PATTERNS.search(text))

    # ── Corrections cache ──────────────────────────────────────────
    #
    # config/stt_corrections.json structure:
    # {
    #   "webpage":  { "<garbled>": "<correct>" },
    #   "apps":     { "<garbled>": "<correct>" },
    #   "briefing": { "<garbled>": "<correct>" }
    # }
    #
    # Edit any section manually to fix wrong entries or add new ones.
    # Jarvis reloads the file on the NEXT startup automatically.

    _EMPTY_SECTIONS: dict = {"webpage": {}, "apps": {}, "briefing": {}, "general": {}}

    def _load_corrections_cache(self) -> dict[str, str]:
        """Load the 'webpage' section from the sectioned stt_corrections.json."""
        try:
            if self._corrections_cache_path.exists():
                data = json.loads(self._corrections_cache_path.read_text(encoding="utf-8"))
                # Skip _readme comment keys
                cache = {k: v for k, v in data.get("webpage", {}).items()
                         if not k.startswith("_")}
                logger.info(f"Corrections cache loaded: {len(cache)} webpage entries")
                return cache
        except Exception as e:
            logger.warning(f"Could not load corrections cache: {e}")
        return {}

    def _load_general_cache(self) -> dict[str, str]:
        """Load the 'general' section from stt_corrections.json."""
        try:
            if self._corrections_cache_path.exists():
                data = json.loads(self._corrections_cache_path.read_text(encoding="utf-8"))
                cache = {k: v for k, v in data.get("general", {}).items()
                         if not k.startswith("_")}
                logger.info(f"Corrections cache loaded: {len(cache)} general entries")
                return cache
        except Exception as e:
            logger.warning(f"Could not load general corrections cache: {e}")
        return {}

    def _read_full_corrections_file(self) -> dict:
        """Read the full sectioned JSON, returning defaults if missing/corrupt."""
        if self._corrections_cache_path.exists():
            try:
                return json.loads(self._corrections_cache_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {k: {} for k in self._EMPTY_SECTIONS}

    def _lookup_corrections_cache(self, raw_text: str, cache: dict[str, str] | None = None) -> str | None:
        """Return a known-good correction for raw_text from the given cache, or None."""
        if cache is None:
            cache = self._corrections_cache
        key = raw_text.lower().strip()
        # 1. Exact hit
        if key in cache:
            logger.info(f"Corrections cache exact hit: '{raw_text}' \u2192 '{cache[key]}'")
            return cache[key]
        # 2. Fuzzy hit (same garbled phrase with slight variation)
        matches = difflib.get_close_matches(key, list(cache.keys()), n=1, cutoff=0.82)
        if matches:
            result = cache[matches[0]]
            logger.info(f"Corrections cache fuzzy hit: '{raw_text}' ≈ '{matches[0]}' → '{result}'")
            return result
        return None

    def save_webpage_correction(self, raw_text: str, corrected: str) -> None:
        """Write a VERIFIED correction into the 'webpage' section of stt_corrections.json.

        Called only after the agent confirms it successfully opened something.
        The file is human-editable. Sections: webpage, apps, briefing.
        """
        if not raw_text or not corrected:
            return
        key = raw_text.lower().strip()
        val = corrected.strip()
        if key == val or self._corrections_cache.get(key) == val:
            return  # nothing new to save
        self._corrections_cache[key] = val
        try:
            self._corrections_cache_path.parent.mkdir(parents=True, exist_ok=True)
            data = self._read_full_corrections_file()
            # Ensure all sections exist
            for section in self._EMPTY_SECTIONS:
                data.setdefault(section, {})
            data["webpage"][key] = val
            self._corrections_cache_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.info(f"Corrections cache saved [webpage]: '{raw_text}' → '{corrected}' ({len(data['webpage'])} entries)")
        except Exception as e:
            logger.error(f"Failed to save corrections cache: {e}")

    def log_webpage_attempt(
        self,
        raw_vosk: str,
        ai_corrected: str,
        action_taken: str,
        success: bool,
        source: str = "ai",   # "ai" | "cache" | "passthrough"
    ) -> None:
        """Append one record to stt_corrections_log.jsonl.

        Every voice attempt in webpage-context is logged here regardless of
        success so the user can review, spot mistakes, and manually fix the
        cache (stt_corrections.json → \"webpage\" section).

        Log schema:
            ts          – ISO timestamp
            context     – which agent/section this belongs to (e.g. 'webpage')
            raw         – exactly what Vosk transcribed
            corrected   – what the AI (or cache) mapped it to
            opened      – the final string the agent acted on
            success     – true if the agent actually opened something
            source      – where the corrected value came from
        """
        record = {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "context": "webpage",
            "raw": raw_vosk,
            "corrected": ai_corrected,
            "opened": action_taken,
            "success": success,
            "source": source,
        }
        try:
            self._corrections_log_path.parent.mkdir(parents=True, exist_ok=True)
            with self._corrections_log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            status = "SUCCESS" if success else "FAILURE"
            logger.info(
                f"Correction log [{status}]: '{raw_vosk}' → '{ai_corrected}' (opened: '{action_taken}')"
            )
        except Exception as e:
            logger.error(f"Failed to write corrections log: {e}")

    def rephrase_speech(self, raw_text: str, context: str | None = None):
        """Async STT correction: fixes speech recognition errors then emits speech_corrected(original, corrected).

        Args:
            raw_text: Raw transcription from Vosk.
            context:  Optional hint about what kind of input we're expecting.
                      'webpage' → use a Jira/Bitbucket-aware correction prompt.

        Uses a fast local model (llama3.1:8b) or Gemini if Ollama is unavailable.
        If no AI provider is available beyond LocalFallback, emits immediately with raw_text unchanged.
        """
        # When a specific context is active we ALWAYS attempt correction because
        # the garbled text may accidentally match an unrelated passthrough pattern.
        if context is None and self._is_clear_command(raw_text):
            logger.info(f"STT text already matches a command, skipping correction: '{raw_text}'")
            self.speech_corrected.emit(raw_text, raw_text)
            return

        # ── Corrections cache (instant, no AI call needed) ──────────────────
        if context == "webpage":
            cached = self._lookup_corrections_cache(raw_text, self._corrections_cache)
            if cached:
                self._log_general_correction(raw_text, cached, source="cache", context="webpage")
                self.speech_corrected.emit(raw_text, cached)
                return
        elif context is None:
            # Check general corrections cache before sending to AI
            cached = self._lookup_corrections_cache(raw_text, self._general_cache)
            if cached:
                logger.info(f"General cache hit: '{raw_text}' \u2192 '{cached}'")
                self._log_general_correction(raw_text, cached, source="cache", context="general")
                self.speech_corrected.emit(raw_text, cached)
                return
        # ───────────────────────────────────────────

        correction_provider = self._correction_provider or self.get_active_provider()

        # LocalFallback can't do corrections - pass through unchanged
        if isinstance(correction_provider, LocalFallback):
            logger.info(f"No real AI provider for STT correction, passing through: '{raw_text}'")
            self.speech_corrected.emit(raw_text, raw_text)
            return

        logger.info(f"STT correction requested via {type(correction_provider).__name__}: '{raw_text}' (context={context!r})")

        # ── Build context-specific system prompt ──────────────────────────────
        if context == "webpage":
            # Build a full repo list with both folder name and kebab slug
            try:
                _git = Path(r"C:\Git")
                if _git.exists():
                    _repo_entries = []
                    for d in sorted(_git.iterdir()):
                        if d.is_dir():
                            # kebab slug: lowercase, underscores/spaces → hyphens
                            slug = re.sub(r"[\s_]+", "-", d.name.lower())
                            slug = re.sub(r"[^a-z0-9\-]", "", slug).strip("-")
                            entry = d.name if slug == d.name.lower() else f"{d.name} ({slug})"
                            _repo_entries.append(entry)
                    _repos = ", ".join(_repo_entries)
                else:
                    _repos = "pipelines, cx-data-visualization, asmp-dev"
            except Exception:
                _repos = "pipelines, cx-data-visualization, asmp-dev, pipeline-tools"

            system_content = (
                "You are a speech-to-text error corrector for a voice assistant. "
                "The assistant just asked: 'Which page would you like to open?' "
                "The user spoke a page name but the microphone garbled it badly. "
                "Your job: recover the EXACT page or Bitbucket repository they meant.\n\n"
                "The user can say:\n"
                "  - 'jira'                    → Jira dashboard\n"
                "  - 'kanban board'            → Kanban sprint board\n"
                "  - 'ci cd board' / 'cicd'   → CI/CD pipeline board\n"
                "  - '[repo name] in bitbucket' → open that Bitbucket repository\n\n"
                f"ALL known repositories (folder name and URL slug): {_repos}\n\n"
                "Phonetic garbling examples (STT output → true intent):\n"
                "  'biplanes in be bigot'          → 'pipelines in bitbucket'\n"
                "  'pipe lines in big cat'         → 'pipelines in bitbucket'\n"
                "  'he is simply dove in bigot'    → 'asmp-dev in bitbucket'\n"
                "  'simply dove in bit beckett'    → 'asmp-dev in bitbucket'\n"
                "  'amp dev in bitbucket'          → 'asmp-dev in bitbucket'\n"
                "  'see ex data' / 'cx data'       → 'cx data visualization in bitbucket'\n"
                "  'main path in bitbucket'        → 'mainpath-accelerator in bitbucket'\n"
                "  'canada board'                  → 'kanban board'\n"
                "  'see i cd board'                → 'ci cd board'\n\n"
                "Rules:\n"
                "1. Output ONLY the corrected phrase — no explanation, no quotes.\n"
                "2. Keep 'in bitbucket' at the end when the user means a repo.\n"
                "3. Match phonetically against the repo list above — even partial or acronym sounds count.\n"
                "4. If you cannot determine the intent, return the input unchanged."
            )
        else:
            system_content = (
                "You are a speech-to-text error corrector. "
                "The user spoke a command but the microphone garbled it. "
                "Output ONLY the corrected command — nothing else.\n\n"
                "Known commands:\n"
                "  - 'visit webpage' (opens the webpage agent)\n"
                "  - 'morning briefing' / 'briefing' / 'newspaper'\n"
                "  - 'open [app]' / 'close [app]'\n"
                "  - 'what time is it' / 'what is the date'\n"
                "  - 'take a screenshot'\n"
                "  - 'volume up' / 'volume down' / 'set volume to 50'\n"
                "  - 'tell me a joke'\n"
                "  - 'hello' / 'help'\n\n"
                "Phonetic examples:\n"
                "  'the sit the beach' → 'visit webpage'\n"
                "  'page' → 'visit webpage'\n"
                "  'visit the page' → 'visit webpage'\n"
                "  'what does the pain' → 'what is the time'\n"
                "  'take his green shot' → 'take a screenshot'\n\n"
                "CRITICAL: Output ONLY the command. No quotes. No explanation. No notes. No newlines. "
                "Just the corrected text on a single line."
            )

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": raw_text},
        ]

        self._rephrase_worker = AIWorker(correction_provider, messages, max_tokens=40)
        self._rephrase_worker.response_ready.connect(
            lambda corrected: self._on_correction_done(raw_text, corrected, context)
        )
        self._rephrase_worker.error_occurred.connect(
            lambda err: self._on_correction_failed(raw_text, err)
        )
        self._rephrase_worker.start()

    def _on_correction_done(self, original: str, corrected: str, context: str | None = None):
        # Strip quotes, newlines, and any AI explanation garbage
        corrected = corrected.strip().strip('"').strip("'")
        # Remove anything after a newline (AI sometimes adds notes like "(Note: ...)")
        corrected = corrected.split("\n")[0].strip()
        # Remove parenthetical notes at the end
        if "(" in corrected and corrected.rstrip().endswith(")"):
            corrected = corrected[:corrected.rfind("(")].strip()
        # Remove common AI explanation prefixes
        for prefix in ("Corrected:", "Output:", "Command:", "Note:"):
            if corrected.lower().startswith(prefix.lower()):
                corrected = corrected[len(prefix):].strip()
        logger.info(f"STT correction result: '{original}' → '{corrected}'")
        # Log every AI correction so user can review in stt_corrections_log.jsonl
        if corrected.lower() != original.lower():
            ctx = context if context else "general"
            self._log_general_correction(original, corrected, source="ai", context=ctx)
        self.speech_corrected.emit(original, corrected)

    def _on_correction_failed(self, original: str, error: str):
        logger.warning(f"STT correction failed ({error}), using raw: '{original}'")
        self.speech_corrected.emit(original, original)

    def _log_general_correction(self, raw_vosk: str, corrected: str,
                                  source: str = "ai", context: str = "general") -> None:
        """Append any correction (AI or cache hit) to stt_corrections_log.jsonl.

        Every correction is logged here regardless of source so you can always
        see what Jarvis heard and what it mapped it to.
        To fix a wrong entry:
          1. Open config/stt_corrections_log.jsonl — find the wrong raw value.
          2. Open config/stt_corrections.json — fix or add the entry in the right section.
        """
        record = {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "context": context,
            "raw": raw_vosk,
            "corrected": corrected,
            "source": source,
        }
        try:
            self._corrections_log_path.parent.mkdir(parents=True, exist_ok=True)
            with self._corrections_log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
                fh.flush()
        except Exception as e:
            logger.error(f"Failed to write general correction log: {e}")

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
        """Synchronous version for command processing. Tries all providers in order."""
        self.conversation_history.append({"role": "user", "content": user_message})
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-16:]

        messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history

        # Try each provider in order until one succeeds
        for provider in self.providers:
            if provider.is_available():
                result = provider.chat(messages, self.settings.get("max_tokens", 500))
                if result:
                    self.conversation_history.append({"role": "assistant", "content": result})
                    logger.info(f"ask_sync answered by {type(provider).__name__}")
                    return result
                logger.warning(f"ask_sync: {type(provider).__name__} returned empty, trying next")
        return "I couldn't generate a response. Please try again."

    def _on_response(self, text: str):
        self.conversation_history.append({"role": "assistant", "content": text})
        self.response_ready.emit(text)

    def _on_error(self, error: str):
        logger.error(f"AI error: {error}")
        self.error_occurred.emit(error)

    def clear_history(self):
        self.conversation_history.clear()
