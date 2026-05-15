"""
Base Agent — Abstract base class for all Jarvis agents.

Every agent must define:
    name        — Human-readable name (e.g. "Morning Briefing")
    triggers    — List of command_processor action strings that invoke it
    run()       — Main logic; returns a spoken summary string

Agents run on a background QThread so they don't freeze the UI.
"""

import logging
from abc import ABC, abstractmethod

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger("jarvis.agents")


class BaseAgent(ABC):
    """Base class every agent inherits from."""

    name: str = "BaseAgent"
    triggers: list[str] = []

    def __init__(self, settings: dict, ai_manager=None):
        self.settings = settings
        self.ai_manager = ai_manager

    @abstractmethod
    def run(self, data: dict | None = None) -> str:
        """Execute the agent's task.

        Args:
            data: Optional dict from CommandResult.data.

        Returns:
            A short spoken summary string (Jarvis reads this aloud).
            The agent can also open files / browsers on its own.
        """
        ...


class AgentWorker(QThread):
    """Runs an agent's .run() on a background thread."""

    finished = pyqtSignal(str, str)  # (agent_name, spoken_summary)
    error = pyqtSignal(str, str)     # (agent_name, error_message)

    def __init__(self, agent: BaseAgent, data: dict | None = None):
        super().__init__()
        self.agent = agent
        self.data = data

    def run(self):
        try:
            logger.info(f"Agent '{self.agent.name}' starting...")
            summary = self.agent.run(self.data)
            logger.info(f"Agent '{self.agent.name}' finished.")
            self.finished.emit(self.agent.name, summary or "Done.")
        except Exception as e:
            logger.error(f"Agent '{self.agent.name}' failed: {e}", exc_info=True)
            self.error.emit(self.agent.name, str(e))
