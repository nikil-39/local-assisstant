"""
Search Agent — Opens Google or YouTube directly with a typed search query.

Triggered by: "search" (two-step flow)
    Step 1: Jarvis asks "Say YouTube or Google followed by your search query."
    Step 2: User says e.g. "YouTube latest Tamil songs"
        → Parses platform + query and opens the direct search results page in Chrome.
"""

import difflib
import logging
import subprocess
from pathlib import Path
from urllib.parse import quote_plus

from assistant.agents.base_agent import BaseAgent

logger = logging.getLogger("jarvis.agents.search")

# Chrome executable paths (tries both Program Files variants)
CHROME_PATHS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
]

# Synonyms — all variations that map to a target key
# Ordered longer-first so multi-word prefixes match before single words
SYNONYMS: dict[str, str] = {
    "google search": "google",
    "go to google": "google",
    "google it": "google",
    "google": "google",
    "youtube.com": "youtube",
    "you tube": "youtube",
    "you two": "youtube",
    "you too": "youtube",
    "utube": "youtube",
    "youtube": "youtube",
    "yt": "youtube",
    "tube": "youtube",
}

HELP_PROMPT = (
    "Say YouTube or Google followed by what you want to search. "
    "For example: YouTube latest Tamil songs."
)


def _find_chrome() -> Path | None:
    for path in CHROME_PATHS:
        if path.exists():
            return path
    return None


def _parse_platform_and_query(text: str) -> tuple[str | None, str]:
    """
    Split 'text' into (platform_key, search_terms).
    Tries to match the longest synonym prefix, then falls back to fuzzy.
    Returns (None, "") if no platform found.
    """
    import re as _re
    # Strip punctuation (commas, periods, etc.) so STT output like
    # "YouTube, Marvel, Thanos, Snaps." doesn't break prefix matching.
    text = _re.sub(r"[^\w\s]", " ", text)
    text = _re.sub(r"\s{2,}", " ", text).strip()
    words = text.split()

    # 1. Longest-first exact synonym prefix match
    for length in range(min(4, len(words)), 0, -1):
        prefix = " ".join(words[:length])
        if prefix in SYNONYMS:
            return SYNONYMS[prefix], " ".join(words[length:]).strip()

    # 2. Fuzzy match on first 1-3 words (catches STT garbling like "utooby")
    for length in range(min(3, len(words)), 0, -1):
        prefix = " ".join(words[:length])
        matches = difflib.get_close_matches(prefix, list(SYNONYMS.keys()), n=1, cutoff=0.6)
        if matches:
            logger.info(f"SearchAgent fuzzy matched '{prefix}' → '{matches[0]}' → {SYNONYMS[matches[0]]}")
            return SYNONYMS[matches[0]], " ".join(words[length:]).strip()

    return None, ""


class SearchAgent(BaseAgent):
    """Opens Google or YouTube search results directly in Chrome."""

    name = "Voice Search"
    triggers = ["voice_search"]

    def run(self, data: dict | None = None) -> str:
        query = ((data or {}).get("query") or "").strip().lower()

        # First invocation (no query) — ask user for platform + search terms
        if not query:
            return HELP_PROMPT

        platform_key, search_terms = _parse_platform_and_query(query)

        if not platform_key:
            return (
                f"I didn't recognise a platform in '{query}'. "
                "Say Google or YouTube followed by your search."
            )

        label = platform_key.capitalize()

        # Build direct search URL
        if search_terms:
            encoded = quote_plus(search_terms)
            if platform_key == "youtube":
                url = f"https://www.youtube.com/results?search_query={encoded}"
            else:
                url = f"https://www.google.com/search?q={encoded}"
            spoken = f"Searching {label} for {search_terms}."
            logger.info(f"SearchAgent: {label} search for '{search_terms}' → {url}")
        else:
            # No search terms — open the site home page
            url = "https://www.youtube.com" if platform_key == "youtube" else "https://www.google.com"
            spoken = f"Opening {label}."
            logger.info(f"SearchAgent: opening {label} home page (no query given)")

        try:
            chrome = _find_chrome()
            if chrome:
                subprocess.Popen([str(chrome), url])
            else:
                subprocess.Popen(["cmd", "/c", "start", "", url], shell=False)
            return spoken
        except Exception as e:
            logger.error(f"SearchAgent failed: {e}")
            return f"Failed to open {label}: {e}"
