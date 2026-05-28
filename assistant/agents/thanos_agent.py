"""
Thanos Agent — Snaps all running applications and browser tabs closed.

Triggered by: "thanos"
    Kills all user-facing applications and browser windows except:
    - The Jarvis assistant itself (python.exe running main.py)
    - Core Windows processes (explorer shell, system services)

Think of it as a "clean slate" for your desktop.
"""

import logging
import os
import subprocess

from assistant.agents.base_agent import BaseAgent

logger = logging.getLogger("jarvis.agents.thanos")

# Processes that must NEVER be killed (system-critical + Jarvis itself)
PROTECTED_PROCESSES = {
    "explorer",        # Windows shell
    "svchost",         # Windows services
    "csrss",           # Client/Server Runtime
    "wininit",         # Windows Init
    "winlogon",        # Logon process
    "lsass",           # Security
    "services",        # Service Control Manager
    "smss",            # Session Manager
    "dwm",            # Desktop Window Manager
    "taskhostw",       # Task Host
    "sihost",          # Shell Infrastructure Host
    "fontdrvhost",     # Font Driver Host
    "ctfmon",          # Input services
    "conhost",         # Console Host
    "runtimebroker",   # Runtime Broker
    "searchhost",      # Windows Search
    "startmenuexperiencehost",
    "shellexperiencehost",
    "textinputhost",
    "widgetservice",
    "widgets",
    "securityhealthservice",
    "securityhealthsystray",
    "smartscreen",
    "systemsettings",
    # Jarvis itself
    "python",
    "pythonw",
    "python3",
    # System tray utilities you may want to keep
    "vpnui",           # Cisco VPN
}


class ThanosAgent(BaseAgent):
    """Closes all user applications — the snap for your desktop."""

    name = "Thanos"
    triggers = ["thanos"]

    def __init__(self, settings: dict, ai_manager=None):
        self.settings = settings
        self.ai_manager = ai_manager
        self._status_emit: callable | None = None

    def _speak_status(self, text: str) -> None:
        logger.info(f"Thanos: {text}")
        if self._status_emit is not None:
            try:
                self._status_emit(text)
            except Exception:
                pass

    def run(self, data: dict | None = None) -> str:
        """Kill all user-facing apps except protected ones."""
        self._speak_status("I am inevitable. Closing all applications.")

        killed = []

        # ── Step 1: Close File Explorer WINDOWS via Shell COM ─────────────────
        # We cannot kill explorer.exe (it's the shell), but we can close its
        # individual folder windows gracefully using the Shell COM object.
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "(New-Object -ComObject Shell.Application).Windows() | "
                 "ForEach-Object { $_.Quit() }"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                killed.append("File Explorer windows")
                logger.info("Closed File Explorer windows via Shell COM")
        except Exception as e:
            logger.warning(f"Could not close File Explorer windows: {e}")

        # ── Step 2: Kill all visible windowed processes except protected ───────
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | "
                 "Select-Object -Property Name, Id | ConvertTo-Json -Compress"],
                capture_output=True, text=True, timeout=15,
            )

            import json
            processes = []
            if result.stdout.strip():
                data_raw = json.loads(result.stdout)
                processes = [data_raw] if isinstance(data_raw, dict) else data_raw

            current_pid = os.getpid()

            for proc in processes:
                name = proc.get("Name", "").lower()
                pid = proc.get("Id", 0)

                if name in PROTECTED_PROCESSES:
                    continue
                if pid == current_pid:
                    continue

                try:
                    subprocess.run(
                        ["taskkill", "/PID", str(pid), "/F"],
                        capture_output=True, timeout=5,
                    )
                    killed.append(name)
                    logger.info(f"Thanos killed: {name} (PID {pid})")
                except Exception as e:
                    logger.debug(f"Failed to kill {name} (PID {pid}): {e}")

        except Exception as e:
            logger.error(f"Thanos process scan error: {e}")

        # ── Step 3: Kill common apps that may lack window titles (browsers, etc.) ──
        # These are safe to kill — they restore session on next open
        EXTRA_TARGETS = [
            "chrome", "msedge", "firefox", "opera", "brave",
            # Teams — new version is ms-teams.exe, old is Teams.exe
            "teams", "ms-teams", "msteams", "MSTeams",
            "slack", "discord", "zoom", "skype",
            "spotify", "vlc", "mpc-hc64", "mpc-hc",
            "notepad", "notepad++", "wordpad",
            "winword", "excel", "powerpnt", "msaccess",
            "acroRd32", "SumatraPDF",
            "code",        # VS Code
            "devenv",      # Visual Studio
        ]
        for proc_name in EXTRA_TARGETS:
            try:
                r = subprocess.run(
                    ["taskkill", "/IM", f"{proc_name}.exe", "/F"],
                    capture_output=True, timeout=5,
                )
                if r.returncode == 0:
                    killed.append(proc_name)
            except Exception:
                pass

        count = len(killed)
        if count == 0:
            return "Nothing to snap. Desktop is already clean."

        unique_killed = sorted(set(killed))
        summary = ", ".join(unique_killed[:8]) + ("..." if len(unique_killed) > 8 else "")
        self._speak_status(f"Snapped {count} targets.")
        return f"Perfectly balanced. Closed: {summary}."
