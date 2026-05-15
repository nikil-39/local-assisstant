"""
Agent Registry — Auto-discovers and manages all agents.

Each agent is a subclass of BaseAgent living in this package.
The registry loads them at startup so main_window can dispatch
voice commands like "morning briefing" to the right agent.
"""

import importlib
import logging
import pkgutil
from pathlib import Path

logger = logging.getLogger("jarvis.agents")


class AgentRegistry:
    """Discovers and holds references to all available agents."""

    def __init__(self, settings: dict, ai_manager=None):
        self.settings = settings
        self.ai_manager = ai_manager
        self._agents: dict[str, "BaseAgent"] = {}
        self._discover()

    def _discover(self):
        """Import every module in this package and register BaseAgent subclasses."""
        from assistant.agents.base_agent import BaseAgent

        pkg_dir = Path(__file__).parent
        for finder, name, _ in pkgutil.iter_modules([str(pkg_dir)]):
            if name == "base_agent":
                continue
            try:
                module = importlib.import_module(f"assistant.agents.{name}")
                for attr_name in dir(module):
                    obj = getattr(module, attr_name)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, BaseAgent)
                        and obj is not BaseAgent
                    ):
                        agent = obj(
                            settings=self.settings,
                            ai_manager=self.ai_manager,
                        )
                        for trigger in agent.triggers:
                            self._agents[trigger] = agent
                        logger.info(f"Registered agent: {agent.name} (triggers: {agent.triggers})")
            except Exception as e:
                logger.error(f"Failed to load agent module '{name}': {e}")

    def match(self, action: str) -> "BaseAgent | None":
        """Return the agent that handles *action*, or None."""
        return self._agents.get(action)

    @property
    def all_agents(self) -> list["BaseAgent"]:
        """Unique list of registered agents."""
        return list({id(a): a for a in self._agents.values()}.values())
