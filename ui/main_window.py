"""
Main Window Module - Jarvis Voice Assistant PyQt6 GUI.
Features a frameless glassmorphism window with central orb,
particle effects, waveform visualization, and control buttons.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import (
    Qt, QSize, QPoint, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve,
)
from PyQt6.QtGui import (
    QColor, QFont, QIcon, QPainter, QPainterPath, QAction,
    QShortcut, QKeySequence, QCursor,
)
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QScrollArea, QSystemTrayIcon, QMenu,
    QApplication, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
    QDialog, QFormLayout, QSpinBox, QComboBox, QSlider, QCheckBox,
)

from ui.animations import (
    OrbWidget, WaveformWidget, GlassBackground,
    AssistantState, Palette, ParticleSystem,
)
from assistant.voice_handler import VoiceHandler
from assistant.command_processor import CommandProcessor, CommandResult
from assistant.ai_integration import AIManager
from assistant.system_controller import SystemController
from assistant.agents import AgentRegistry
from assistant.agents.base_agent import AgentWorker

logger = logging.getLogger("jarvis.ui")

CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════════════
# Custom Styled Button
# ═══════════════════════════════════════════════════════════════════════════

class GlassButton(QPushButton):
    """A translucent glass-style button with hover effects."""

    def __init__(self, text: str = "", icon_char: str = "", parent=None):
        super().__init__(text, parent)
        self.icon_char = icon_char
        self.setFixedSize(52, 52)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(51, 65, 85, 150);
                border: 1px solid rgba(100, 116, 139, 60);
                border-radius: 26px;
                color: #e2e8f0;
                font-size: 18px;
                font-family: 'Segoe UI Emoji', 'Segoe UI Symbol', 'Segoe UI';
            }
            QPushButton:hover {
                background-color: rgba(99, 102, 241, 120);
                border: 1px solid rgba(99, 102, 241, 150);
            }
            QPushButton:pressed {
                background-color: rgba(99, 102, 241, 180);
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)


# ═══════════════════════════════════════════════════════════════════════════
# Chat Message Widget
# ═══════════════════════════════════════════════════════════════════════════

class ChatBubble(QFrame):
    """A single chat message bubble."""

    def __init__(self, text: str, is_user: bool = True, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        if is_user:
            label.setStyleSheet("""
                QLabel {
                    background-color: rgba(99, 102, 241, 100);
                    border-radius: 12px;
                    padding: 10px 14px;
                    color: #e2e8f0;
                    font-size: 13px;
                    font-family: 'Segoe UI', sans-serif;
                }
            """)
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            label.setStyleSheet("""
                QLabel {
                    background-color: rgba(30, 41, 59, 180);
                    border: 1px solid rgba(100, 116, 139, 40);
                    border-radius: 12px;
                    padding: 10px 14px;
                    color: #cbd5e1;
                    font-size: 13px;
                    font-family: 'Segoe UI', sans-serif;
                }
            """)
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        label.setMaximumWidth(400)
        layout.addWidget(label)


# ═══════════════════════════════════════════════════════════════════════════
# Settings Dialog
# ═══════════════════════════════════════════════════════════════════════════

class SettingsDialog(QDialog):
    """Settings configuration dialog."""

    settings_changed = pyqtSignal(dict)

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.settings = settings.copy()
        self.setWindowTitle("Jarvis Settings")
        self.setFixedSize(400, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e293b;
                color: #e2e8f0;
                font-family: 'Segoe UI';
            }
            QLabel { color: #94a3b8; font-size: 12px; }
            QSpinBox, QComboBox {
                background-color: #334155;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 4px 8px;
                color: #e2e8f0;
                min-height: 28px;
            }
            QSlider::groove:horizontal {
                background: #334155; height: 6px; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #6366f1; width: 16px; height: 16px;
                margin: -5px 0; border-radius: 8px;
            }
            QCheckBox { color: #e2e8f0; spacing: 8px; }
            QCheckBox::indicator {
                width: 18px; height: 18px; border-radius: 4px;
                background-color: #334155; border: 1px solid #475569;
            }
            QCheckBox::indicator:checked {
                background-color: #6366f1; border: 1px solid #6366f1;
            }
            QPushButton {
                background-color: #6366f1; color: white; border: none;
                border-radius: 8px; padding: 8px 20px; font-weight: bold;
            }
            QPushButton:hover { background-color: #818cf8; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("⚙️  Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e2e8f0;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        # Voice speed
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(100, 300)
        self.rate_spin.setValue(settings.get("voice", {}).get("tts_rate", 175))
        form.addRow("Voice Speed:", self.rate_spin)

        # Volume
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(settings.get("voice", {}).get("tts_volume", 0.9) * 100))
        form.addRow("TTS Volume:", self.volume_slider)

        # AI Provider
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["openai", "anthropic", "gemini", "local"])
        current = settings.get("ai", {}).get("provider", "openai")
        self.provider_combo.setCurrentText(current)
        form.addRow("AI Provider:", self.provider_combo)

        # STT Engine
        self.stt_combo = QComboBox()
        self.stt_combo.addItems(["vosk", "sphinx", "google", "windows_sapi", "powershell_sapi"])
        stt_current = settings.get("voice", {}).get("stt_engine", "sphinx")
        self.stt_combo.setCurrentText(stt_current)
        form.addRow("Speech Engine:", self.stt_combo)

        # Always on top
        self.on_top_check = QCheckBox("Keep window on top")
        self.on_top_check.setChecked(settings.get("ui", {}).get("always_on_top", True))
        form.addRow("", self.on_top_check)

        # Continuous listening
        self.continuous_check = QCheckBox("Continuous listening")
        self.continuous_check.setChecked(settings.get("assistant", {}).get("continuous_listening", False))
        form.addRow("", self.continuous_check)

        layout.addLayout(form)
        layout.addStretch()

        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

    def _save(self):
        self.settings.setdefault("voice", {})["tts_rate"] = self.rate_spin.value()
        self.settings.setdefault("voice", {})["tts_volume"] = self.volume_slider.value() / 100.0
        self.settings.setdefault("voice", {})["stt_engine"] = self.stt_combo.currentText()
        self.settings.setdefault("ai", {})["provider"] = self.provider_combo.currentText()
        self.settings.setdefault("ui", {})["always_on_top"] = self.on_top_check.isChecked()
        self.settings.setdefault("assistant", {})["continuous_listening"] = self.continuous_check.isChecked()

        # Write to disk
        try:
            settings_path = CONFIG_DIR / "settings.json"
            settings_path.write_text(json.dumps(self.settings, indent=4), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

        self.settings_changed.emit(self.settings)
        self.accept()


# ═══════════════════════════════════════════════════════════════════════════
# Main Window
# ═══════════════════════════════════════════════════════════════════════════

class JarvisMainWindow(QMainWindow):
    """Frameless glassmorphism main window for the Jarvis assistant."""

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self._drag_pos = None
        self._state = AssistantState.IDLE
        self._chat_visible = False
        self._pending_context: str | None = None  # e.g. "webpage" after "open webpage"
        # Stores (raw_vosk, ai_corrected, source) until agent confirms success/failure
        self._pending_webpage_correction: tuple[str, str, str] | None = None

        # Load configuration
        self.ui_settings = settings.get("ui", {})
        self.voice_settings = settings.get("voice", {})
        self.ai_settings = settings.get("ai", {})
        self.assistant_settings = settings.get("assistant", {})

        commands_config = load_json(CONFIG_DIR / "commands.json")

        # Initialize backend modules
        self.voice_handler = VoiceHandler(self.voice_settings)
        self.command_processor = CommandProcessor(commands_config)
        self.ai_manager = AIManager(self.ai_settings)
        self.system_controller = SystemController(commands_config)
        self.agent_registry = AgentRegistry(settings, ai_manager=self.ai_manager)
        self._agent_worker = None  # keep reference alive

        # Wire up signals
        self._connect_signals()

        # Build UI
        self._setup_window()
        self._build_ui()
        self._setup_hotkeys()
        self._setup_tray()

        # Status message timer
        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(lambda: self._set_status("Ready"))

        # Initial status
        QTimer.singleShot(500, lambda: self._set_status("Ready • Press mic or Ctrl+Space"))

    # ── Window Setup ──────────────────────────────────────────────────

    def _setup_window(self):
        w = self.ui_settings.get("window_width", 600)
        h = self.ui_settings.get("window_height", 650)

        self.setWindowTitle("Jarvis")
        self.setFixedSize(w, h)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        if not self.ui_settings.get("always_on_top", True):
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
            )

    def _build_ui(self):
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Glass background (painted widget)
        self.glass_bg = GlassBackground(central)
        self.glass_bg.setGeometry(0, 0, self.width(), self.height())
        self.glass_bg.lower()

        # Content overlay
        content = QWidget(central)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 12, 20, 16)
        content_layout.setSpacing(0)

        # Top bar: title + controls
        top_bar = self._build_top_bar()
        content_layout.addLayout(top_bar)

        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
                padding: 4px;
            }
        """)
        content_layout.addWidget(self.status_label)

        # Orb
        self.orb = OrbWidget(
            parent=content,
            orb_size=self.ui_settings.get("orb_size", 280),
        )
        self.orb.setMinimumHeight(320)
        content_layout.addWidget(self.orb, stretch=3)

        # State text below orb
        self.state_label = QLabel("IDLE")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setStyleSheet("""
            QLabel {
                color: #6366f1;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 3px;
                font-family: 'Segoe UI', sans-serif;
                padding: 2px;
            }
        """)
        content_layout.addWidget(self.state_label)

        # Last response text
        self.response_label = QLabel("")
        self.response_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.response_label.setWordWrap(True)
        self.response_label.setMaximumHeight(60)
        self.response_label.setStyleSheet("""
            QLabel {
                color: #cbd5e1;
                font-size: 12px;
                font-family: 'Segoe UI', sans-serif;
                padding: 4px 16px;
            }
        """)
        content_layout.addWidget(self.response_label)

        # Waveform
        self.waveform = WaveformWidget(parent=content, bar_count=40)
        content_layout.addWidget(self.waveform)

        # Control buttons
        controls = self._build_controls()
        content_layout.addLayout(controls)

        # Chat area (hidden by default)
        self.chat_area = self._build_chat_area()
        self.chat_area.setVisible(False)
        content_layout.addWidget(self.chat_area)

        main_layout.addWidget(content)

    def _build_top_bar(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 0)

        # Title
        title = QLabel("JARVIS")
        title.setStyleSheet("""
            QLabel {
                color: #6366f1;
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 4px;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        layout.addWidget(title)

        layout.addStretch()

        # Minimize
        minimize_btn = QPushButton("─")
        minimize_btn.setFixedSize(28, 28)
        minimize_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                color: #64748b; font-size: 14px; border-radius: 14px;
            }
            QPushButton:hover { background: rgba(100,116,139,60); color: #e2e8f0; }
        """)
        minimize_btn.clicked.connect(self.showMinimized)
        layout.addWidget(minimize_btn)

        # Close
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                color: #64748b; font-size: 12px; border-radius: 14px;
            }
            QPushButton:hover { background: rgba(239,68,68,120); color: #fff; }
        """)
        close_btn.clicked.connect(self._on_close)
        layout.addWidget(close_btn)

        return layout

    def _build_controls(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(0, 8, 0, 4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Settings button
        self.settings_btn = GlassButton(icon_char="⚙")
        self.settings_btn.setText("⚙")
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(self.settings_btn)

        # Chat toggle
        self.chat_btn = GlassButton(icon_char="💬")
        self.chat_btn.setText("💬")
        self.chat_btn.setToolTip("Toggle chat")
        self.chat_btn.clicked.connect(self._toggle_chat)
        layout.addWidget(self.chat_btn)

        # Microphone button (main action)
        self.mic_btn = GlassButton()
        self.mic_btn.setFixedSize(68, 68)
        self.mic_btn.setText("🎤")
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(99, 102, 241, 160);
                border: 2px solid rgba(99, 102, 241, 200);
                border-radius: 34px;
                color: white;
                font-size: 24px;
            }
            QPushButton:hover {
                background-color: rgba(99, 102, 241, 220);
                border: 2px solid rgba(129, 140, 248, 250);
            }
            QPushButton:pressed {
                background-color: rgba(79, 82, 220, 240);
            }
        """)
        mic_shadow = QGraphicsDropShadowEffect(self.mic_btn)
        mic_shadow.setBlurRadius(20)
        mic_shadow.setColor(QColor(99, 102, 241, 100))
        mic_shadow.setOffset(0, 4)
        self.mic_btn.setGraphicsEffect(mic_shadow)
        self.mic_btn.setToolTip("Start listening (Ctrl+Space)")
        self.mic_btn.clicked.connect(self._toggle_listening)
        layout.addWidget(self.mic_btn)

        # History button
        self.history_btn = GlassButton(icon_char="📋")
        self.history_btn.setText("📋")
        self.history_btn.setToolTip("Command history")
        self.history_btn.clicked.connect(self._show_history)
        layout.addWidget(self.history_btn)

        # Clear button
        self.clear_btn = GlassButton(icon_char="🗑")
        self.clear_btn.setText("🗑")
        self.clear_btn.setToolTip("Clear history")
        self.clear_btn.clicked.connect(self._clear_history)
        layout.addWidget(self.clear_btn)

        return layout

    def _build_chat_area(self) -> QWidget:
        container = QWidget()
        container.setFixedHeight(200)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(4)

        # Scroll area for messages
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(30,41,59,100);
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(100,116,139,100);
                border-radius: 3px;
                min-height: 20px;
            }
        """)
        self.chat_scroll = scroll

        self.chat_content = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(4)
        self.chat_layout.setContentsMargins(4, 4, 4, 4)
        scroll.setWidget(self.chat_content)
        layout.addWidget(scroll)

        # Input bar
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.chat_input = QTextEdit()
        self.chat_input.setFixedHeight(36)
        self.chat_input.setPlaceholderText("Type a command...")
        self.chat_input.setStyleSheet("""
            QTextEdit {
                background-color: rgba(30, 41, 59, 200);
                border: 1px solid rgba(100, 116, 139, 60);
                border-radius: 18px;
                padding: 6px 14px;
                color: #e2e8f0;
                font-size: 12px;
                font-family: 'Segoe UI', sans-serif;
            }
            QTextEdit:focus {
                border: 1px solid rgba(99, 102, 241, 150);
            }
        """)
        input_layout.addWidget(self.chat_input)

        send_btn = QPushButton("→")
        send_btn.setFixedSize(36, 36)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(99, 102, 241, 160);
                border: none; border-radius: 18px;
                color: white; font-size: 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(99, 102, 241, 220); }
        """)
        send_btn.clicked.connect(self._send_chat)
        input_layout.addWidget(send_btn)
        layout.addLayout(input_layout)

        return container

    # ── Signal Connections ─────────────────────────────────────────────

    def _connect_signals(self):
        # Voice handler signals
        self.voice_handler.listening_started.connect(self._on_listening_started)
        self.voice_handler.listening_stopped.connect(self._on_listening_stopped)
        self.voice_handler.text_recognized.connect(self._on_text_recognized)
        self.voice_handler.speech_started.connect(self._on_speech_started)
        self.voice_handler.speech_finished.connect(self._on_speech_finished)
        self.voice_handler.audio_level.connect(self._on_audio_level)
        self.voice_handler.error_occurred.connect(self._on_error)

        # AI manager signals
        self.ai_manager.response_ready.connect(self._on_ai_response)
        self.ai_manager.error_occurred.connect(self._on_error)
        self.ai_manager.speech_corrected.connect(self._on_speech_corrected)

    # ── Hotkeys ───────────────────────────────────────────────────────

    def _setup_hotkeys(self):
        # Ctrl+Space to toggle listening
        shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
        shortcut.activated.connect(self._toggle_listening)

        # Ctrl+Q to quit
        quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quit_shortcut.activated.connect(self._on_close)

        # Escape to cancel listening
        esc_shortcut = QShortcut(QKeySequence("Escape"), self)
        esc_shortcut.activated.connect(self._cancel_listening)

        # Enter to send chat (when chat visible)
        enter_shortcut = QShortcut(QKeySequence("Return"), self)
        enter_shortcut.activated.connect(self._send_chat)

    # ── System Tray ───────────────────────────────────────────────────

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setToolTip("Jarvis Voice Assistant")

        # Create tray menu
        menu = QMenu()
        show_action = QAction("Show Jarvis", self)
        show_action.triggered.connect(self.show)
        menu.addAction(show_action)

        listen_action = QAction("Start Listening", self)
        listen_action.triggered.connect(self._toggle_listening)
        menu.addAction(listen_action)

        menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._on_close)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    # ── Event Handlers ────────────────────────────────────────────────

    def _toggle_listening(self):
        if self.voice_handler.is_listening:
            self.voice_handler.stop_listening()
            self._set_state(AssistantState.IDLE)
        elif self.voice_handler.is_speaking:
            return  # Don't interrupt speech
        else:
            self._set_state(AssistantState.LISTENING)
            self.voice_handler.start_listening()

    def _cancel_listening(self):
        if self.voice_handler.is_listening:
            self.voice_handler.stop_listening()
            self._set_state(AssistantState.IDLE)
            self._set_status("Cancelled")

    def _on_listening_started(self):
        self._set_state(AssistantState.LISTENING)
        self._set_status("Listening... Speak now")

    def _on_listening_stopped(self):
        if self._state == AssistantState.LISTENING:
            self._set_state(AssistantState.PROCESSING)
            self._set_status("Processing...")

    def _on_text_recognized(self, text: str):
        self._set_state(AssistantState.PROCESSING)
        self._raw_speech_text = text  # store for comparison
        # Show raw transcription immediately so the user sees what was heard
        self._set_status(f'Heard: "{text}" — correcting...')
        # Pass the active context so the AI uses the right correction prompt.
        # e.g. when _pending_context == 'webpage', the AI knows we want a page name.
        self.ai_manager.rephrase_speech(text, context=self._pending_context)

    def _on_speech_corrected(self, original: str, corrected: str):
        """Called after AI corrects STT output. Process the corrected command."""
        corrected = corrected.strip()
        if corrected and corrected.lower() != original.lower():
            display = f"{corrected}  \u2022  *(fixed from: \"{original}\")*"
            logger.info(f"STT correction: '{original}' → '{corrected}'")
        else:
            display = corrected or original
        self._add_chat_message(display, is_user=True)
        self._set_status(f'Processing: "{corrected or original}"')

        text = corrected or original

        # ── Pending context: route to waiting agent ───────────────────
        if self._pending_context == "webpage":
            self._pending_context = None
            # Determine where the corrected text came from
            if corrected and corrected.lower() != original.lower():
                source = "ai"
            else:
                source = "passthrough"
            # Store for deferred learning — we save to cache ONLY after the agent
            # confirms it actually opened something (see _on_agent_finished)
            self._pending_webpage_correction = (original, corrected or original, source)
            from assistant.command_processor import CommandResult
            result = CommandResult("open_webpage", "Opening...", data={"query": text})
            self._handle_command_result(result)
            return

        # Normal routing
        result = self.command_processor.process(text)
        self._handle_command_result(result)

    def _on_speech_started(self):
        self._set_state(AssistantState.SPEAKING)

    def _on_speech_finished(self):
        self._set_state(AssistantState.IDLE)
        self._set_status("Ready")

    def _on_audio_level(self, level: float):
        self.orb.set_audio_level(level)
        self.waveform.set_level(level)

    def _on_error(self, error: str):
        self._set_state(AssistantState.ERROR)
        self._set_status(f"Error: {error}")
        self.response_label.setText(error)
        # Return to idle after 3 seconds
        QTimer.singleShot(3000, lambda: self._set_state(AssistantState.IDLE))
        QTimer.singleShot(3000, lambda: self._set_status("Ready"))

    def _on_ai_response(self, text: str):
        self._add_chat_message(text, is_user=False)
        self.response_label.setText(text[:150] + ("..." if len(text) > 150 else ""))
        self.voice_handler.speak(text)

    def _on_agent_finished(self, agent_name: str, summary: str):
        """Called when a background agent finishes successfully."""
        self._add_chat_message(summary, is_user=False)
        self.response_label.setText(summary[:150] + ("..." if len(summary) > 150 else ""))
        self._set_state(AssistantState.SPEAKING)
        self._set_status(f"{agent_name} complete")
        self.voice_handler.speak(summary)

        # ── Webpage correction learning ──────────────────────────
        if agent_name == "Web Page" and self._pending_webpage_correction:
            raw, corrected, source = self._pending_webpage_correction
            self._pending_webpage_correction = None
            # Success = agent actually opened something (not an error/not-found message)
            success = summary.lower().startswith("opening")
            # Log every attempt so user can review config/webpage_corrections_log.jsonl
            self.ai_manager.log_webpage_attempt(raw, corrected, summary, success, source)
            # Only cache verified successes — prevents wrong guesses from poisoning the cache
            if success and source == "ai" and corrected.lower() != raw.lower():
                self.ai_manager.save_webpage_correction(raw, corrected)

    def _on_webpage_prompt_ready(self, agent_name: str, prompt: str):
        """First step of 'open webpage': speak the prompt then listen for the page name."""
        self._add_chat_message(prompt, is_user=False)
        self.response_label.setText(prompt[:150] + ("..." if len(prompt) > 150 else ""))
        self._pending_context = "webpage"
        self._set_status("Waiting for page name — speak now...")
        # Speak the prompt; when TTS finishes, _on_speech_finished will idle.
        # We auto-start listening after speaking.
        self.voice_handler.speak(prompt)
        # Start listening after a short delay to let TTS finish
        QTimer.singleShot(3500, self._toggle_listening)

    def _on_agent_error(self, agent_name: str, error: str):
        """Called when a background agent fails."""
        msg = f"{agent_name} failed: {error}"
        self._add_chat_message(msg, is_user=False)
        self._set_state(AssistantState.ERROR)
        self._set_status(msg)
        QTimer.singleShot(3000, lambda: self._set_state(AssistantState.IDLE))

    def _handle_command_result(self, result: CommandResult):
        """Route a command result to the appropriate handler."""
        if result.data.get("needs_ai"):
            # Send to AI for response
            self.ai_manager.ask(result.data.get("original_text", result.response))
            return

        if result.action == "exit":
            self._add_chat_message(result.response, is_user=False)
            self.voice_handler.speak(result.response)
            QTimer.singleShot(2000, self._on_close)
            return

        if result.action == "clear_history":
            self.ai_manager.clear_history()
            self._clear_chat()
            self._set_state(AssistantState.IDLE)
            self._set_status("History cleared")
            return

        # Check if an agent handles this action
        agent = self.agent_registry.match(result.action)
        if agent:
            # ── Two-step "open webpage" flow ──────────────────────────────────
            # First trigger: no query yet → agent returns the help prompt and we
            # set _pending_context so the next voice input is routed back here.
            if result.action == "open_webpage" and not result.data.get("query"):
                self._set_status("Waiting for page name...")
                self._agent_worker = AgentWorker(agent, {})
                self._agent_worker.finished.connect(self._on_webpage_prompt_ready)
                self._agent_worker.error.connect(self._on_agent_error)
                self._agent_worker.start()
                return

            self._add_chat_message(result.response, is_user=False)
            self.voice_handler.speak(result.response)
            self._set_status(f"Running {agent.name}...")
            self._agent_worker = AgentWorker(agent, result.data)
            self._agent_worker.finished.connect(self._on_agent_finished)
            self._agent_worker.error.connect(self._on_agent_error)
            self._agent_worker.start()
            return

        # Try system execution
        sys_response = self.system_controller.execute(result.action, result.data)

        if sys_response:
            full_response = sys_response
        else:
            full_response = result.response

        self._add_chat_message(full_response, is_user=False)
        self.response_label.setText(full_response[:150] + ("..." if len(full_response) > 150 else ""))
        self._set_state(AssistantState.SPEAKING)
        self.voice_handler.speak(full_response)

    # ── Chat ──────────────────────────────────────────────────────────

    def _toggle_chat(self):
        self._chat_visible = not self._chat_visible
        self.chat_area.setVisible(self._chat_visible)

        if self._chat_visible:
            new_h = self.ui_settings.get("window_height", 650) + 200
        else:
            new_h = self.ui_settings.get("window_height", 650)

        self.setFixedHeight(new_h)
        self.glass_bg.setGeometry(0, 0, self.width(), new_h)

    def _add_chat_message(self, text: str, is_user: bool = True):
        bubble = ChatBubble(text, is_user=is_user)
        self.chat_layout.addWidget(bubble)
        # Scroll to bottom
        QTimer.singleShot(50, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))

    def _clear_chat(self):
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _send_chat(self):
        if not self._chat_visible:
            return
        text = self.chat_input.toPlainText().strip()
        if not text:
            return
        self.chat_input.clear()
        self._add_chat_message(text, is_user=True)
        self._set_state(AssistantState.PROCESSING)
        self._set_status(f"Processing: \"{text}\"")

        result = self.command_processor.process(text)
        self._handle_command_result(result)

    def _show_history(self):
        history = self.command_processor.get_history(20)
        if not history:
            self._set_status("No command history yet")
            return

        self._chat_visible = True
        self.chat_area.setVisible(True)
        new_h = self.ui_settings.get("window_height", 650) + 200
        self.setFixedHeight(new_h)
        self.glass_bg.setGeometry(0, 0, self.width(), new_h)

        for result in history[-10:]:
            self._add_chat_message(f"[{result.action}] {result.response}", is_user=False)

    def _clear_history(self):
        self.command_processor.history.clear()
        self.ai_manager.clear_history()
        self._clear_chat()
        self._set_status("All history cleared")

    # ── Settings ──────────────────────────────────────────────────────

    def _open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        dialog.settings_changed.connect(self._apply_settings)
        dialog.exec()

    def _apply_settings(self, new_settings: dict):
        self.settings = new_settings
        self.voice_settings = new_settings.get("voice", self.voice_settings)
        self.ai_settings = new_settings.get("ai", self.ai_settings)
        self.ui_settings = new_settings.get("ui", self.ui_settings)
        self._set_status("Settings updated")

    # ── State Management ──────────────────────────────────────────────

    def _set_state(self, state: AssistantState):
        self._state = state
        self.orb.set_state(state)

        state_labels = {
            AssistantState.IDLE: "IDLE",
            AssistantState.LISTENING: "LISTENING",
            AssistantState.PROCESSING: "PROCESSING",
            AssistantState.SPEAKING: "SPEAKING",
            AssistantState.ERROR: "ERROR",
        }
        state_colors = {
            AssistantState.IDLE: "#6366f1",
            AssistantState.LISTENING: "#06b6d4",
            AssistantState.PROCESSING: "#f59e0b",
            AssistantState.SPEAKING: "#22c55e",
            AssistantState.ERROR: "#ef4444",
        }
        label = state_labels.get(state, "IDLE")
        color = state_colors.get(state, "#6366f1")
        self.state_label.setText(label)
        self.state_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 3px;
                font-family: 'Segoe UI', sans-serif;
                padding: 2px;
            }}
        """)

        if state != AssistantState.LISTENING:
            self.waveform.set_idle()

    def _set_status(self, text: str):
        self.status_label.setText(text)

    # ── Window Dragging (frameless) ──────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ── Close / Tray ──────────────────────────────────────────────────

    def _on_close(self):
        self.voice_handler.cleanup()
        self.tray.hide()
        QApplication.quit()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    def closeEvent(self, event):
        # Minimize to tray instead of closing
        event.ignore()
        self.hide()
        self.tray.showMessage(
            "Jarvis",
            "Running in background. Click tray icon to restore.",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )
