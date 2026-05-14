#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║       ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗                        ║
║       ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝                        ║
║       ██║███████║██████╔╝██║   ██║██║███████╗                        ║
║  ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║                        ║
║  ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║                        ║
║   ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝                        ║
║                                                                       ║
║       Voice-Controlled AI Desktop Assistant                           ║
║       Python 3.10+ • PyQt6 • Speech Recognition                      ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝

Entry point for the Jarvis Voice Assistant.

Usage:
    python main.py              Launch the GUI assistant
    python main.py --minimized  Start minimized to system tray
    python main.py --debug      Enable debug logging
"""

import sys
import os
import json
import logging
import argparse
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env if present (for API keys)
ENV_FILE = PROJECT_ROOT / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    fmt = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, datefmt="%H:%M:%S")

    # Suppress noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def load_settings() -> dict:
    settings_path = PROJECT_ROOT / "config" / "settings.json"
    try:
        return json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception as e:
        logging.warning(f"Could not load settings.json: {e}. Using defaults.")
        return {
            "assistant": {"name": "Jarvis", "wake_word": "hey assistant"},
            "voice": {"tts_rate": 175, "tts_volume": 0.9, "stt_engine": "google"},
            "ai": {"provider": "openai", "openai_model": "gpt-4o-mini"},
            "ui": {"window_width": 600, "window_height": 650, "orb_size": 280, "always_on_top": True},
            "hotkeys": {"toggle_listen": "Ctrl+Space"},
        }


def main():
    parser = argparse.ArgumentParser(description="Jarvis Voice Assistant")
    parser.add_argument("--minimized", action="store_true", help="Start minimized to tray")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    setup_logging(args.debug)
    logger = logging.getLogger("jarvis")
    logger.info("Starting Jarvis Voice Assistant...")

    # Suppress SSL warnings for proxy environments
    import warnings
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")

    # Import PyQt6
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont
    except ImportError:
        print("\n❌ PyQt6 is required. Install it with:")
        print("   pip install PyQt6\n")
        sys.exit(1)

    # Load settings
    settings = load_settings()

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Jarvis")
    app.setOrganizationName("JarvisAssistant")

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Load stylesheet
    qss_path = PROJECT_ROOT / "ui" / "styles.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    # Prevent closing when last window hidden (for tray)
    app.setQuitOnLastWindowClosed(False)

    # Create main window
    from ui.main_window import JarvisMainWindow
    window = JarvisMainWindow(settings)

    if args.minimized:
        window.hide()
        logger.info("Started minimized to system tray")
    else:
        window.show()
        logger.info("Main window displayed")

    logger.info("Jarvis is ready!")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
