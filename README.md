# Jarvis — Voice Assistant

A futuristic voice assistant with a PyQt6 glassmorphism GUI, offline speech recognition (Vosk), and system control capabilities.

## Quick Start

```powershell
cd c:\Github\local-assistant
pip install -r requirements.txt
python download_vosk_model.py   # one-time: downloads offline speech model
python main.py
```

Launch flags:

| Flag | Description |
|------|-------------|
| `--debug` | Enable verbose debug logging |
| `--minimized` | Start minimized to system tray |

## Features

- **Offline voice recognition** — Vosk STT (no internet needed)
- **Glassmorphism GUI** — animated orb, particle effects, waveform visualizer
- **80+ app aliases** — fuzzy matching + Start Menu shortcut fallback
- **AI integration** — OpenAI / Claude / Gemini (optional, via `.env`)
- **Speech normalization** — handles messy voice input ("could you opened outlook" → opens Outlook)
- **System control** — volume, screenshots, file ops, process management

---

## Voice Commands

### Applications

| Say | Action |
|-----|--------|
| "Open Chrome" | Launch Google Chrome |
| "Launch Outlook" | Launch Outlook |
| "Start VS Code" | Launch Visual Studio Code |
| "Run Firefox" | Launch Mozilla Firefox |
| "Close Notepad" | Kill Notepad process |

You can say just the app name (e.g. "Outlook") and it will be opened automatically.

**Supported app names:** outlook, word, excel, powerpoint, teams, onenote, chrome, firefox, edge, notepad, calculator, terminal, powershell, cmd, task manager, vs code, visual studio, paint, snipping tool, spotify, zoom, slack, discord, telegram, whatsapp, vpn, sap, keepass, acrobat, file explorer, settings, control panel, and more.

### Web Search

| Say | Action |
|-----|--------|
| "Search for Python tutorials" | Google search |
| "Google machine learning" | Google search |
| "Search Python on YouTube" | YouTube search |
| "Search for React on GitHub" | GitHub search |
| "Look up neural networks" | Google search |

**Supported engines:** Google, YouTube, GitHub, Bing, StackOverflow, Wikipedia, Amazon, Reddit.

### Websites

| Say | Action |
|-----|--------|
| "Open google.com" | Opens in default browser |
| "Go to github.com" | Opens in default browser |
| "Visit stackoverflow.com" | Opens in default browser |

### Volume Control

| Say | Action |
|-----|--------|
| "Set volume to 50" | Set volume to 50% |
| "Volume up" | Increase volume |
| "Volume down" | Decrease volume |
| "Mute" | Mute audio |
| "Unmute" | Unmute audio |

### System Information

| Say | Action |
|-----|--------|
| "System info" | CPU, RAM, disk, OS overview |
| "Battery status" | Battery percentage & charging state |
| "CPU usage" | Current CPU load |
| "Memory info" | RAM usage |
| "Disk info" | Disk space |
| "IP address" | Network IP address |

### File Operations

| Say | Action |
|-----|--------|
| "Create a file named notes.txt" | Creates file |
| "Create a folder called projects" | Creates directory |
| "Delete file test.txt" | Deletes file |
| "List files in Desktop" | Lists directory contents |
| "Search for files named report" | Searches for files |
| "Open file readme.txt" | Opens file in default app |

### Screenshots

| Say | Action |
|-----|--------|
| "Take a screenshot" | Captures screen |
| "Capture screenshot" | Captures screen |
| "Grab a screenshot" | Captures screen |

### Date & Time

| Say | Action |
|-----|--------|
| "What time is it" | Current time |
| "What's the date" | Current date |
| "What day is it" | Day of the week |

### Process Management

| Say | Action |
|-----|--------|
| "List running processes" | Show active processes |
| "Show tasks" | Show active processes |

### Media

| Say | Action |
|-----|--------|
| "Play music" | Play media |
| "Pause music" | Pause media |

### System

| Say | Action |
|-----|--------|
| "Lock screen" | Lock the computer |
| "Lock PC" | Lock the computer |

### Misc

| Say | Action |
|-----|--------|
| "Tell me a joke" | Random joke |
| "What's your name" | Assistant introduction |
| "Help" / "What can you do" | List capabilities |
| "Clear history" | Clear chat history |
| "Exit" / "Goodbye" | Shut down assistant |

### AI Chat

Anything that doesn't match a command is sent to the AI provider for a conversational response (requires API key in `.env`).

---

## Configuration

### `config/settings.json`

| Setting | Default | Description |
|---------|---------|-------------|
| `voice.stt_engine` | `"vosk"` | Speech engine: vosk, sphinx, powershell_sapi |
| `voice.tts_rate` | `175` | Text-to-speech speed |
| `voice.tts_volume` | `0.9` | TTS volume (0.0–1.0) |
| `voice.listen_timeout` | `10` | Max seconds to wait for speech |
| `voice.pause_threshold` | `2.0` | Silence duration to end phrase |
| `voice.energy_threshold` | `150` | Microphone sensitivity |
| `ai.provider` | `"openai"` | AI provider: openai, claude, gemini |

### `config/commands.json`

- `app_aliases` — Map friendly names to executables (add your own apps here)
- `search_engines` — URL templates for web searches
- `quick_responses` — Canned replies for greetings

### `.env` (optional, for AI features)

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_AI_API_KEY=AI...
```

---

## Project Structure

```
local-assistant/
├── main.py                  # Entry point
├── assistant/
│   ├── voice_handler.py     # STT/TTS (Vosk, Sphinx, SAPI)
│   ├── command_processor.py # NLP pattern matching + normalization
│   ├── system_controller.py # App launch, files, volume, etc.
│   └── ai_integration.py   # OpenAI/Claude/Gemini integration
├── ui/
│   ├── main_window.py      # PyQt6 glassmorphism window
│   ├── animations.py       # Orb, particles, waveform widgets
│   └── styles.qss          # Qt stylesheet
├── config/
│   ├── settings.json        # Runtime settings
│   └── commands.json        # App aliases & search engines
├── assets/
│   └── vosk-model/          # Offline speech model (downloaded)
├── download_vosk_model.py   # One-time model downloader
└── requirements.txt         # Python dependencies
```

## Requirements

- Python 3.11+
- Windows 10/11
- Microphone (USB headset recommended)
- ~40 MB disk for Vosk model
