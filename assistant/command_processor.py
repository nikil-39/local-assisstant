"""
Command Processor Module - Parses natural language into structured commands
and dispatches them to the appropriate handler.
"""

import re
import json
import logging
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger("jarvis.commands")


class CommandResult:
    """Represents the result of a processed command."""

    def __init__(self, action: str, response: str, success: bool = True, data: dict | None = None):
        self.action = action
        self.response = response
        self.success = success
        self.data = data or {}
        self.timestamp = datetime.now()

    def __repr__(self):
        return f"CommandResult(action={self.action!r}, success={self.success})"


class CommandProcessor(QObject):
    """Processes voice/text commands into structured actions."""

    command_processed = pyqtSignal(object)  # CommandResult

    # Command patterns (order matters - more specific first)
    PATTERNS = [
        # Exit / Quit
        (r"\b(exit|quit|bye|goodbye|shut\s*down|close assistant|stop assistant)\b", "exit"),
        # Help
        (r"^(help|commands|what can you do)\b", "help"),
        # Screenshot
        (r"\b(take|capture|grab)\s+(a\s+)?screenshot\b", "screenshot"),
        # Volume control
        (r"\b(set|change)?\s*volume\s+(to\s+)?(\d+)\b", "volume"),
        (r"\bvolume\s+(up|down|mute|unmute)\b", "volume_adjust"),
        (r"\b(mute|unmute)\b", "volume_toggle"),
        # Time / Date
        (r"\b(what\s+)?(time|date|day)\s*(is it|today)?\b", "datetime"),
        # Weather
        (r"\b(what'?s?\s+the\s+)?weather\b", "weather"),
        # File operations
        (r"\bcreate\s+(a\s+)?(file|folder|directory)\s+(named|called)\s+(.+)", "create_file"),
        (r"\b(delete|remove)\s+(the\s+)?(file|folder|directory)\s+(.+)", "delete_file"),
        (r"\b(what|which|list)\s+(files|folders)\s+(are\s+)?(in|inside)\s+(.+)", "list_files"),
        (r"\bsearch\s+(for\s+)?(files?|folders?)\s+(named|called|containing)\s+(.+)", "search_files"),
        (r"\bopen\s+(the\s+)?file\s+(.+)", "open_file"),
        # Web search
        (r"\bsearch\s+(for\s+)?(.+?)\s+on\s+(google|youtube|github|bing|stackoverflow|wikipedia|amazon|reddit)\b", "web_search_engine"),
        (r"\b(google|search(\s+for)?|look\s+up)\s+(.+)", "web_search"),
        (r"\b(search|find)\s+on\s+youtube\s+(.+)", "youtube_search"),
        # Open website
        (r"\b(open|go\s+to|navigate\s+to|visit)\s+(https?://\S+|www\.\S+|\S+\.(com|org|net|io|dev|ai))\b", "open_url"),
        (r"\bopen\s+(.+?)\s+and\s+search\s+(for\s+)?(.+)", "open_and_search"),
        # Open application
        (r"\b(open|launch|start|run)\s+(.+)", "open_app"),
        # Close / Kill application
        (r"\b(close|kill|stop|end)\s+(.+)", "close_app"),
        # System info
        (r"\b(system\s+info|system\s+information|my\s+computer|pc\s+info)\b", "system_info"),
        (r"\b(battery|power)\s*(status|level|info)?\b", "battery"),
        (r"\b(cpu|processor)\s*(usage|load|info)?\b", "cpu_info"),
        (r"\b(memory|ram)\s*(usage|info)?\b", "memory_info"),
        (r"\b(disk|storage)\s*(usage|space|info)?\b", "disk_info"),
        (r"\bip\s*address\b", "ip_address"),
        # Process management
        (r"\b(list|show)\s+(running\s+)?(processes|tasks|apps)\b", "list_processes"),
        # Reminder
        (r"\b(set|create)\s+(a\s+)?reminder\s+(.+)", "reminder"),
        # Music / Media
        (r"\bplay\s+music\b", "play_music"),
        (r"\b(pause|stop)\s+music\b", "pause_music"),
        # Joke
        (r"\b(tell\s+me\s+a\s+joke|joke|make\s+me\s+laugh|something\s+funny)\b", "joke"),
        # Lock screen
        (r"\block\s+(the\s+)?(screen|computer|pc)\b", "lock"),
        # Quick responses (greetings, etc.)
        (r"^(hello|hi|hey|good\s+morning|good\s+afternoon|good\s+evening|good\s+night)\b", "greeting"),
        (r"^(thanks|thank\s+you|thx)\b", "thanks"),
        (r"\bhow\s+are\s+you\b", "how_are_you"),
        (r"\bwhat'?s?\s+your\s+name\b", "name"),
        # Clear history
        (r"\bclear\s+(chat\s+)?history\b", "clear_history"),
    ]

    # Filler words common in voice recognition output
    FILLER_WORDS = re.compile(
        r"\b(um+|uh+|hum+|hmm+|yep|yeah|yes|please|could you|can you|would you|"
        r"hey|hello|hi|okay|ok|so|well|actually|basically|just|like|you know)\b",
        re.IGNORECASE,
    )

    # Verb normalization: past tense / gerund → base form
    VERB_NORMALIZE = {
        "opened": "open", "opens": "open", "opening": "open",
        "launched": "launch", "launches": "launch", "launching": "launch",
        "started": "start", "starts": "start", "starting": "start",
        "closed": "close", "closes": "close", "closing": "close",
        "searched": "search", "searches": "search", "searching": "search",
    }

    def __init__(self, commands_config: dict | None = None):
        super().__init__()
        self.commands_config = commands_config or {}
        self.quick_responses = self.commands_config.get("quick_responses", {})
        self.app_aliases = self.commands_config.get("app_aliases", {})
        self.history: list[CommandResult] = []
        self._compiled_patterns = [(re.compile(p, re.IGNORECASE), action) for p, action in self.PATTERNS]

    def _normalize_speech(self, text: str) -> str:
        """Clean up noisy voice recognition output."""
        # Normalize verbs
        words = text.split()
        words = [self.VERB_NORMALIZE.get(w.lower(), w) for w in words]
        text = " ".join(words)
        # Remove filler words
        text = self.FILLER_WORDS.sub("", text)
        # Collapse whitespace
        text = re.sub(r"\s{2,}", " ", text).strip()
        return text

    def _try_app_name_fallback(self, text: str) -> CommandResult | None:
        """If text contains a known app name, treat it as an open command."""
        text_lower = text.lower()
        # Check for known app aliases in the text (longer names first to avoid partial matches)
        for alias in sorted(self.app_aliases.keys(), key=len, reverse=True):
            if alias in text_lower:
                return CommandResult("open_app", f"Opening {alias}...", data={"app": alias})
        return None

    def process(self, text: str) -> CommandResult:
        """Parse text and return a CommandResult with the identified action."""
        text = text.strip()
        if not text:
            return CommandResult("empty", "I didn't catch that. Could you repeat?", success=False)

        # Normalize noisy voice input
        normalized = self._normalize_speech(text)
        logger.debug(f"Normalized: '{text}' → '{normalized}'")

        # Try pattern matching (on normalized text first, then raw)
        for attempt in (normalized, text):
            for pattern, action in self._compiled_patterns:
                match = pattern.search(attempt)
                if match:
                    result = self._build_result(action, attempt, match)
                    self.history.append(result)
                    if len(self.history) > 100:
                        self.history = self.history[-80:]
                    self.command_processed.emit(result)
                    return result

        # Fallback: detect known app names in the text
        fallback = self._try_app_name_fallback(normalized) or self._try_app_name_fallback(text)
        if fallback:
            logger.info(f"App-name fallback matched: {fallback.data}")
            self.history.append(fallback)
            self.command_processed.emit(fallback)
            return fallback

        # No pattern matched → send to AI
        result = CommandResult("ai_query", text, data={"needs_ai": True, "original_text": text})
        self.history.append(result)
        self.command_processed.emit(result)
        return result

    def _build_result(self, action: str, text: str, match: re.Match) -> CommandResult:
        """Build a CommandResult from a matched action."""

        if action == "exit":
            return CommandResult("exit", "Goodbye! Shutting down.", data={"exit": True})

        elif action == "help":
            help_text = (
                "I can help you with:\n"
                "• Open apps: 'Open Chrome', 'Launch Spotify'\n"
                "• Web search: 'Search for Python tutorials'\n"
                "• Files: 'Create a file named test.txt'\n"
                "• System: 'Take a screenshot', 'System info'\n"
                "• Volume: 'Volume up', 'Set volume to 50'\n"
                "• Fun: 'Tell me a joke'\n"
                "• AI chat: Just ask me anything!"
            )
            return CommandResult("help", help_text)

        elif action == "screenshot":
            return CommandResult("screenshot", "Taking a screenshot...", data={"action": "screenshot"})

        elif action == "volume":
            level = int(match.group(3)) if match.group(3) else 50
            return CommandResult("volume", f"Setting volume to {level}%.", data={"level": min(level, 100)})

        elif action == "volume_adjust":
            direction = match.group(1).lower()
            return CommandResult("volume_adjust", f"Volume {direction}.", data={"direction": direction})

        elif action == "volume_toggle":
            action_name = match.group(1).lower()
            return CommandResult("volume_toggle", f"{action_name.capitalize()}ing.", data={"action": action_name})

        elif action == "datetime":
            now = datetime.now()
            response = f"It's {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}."
            return CommandResult("datetime", response)

        elif action == "weather":
            return CommandResult("weather", "Checking the weather...", data={"needs_ai": True, "original_text": text})

        elif action == "create_file":
            name = match.group(4).strip().strip('"\'')
            file_type = match.group(2)  # file or folder
            return CommandResult("create_file", f"Creating {file_type} '{name}'...", data={"name": name, "type": file_type})

        elif action == "delete_file":
            name = match.group(4).strip().strip('"\'')
            return CommandResult("delete_file", f"Deleting '{name}'...", data={"name": name})

        elif action == "list_files":
            path = match.group(5).strip().strip('"\'')
            return CommandResult("list_files", f"Listing files in '{path}'...", data={"path": path})

        elif action == "search_files":
            query = match.group(4).strip().strip('"\'')
            return CommandResult("search_files", f"Searching for '{query}'...", data={"query": query})

        elif action == "open_file":
            path = match.group(2).strip().strip('"\'')
            return CommandResult("open_file", f"Opening '{path}'...", data={"path": path})

        elif action == "web_search_engine":
            query = match.group(2).strip()
            engine = match.group(3).lower()
            return CommandResult("web_search", f"Searching '{query}' on {engine}...", data={"query": query, "engine": engine})

        elif action == "web_search":
            query = match.group(3).strip() if match.group(3) else text
            return CommandResult("web_search", f"Searching for '{query}'...", data={"query": query, "engine": "google"})

        elif action == "youtube_search":
            query = match.group(2).strip()
            return CommandResult("web_search", f"Searching YouTube for '{query}'...", data={"query": query, "engine": "youtube"})

        elif action == "open_url":
            url = match.group(2).strip()
            return CommandResult("open_url", f"Opening {url}...", data={"url": url})

        elif action == "open_and_search":
            app = match.group(1).strip()
            query = match.group(3).strip()
            return CommandResult("open_and_search", f"Opening {app} and searching for '{query}'...", data={"app": app, "query": query})

        elif action == "open_app":
            app = match.group(2).strip()
            return CommandResult("open_app", f"Opening {app}...", data={"app": app})

        elif action == "close_app":
            app = match.group(2).strip()
            return CommandResult("close_app", f"Closing {app}...", data={"app": app})

        elif action in ("system_info", "battery", "cpu_info", "memory_info", "disk_info", "ip_address"):
            return CommandResult(action, "Fetching system information...", data={"info_type": action})

        elif action == "list_processes":
            return CommandResult("list_processes", "Listing running processes...")

        elif action == "reminder":
            reminder_text = match.group(3).strip()
            return CommandResult("reminder", f"Reminder set: {reminder_text}", data={"text": reminder_text})

        elif action == "play_music":
            return CommandResult("play_music", "Playing music...", data={"action": "play"})

        elif action == "pause_music":
            return CommandResult("pause_music", "Pausing music.", data={"action": "pause"})

        elif action == "joke":
            return CommandResult("joke", "", data={"needs_ai": True, "original_text": "Tell me a short, funny joke."})

        elif action == "lock":
            return CommandResult("lock", "Locking the screen...", data={"action": "lock"})

        elif action in ("greeting", "thanks", "how_are_you", "name"):
            responses = {
                "greeting": "Hello! I'm Jarvis, your desktop assistant. How can I help you?",
                "thanks": "You're welcome! Let me know if you need anything else.",
                "how_are_you": "I'm running at peak performance! How can I assist you?",
                "name": "I'm Jarvis, your AI-powered desktop assistant.",
            }
            return CommandResult(action, responses.get(action, "Hello!"))

        elif action == "clear_history":
            return CommandResult("clear_history", "Chat history cleared.", data={"action": "clear"})

        return CommandResult("unknown", text, data={"needs_ai": True, "original_text": text})

    def get_history(self, limit: int = 20) -> list[CommandResult]:
        return self.history[-limit:]
