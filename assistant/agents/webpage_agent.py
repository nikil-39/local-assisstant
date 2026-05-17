"""
Web Page Opening Agent — Opens configured URLs in Mozilla Firefox.

Triggered by: "open_webpage" (two-step: first trigger sets context, second
              step passes the query in data["query"])

Supported pages:
    • "jira"            → Jira dashboard
    • "kanban board"    → Scrum / Kanban board
    • "ci cd board"     → CI/CD pipeline board
    • "<name> in bitbucket" / "<name> repo" → opens repo on Bitbucket
      Repo names are read from C:\\Git at runtime (kebab-case conversion).
"""

import difflib
import logging
import re
import subprocess
from pathlib import Path

from assistant.agents.base_agent import BaseAgent

logger = logging.getLogger("jarvis.agents.webpage")

# ── Firefox path ──────────────────────────────────────────────────────────────
FIREFOX = Path(r"C:\Program Files\Mozilla Firefox\firefox.exe")

# ── Predefined page URLs ──────────────────────────────────────────────────────
PAGES: dict[str, str] = {
    "jira": "https://rb-tracker.bosch.com/tracker07/secure/Dashboard.jspa",
    "kanban board": "https://rb-tracker.bosch.com/tracker07/secure/RapidBoard.jspa?rapidView=23708&selectedIssue=ACCEL-1708#",
    "kanban": "https://rb-tracker.bosch.com/tracker07/secure/RapidBoard.jspa?rapidView=23708&selectedIssue=ACCEL-1708#",
    "ci cd board": "https://rb-tracker.bosch.com/tracker07/secure/RapidBoard.jspa?rapidView=23841&selectedIssue=ACCEL-2714#",
    "cicd board": "https://rb-tracker.bosch.com/tracker07/secure/RapidBoard.jspa?rapidView=23841&selectedIssue=ACCEL-2714#",
    "ci/cd board": "https://rb-tracker.bosch.com/tracker07/secure/RapidBoard.jspa?rapidView=23841&selectedIssue=ACCEL-2714#",
    "ci/cd": "https://rb-tracker.bosch.com/tracker07/secure/RapidBoard.jspa?rapidView=23841&selectedIssue=ACCEL-2714#",
    "cicd": "https://rb-tracker.bosch.com/tracker07/secure/RapidBoard.jspa?rapidView=23841&selectedIssue=ACCEL-2714#",
}

# ── Bitbucket ────────────────────────────────────────────────────────────────
# Repos whose Bitbucket project differs from the default
REPO_PROJECTS: dict[str, str] = {
    "pipelines": "ASMPAPP",
    "pipeline-tools": "ASMPAPP",
    "pipeline-utils": "ASMPAPP",
    "asmp-dev": "ASMPAPP",
    "ci-cd-by-vm-steering": "ASMPAPP",
}
DEFAULT_PROJECT = "ASIOS"
BITBUCKET_BASE = "https://sourcecode07.dev.bosch.com/projects/{project}/repos/{repo}/browse"

# Folder where all local Git clones live
GIT_DIR = Path(r"C:\Git")

# Words that phonetically resemble "bitbucket" — used as last-resort detection
_BITBUCKET_LIKE = re.compile(
    r"\b(bitbucket|bitbuckit|bigot|biggot|bit\s*buck|bigat|bick\s*buck|be\s*buck|big\s*cat|bigcat)\b",
    re.IGNORECASE,
)

# Prompt shown to user when no sub-command is given yet
HELP_PROMPT = (
    "Which page would you like to open? "
    "Say Jira, Kanban board, CI CD board, "
    "or say a repo name followed by in Bitbucket."
)


class WebpageAgent(BaseAgent):
    """Opens work pages (Jira, Kanban, CI/CD, Bitbucket repos) in Firefox."""

    name = "Web Page"
    triggers = ["open_webpage"]

    # ── Entry point ───────────────────────────────────────────────────────

    def run(self, data: dict | None = None) -> str:
        query = ((data or {}).get("query") or "").strip()

        # First invocation (no query yet) — just return the help prompt.
        # The main window will speak this, then listen for the sub-command.
        if not query:
            return HELP_PROMPT

        # Normalise: lowercase, collapse whitespace, strip leading "open"
        query_clean = re.sub(r"\s+", " ", query.lower()).strip()
        query_clean = re.sub(r"^open\s+", "", query_clean).strip()

        logger.info(f"WebpageAgent received query: '{query_clean}'")

        # ── 1. Try predefined pages (longest key first to avoid partial hits) ──
        for page_key in sorted(PAGES.keys(), key=len, reverse=True):
            if page_key in query_clean:
                return self._open(PAGES[page_key], page_key.title())

        # ── 1b. Fuzzy match against page names (catches garbling like "canada board") ──
        page_keys = list(PAGES.keys())
        fuzzy_pages = difflib.get_close_matches(query_clean, page_keys, n=1, cutoff=0.55)
        if fuzzy_pages:
            logger.info(f"Fuzzy page match: '{query_clean}' → '{fuzzy_pages[0]}'")
            return self._open(PAGES[fuzzy_pages[0]], fuzzy_pages[0].title())

        # ── 2. Bitbucket: "X in bitbucket" or "X repo" patterns ─────────────
        bb_match = re.search(
            r"(.+?)\s+(?:repo(?:sitory)?\s+)?in\s+bitbucket"
            r"|bitbucket\s+(.+?)(?:\s+repo(?:sitory)?)?$"
            r"|(.+?)\s+repo(?:sitory)?$",
            query_clean,
        )
        if bb_match:
            raw = (bb_match.group(1) or bb_match.group(2) or bb_match.group(3) or "").strip()
            if raw:
                return self._open_bitbucket(raw)

        # ── 2b. Garbled "bitbucket": phonetic variants anywhere in text ───────
        if _BITBUCKET_LIKE.search(query_clean):
            # Strip the bitbucket-alike word and treat the rest as the repo name
            repo_raw = _BITBUCKET_LIKE.sub("", query_clean)
            repo_raw = re.sub(r"\b(in|the|repo(?:sitory)?)\b", "", repo_raw).strip()
            if repo_raw:
                logger.info(f"Phonetic bitbucket match in '{query_clean}', repo candidate: '{repo_raw}'")
                return self._open_bitbucket(repo_raw)

        # ── 3. Check whether the whole query looks like a repo name ──────────
        repo = self._find_repo_in_git(query_clean)
        if repo:
            return self._open_bitbucket(query_clean)

        return (
            f"I couldn't match '{query}' to a known page. "
            "Say Jira, Kanban board, CI CD board, or a repo name in Bitbucket."
        )

    # ── Bitbucket helpers ─────────────────────────────────────────────────

    @staticmethod
    def _to_kebab(text: str) -> str:
        """Convert spoken repo name to kebab-case URL slug.

        Examples:
            "cx data visualization" → "cx-data-visualization"
            "CX_Data_Visualization" → "cx-data-visualization"
        """
        text = text.lower().strip()
        text = re.sub(r"[\s_]+", "-", text)
        text = re.sub(r"[^a-z0-9\-]", "", text)
        text = re.sub(r"-{2,}", "-", text).strip("-")
        return text

    def _find_repo_in_git(self, query: str) -> str | None:
        """Return the matched repo folder name (already kebab) or None."""
        if not GIT_DIR.exists():
            return None

        repos = {d.name.lower(): d.name for d in GIT_DIR.iterdir() if d.is_dir()}
        kebab = self._to_kebab(query)

        # Exact kebab match
        if kebab in repos:
            return repos[kebab]

        # Fuzzy match against kebab versions of all repo names
        kebab_names = list(repos.keys())
        matches = difflib.get_close_matches(kebab, kebab_names, n=1, cutoff=0.6)
        if matches:
            logger.info(f"Fuzzy repo match: '{kebab}' → '{matches[0]}'")
            return repos[matches[0]]

        return None

    def _open_bitbucket(self, repo_name_raw: str) -> str:
        """Resolve repo name to a Bitbucket URL and open it."""
        matched = self._find_repo_in_git(repo_name_raw)
        repo_slug = matched.lower() if matched else self._to_kebab(repo_name_raw)
        project = REPO_PROJECTS.get(repo_slug, DEFAULT_PROJECT)
        url = BITBUCKET_BASE.format(project=project, repo=repo_slug)
        label = f"{repo_slug} on Bitbucket"
        return self._open(url, label)

    # ── Browser launcher ──────────────────────────────────────────────────

    @staticmethod
    def _open(url: str, label: str) -> str:
        try:
            if FIREFOX.exists():
                subprocess.Popen([str(FIREFOX), url])
                logger.info(f"Firefox opened '{label}': {url}")
            else:
                # Fallback: system default browser
                import webbrowser
                webbrowser.open(url)
                logger.info(f"Default browser opened '{label}': {url}")
            return f"Opening {label}."
        except Exception as exc:
            logger.error(f"Failed to open '{label}': {exc}")
            return f"Failed to open {label}: {exc}"
