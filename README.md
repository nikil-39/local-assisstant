# Jarvis — Voice Assistant

A futuristic voice assistant with a PyQt6 glassmorphism GUI, offline speech recognition (Vosk), AI-powered speech correction, and system control capabilities.

## Quick Start

```powershell
cd c:\Github\local-assistant
pip install -r requirements.txt
python download_vosk_model.py   # one-time: downloads offline speech model
python main.py
```

Launch flags:

| Flag            | Description                                                   |
| --------------- | ------------------------------------------------------------- |
| `--debug`     | Enable verbose debug logging (shows STT correction in action) |
| `--minimized` | Start minimized to system tray                                |

## How It Works — Speech Pipeline

```
Microphone → Vosk STT → AI Correction → Command Processor → Action
```

Vosk converts speech to text offline, but sometimes mishears words (e.g. "what does the pain" instead of "what is the time"). The **AI correction step** uses a local LLM (via Ollama) to interpret the intent and fix the transcription before it reaches the command processor.

**Example:**

```
Vosk heard:   "what does the pain"
AI corrected: "what is the time"
Action:       → DateTime command executed ✓
```

With `--debug` you can see this in the logs:

```
[jarvis.voice] INFO: Vosk recognized: "what does the pain"
[jarvis.ai]    INFO: STT correction requested via OllamaProvider: 'what does the pain'
[jarvis.ai]    INFO: STT correction result: 'what does the pain' → 'what is the time'
```

---

## Features

- **Offline voice recognition** — Vosk STT (no internet needed)
- **AI speech correction** — local LLM fixes STT errors before action dispatch
- **Glassmorphism GUI** — animated orb, particle effects, waveform visualizer
- **80+ app aliases** — fuzzy matching + Start Menu shortcut fallback (mishearings like "themes" → "teams" auto-corrected)
- **AI integration** — Ollama (local) / Gemini / OpenAI / Claude (optional)
- **Speech normalization** — handles messy voice input ("could you opened outlook" → opens Outlook)
- **System control** — volume, screenshots, file ops, process management
- **Web Page Agent** — opens Jira, Kanban, CI/CD boards, and Bitbucket repos in Firefox with a two-step voice flow

---

## Voice Commands

### Applications — Open & Close

Use **"Open"**, **"Launch"**, **"Start"**, or **"Run"** to open an app.  
Use **"Close"**, **"Kill"**, or **"Stop"** to close it.

> Vosk mishearings are auto-corrected by fuzzy matching (e.g. *"open microsoft themes"* → opens **Microsoft Teams**).

| Say                         | Say to Close                   | App                        |
| --------------------------- | ------------------------------ | -------------------------- |
| "Open Outlook"              | "Close Outlook"                | Microsoft Outlook          |
| "Open Word"                 | "Close Word"                   | Microsoft Word             |
| "Open Excel"                | "Close Excel"                  | Microsoft Excel            |
| "Open PowerPoint"           | "Close PowerPoint"             | Microsoft PowerPoint       |
| "Open Teams"                | "Close Teams"                  | Microsoft Teams            |
| "Open OneNote"              | "Close OneNote"                | Microsoft OneNote          |
| "Open Chrome"               | "Close Chrome"                 | Google Chrome              |
| "Open Firefox"              | "Close Firefox"                | Mozilla Firefox            |
| "Open Edge"                 | "Close Edge"                   | Microsoft Edge             |
| "Open Notepad"              | "Close Notepad"                | Notepad                    |
| "Open Calculator"           | "Close Calculator"             | Calculator                 |
| "Open Terminal"             | "Close Terminal"               | Windows Terminal           |
| "Open PowerShell"           | "Close PowerShell"             | PowerShell                 |
| "Open Command Prompt"       | "Close Command Prompt"         | CMD                        |
| "Open VS Code"              | "Close VS Code"                | Visual Studio Code         |
| "Open Visual Studio"        | "Close Visual Studio"          | Visual Studio              |
| "Open File Explorer"        | "Close File Explorer"          | Windows Explorer           |
| "Open Task Manager"         | "Close Task Manager"           | Task Manager               |
| "Open Settings"             | —                              | Windows Settings           |
| "Open Control Panel"        | —                              | Control Panel              |
| "Open Paint"                | "Close Paint"                  | Microsoft Paint            |
| "Open Snipping Tool"        | "Close Snipping Tool"          | Snipping Tool              |
| "Open Sticky Notes"         | —                              | Sticky Notes               |
| "Open Spotify"              | "Close Spotify"                | Spotify                    |
| "Open Zoom"                 | "Close Zoom"                   | Zoom                       |
| "Open Slack"                | "Close Slack"                  | Slack                      |
| "Open Discord"              | "Close Discord"                | Discord                    |
| "Open Telegram"             | "Close Telegram"               | Telegram                   |
| "Open WhatsApp"             | —                              | WhatsApp                   |
| "Open VPN"                  | "Close VPN"                    | Cisco Secure Client        |
| "Open Citrix"               | "Close Citrix"                 | Citrix Workspace           |
| "Open SAP"                  | "Close SAP"                    | SAP GUI / SAP Logon        |
| "Open KeePass"              | "Close KeePass"                | KeePass                    |
| "Open Screenpresso"         | "Close Screenpresso"           | Screenpresso               |
| "Open Acrobat"              | "Close Acrobat"                | Adobe Acrobat Reader       |
| "Open Git Bash"             | —                              | Git Bash                   |
| "Open SourceTree"           | —                              | SourceTree                 |
| "Open Beyond Compare"       | —                              | Beyond Compare             |
| "Open Media Player"         | "Close Media Player"           | Windows Media Player       |
| "Open Camera"               | —                              | Windows Camera             |
| "Open Store"                | —                              | Microsoft Store            |

### Web Search

| Say                           | Action         |
| ----------------------------- | -------------- |
| "Search for Python tutorials" | Google search  |
| "Google machine learning"     | Google search  |
| "Search Python on YouTube"    | YouTube search |
| "Search for React on GitHub"  | GitHub search  |
| "Look up neural networks"     | Google search  |

**Supported engines:** Google, YouTube, GitHub, Bing, StackOverflow, Wikipedia, Amazon, Reddit.

### Websites

| Say                       | Action                   |
| ------------------------- | ------------------------ |
| "Open google.com"         | Opens in default browser |
| "Go to github.com"        | Opens in default browser |
| "Visit stackoverflow.com" | Opens in default browser |

### Volume Control

| Say                | Action            |
| ------------------ | ----------------- |
| "Set volume to 50" | Set volume to 50% |
| "Volume up"        | Increase volume   |
| "Volume down"      | Decrease volume   |
| "Mute"             | Mute audio        |
| "Unmute"           | Unmute audio      |

### System Information

| Say              | Action                              |
| ---------------- | ----------------------------------- |
| "System info"    | CPU, RAM, disk, OS overview         |
| "Battery status" | Battery percentage & charging state |
| "CPU usage"      | Current CPU load                    |
| "Memory info"    | RAM usage                           |
| "Disk info"      | Disk space                          |
| "IP address"     | Network IP address                  |

### File Operations

| Say                               | Action                    |
| --------------------------------- | ------------------------- |
| "Create a file named notes.txt"   | Creates file              |
| "Create a folder called projects" | Creates directory         |
| "Delete file test.txt"            | Deletes file              |
| "List files in Desktop"           | Lists directory contents  |
| "Search for files named report"   | Searches for files        |
| "Open file readme.txt"            | Opens file in default app |

### Screenshots

| Say                  | Action          |
| -------------------- | --------------- |
| "Take a screenshot"  | Captures screen |
| "Capture screenshot" | Captures screen |
| "Grab a screenshot"  | Captures screen |

### Date & Time

| Say               | Action          |
| ----------------- | --------------- |
| "What time is it" | Current time    |
| "What's the date" | Current date    |
| "What day is it"  | Day of the week |

### Process Management

| Say                      | Action                |
| ------------------------ | --------------------- |
| "List running processes" | Show active processes |
| "Show tasks"             | Show active processes |

### Media

| Say           | Action      |
| ------------- | ----------- |
| "Play music"  | Play media  |
| "Pause music" | Pause media |

### System

| Say           | Action            |
| ------------- | ----------------- |
| "Lock screen" | Lock the computer |
| "Lock PC"     | Lock the computer |

### Misc

| Say                        | Action                 |
| -------------------------- | ---------------------- |
| "Tell me a joke"           | Random joke            |
| "What's your name"         | Assistant introduction |
| "Help" / "What can you do" | List capabilities      |
| "Clear history"            | Clear chat history     |
| "Exit" / "Goodbye"         | Shut down assistant    |

### AI Chat

Anything that doesn't match a command is sent to the AI provider for a conversational response (requires API key in `.env`).

---

## Configuration

### `config/settings.json`

| Setting                        | Default                      | Description                                      |
| ------------------------------ | ---------------------------- | ------------------------------------------------ |
| `voice.stt_engine`           | `"vosk"`                   | Speech engine: vosk, sphinx, powershell_sapi     |
| `voice.tts_rate`             | `175`                      | Text-to-speech speed                             |
| `voice.tts_volume`           | `0.9`                      | TTS volume (0.0–1.0)                            |
| `voice.listen_timeout`       | `10`                       | Max seconds to wait for speech                   |
| `voice.pause_threshold`      | `2.0`                      | Silence duration to end phrase                   |
| `voice.energy_threshold`     | `150`                      | Microphone sensitivity                           |
| `ai.provider`                | `"ollama"`                 | AI provider priority: ollama → gemini → openai |
| `ai.ollama_model`            | `"qwen2.5:32b"`            | Ollama model for general AI responses            |
| `ai.ollama_correction_model` | `"llama3.1:8b"`            | Ollama model used for fast STT correction        |
| `ai.ollama_base_url`         | `"http://localhost:11434"` | Ollama server URL                                |
| `ai.gemini_api_key`          | `""`                       | Google Gemini API key (cloud fallback)           |

### Ollama (recommended — fully local, no API key)

Install [Ollama](https://ollama.com) and pull the models:

```powershell
ollama pull llama3.1:8b     # fast STT correction
ollama pull qwen2.5:32b     # general AI responses (or any model you prefer)
ollama serve                 # keep running in background
```

Jarvis will auto-detect Ollama at startup. No `.env` or API keys needed.

### `config/commands.json`

- `app_aliases` — Map friendly names to executables (add your own apps here)
- `search_engines` — URL templates for web searches
- `quick_responses` — Canned replies for greetings

### `.env` (optional, for cloud AI fallback)

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...
```

Cloud providers are only used if Ollama is not running or a model isn't available.

---

## Project Structure

```
local-assistant/
├── main.py                  # Entry point
├── assistant/
│   ├── voice_handler.py     # STT/TTS (Vosk, Sphinx, SAPI)
│   ├── command_processor.py # NLP pattern matching + normalization
│   ├── system_controller.py # App launch, files, volume, etc.
│   ├── ai_integration.py    # Ollama/OpenAI/Claude/Gemini + STT correction
│   └── agents/
│       ├── __init__.py      # Agent registry (auto-discovers agents)
│       ├── base_agent.py    # Base class for all agents
│       └── briefing_agent.py# Morning briefing (Outlook + Jira → HTML)
├── ui/
│   ├── main_window.py       # PyQt6 glassmorphism window
│   ├── animations.py        # Orb, particles, waveform widgets
│   └── styles.qss           # Qt stylesheet
├── config/
│   ├── settings.json        # Runtime settings
│   └── commands.json        # App aliases & search engines
├── assets/
│   └── vosk-model/          # Offline speech model (downloaded)
├── output/                  # Agent-generated files (HTML briefings, etc.)
├── .env                     # Secrets (gitignored)
├── download_vosk_model.py   # One-time model downloader
└── requirements.txt         # Python dependencies
```

## Requirements

- Python 3.11+
- Windows 10/11
- Microphone (USB headset recommended)
- ~40 MB disk for Vosk model
- [Ollama](https://ollama.com) (optional but recommended for AI correction + responses)

---

## Agents

Jarvis supports modular **agents** — each lives in `assistant/agents/` and handles a specific domain.

### Morning Briefing Agent

> *"Hey Jarvis, morning briefing"* / *"give briefing"* / *"newspaper"*

Generates a newspaper-style HTML page with:
- **Outlook emails** — today's inbox (unread count, subjects, previews)
- **Calendar** — today's meetings with times and organizers
- **Jira tickets** — open issues assigned to you, days open, priority
- **AI summary** — spoken overview of the most important items

The HTML opens in your default browser automatically.

#### Setup

Add your credentials to the `.env` file (never commit this file):

```env
# Microsoft Graph (Outlook + Calendar)
MS_CLIENT_ID=your-client-id
MS_TENANT_ID=your-tenant-id
MS_CLIENT_SECRET=your-client-secret

# Jira
JIRA_BASE_URL=https://your-jira-server.com
JIRA_PAT=your-personal-access-token
JIRA_USER=your-username
```

You can also adjust the Jira JQL query in `config/settings.json` under `agents.briefing.jira_jql`.

---

### Web Page Agent

> *"Open webpage"* → Jarvis asks *"Which page?"* → speak the page name

**Two-step flow:**
1. Say **"open webpage"** — Jarvis responds with *"Which page? Say Jira, Kanban board, CI CD board, or a repo name in Bitbucket."*
2. Say one of the commands below — Jarvis opens it in **Mozilla Firefox**.

#### Predefined pages

| Say (after "open webpage") | Opens                                          |
| -------------------------- | ---------------------------------------------- |
| "Jira"                     | Jira project dashboard                         |
| "Kanban board"             | Scrum / Kanban sprint board                    |
| "CI CD board"              | CI/CD pipeline board                           |

#### Bitbucket repositories

Say **"[repo name] in Bitbucket"** or **"[repo name] repo"** after the trigger.

- Spoken repo names are automatically converted to kebab-case:  
  *"cx data visualization"* → `cx-data-visualization`
- Repos are matched against your local `C:\Git` folder (fuzzy match supported).
- Unknown repos default to the `ASIOS` project. Known pipeline repos use `ASMPAPP`.

| Say (after "open webpage")                | Opens                                                         |
| ----------------------------------------- | ------------------------------------------------------------- |
| "pipelines in bitbucket"                  | `ASMPAPP/repos/pipelines/browse`                              |
| "cx data visualization in bitbucket"      | `ASIOS/repos/cx-data-visualization/browse`                    |
| "pipeline tools in bitbucket"             | `ASMPAPP/repos/pipeline-tools/browse`                         |
| "[any repo from C:\Git] in bitbucket"     | Matching Bitbucket repo                                       |

To add more repos with non-default projects, edit `REPO_PROJECTS` in  
`assistant/agents/webpage_agent.py`.
