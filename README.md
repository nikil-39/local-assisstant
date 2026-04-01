# 🤖 Local Command Assistant

An **always-on local assistant** that executes system commands using natural language. Inspired by Claude Code's PowerShellTool and BashTool patterns.

## 🚀 Quick Start

### Option 1: Zero Dependencies (Recommended for Office Laptops!)
```powershell
cd c:\Github\local-assistant
python assistant_windows.py
```
✅ Uses **Windows built-in Speech Recognition (SAPI)**  
✅ **NO external tools or pip installs required!**  
✅ Works offline  

### Option 2: Text Mode Only
```powershell
npm start
```

---

## 🎤 Voice Setup (Zero Dependencies Version)

**No setup required!** Just run:
```powershell
python assistant_windows.py
```

The script uses **Windows Speech Recognition (SAPI)** which is built into Windows.

### How to Use Voice:
1. Press **ENTER** (empty input)
2. Speak your command clearly (e.g., "Open Outlook")
3. Wait for auto-detection when you stop speaking
4. Command executes!

### Supported Voice Commands:
```
"Open Outlook"          → Opens Outlook
"Open Chrome"           → Opens Chrome  
"Open VS Code"          → Opens VS Code
"Open Teams"            → Opens Microsoft Teams
"Open Jira"             → Opens Bosch Jira
"Search weather today"  → Google search
"YouTube funny cats"    → YouTube search
"Go to github.com"      → Opens website
"What time is it"       → Shows time
"Lock screen"           → Locks PC
"Exit"                  → Closes assistant
```

---

## 🧠 Option 3: Voice + Bosch LLM Farm (Smart Commands!)

Uses your company's LLM for intelligent command parsing:

```powershell
# Set your LLM Farm key
set GENAIPLATFORM_FARM_SUBSCRIPTION_KEY=your-api-key-here

python assistant_llm.py
```

With LLM, you can say things more naturally:
- "Can you open my email please?" → Opens Outlook
- "I need to check something on Jira" → Opens Jira
- "Find me some Python tutorials" → Searches Google

---

## 💬 Available Commands

### 🚀 Open Apps
| Command | Action |
|---------|--------|
| `open outlook` | Open Microsoft Outlook |
| `open chrome` | Open Google Chrome |
| `open vscode` | Open Visual Studio Code |
| `open calculator` | Open Calculator |
| `open [any app]` | Try to open any app by name |

### Supported Apps
```
Microsoft Office: outlook, word, excel, powerpoint, teams, onenote
Browsers: chrome, firefox, edge, brave
System: notepad, calculator, terminal, explorer, settings, task manager
Dev Tools: vscode, git bash
Media: spotify, vlc
Communication: discord, slack, zoom, whatsapp, telegram
Others: steam, obs
```

### 🔍 Search
| Command | Action |
|---------|--------|
| `search [query]` | Google search |
| `youtube [query]` | YouTube search |
| `github [query]` | GitHub search |
| `bing [query]` | Bing search |

### 🌐 Web
| Command | Action |
|---------|--------|
| `go to github.com` | Open a website |
| `visit google.com` | Open a website |

### 💻 System
| Command | Action |
|---------|--------|
| `system info` | Show PC info (OS, CPU, RAM) |
| `show processes` | List top running processes |
| `kill chrome` | Kill a process |
| `time` / `date` | Show current time |
| `lock` | Lock screen |
| `screenshot` | Take a screenshot (saves to Desktop) |
| `sleep` | Put computer to sleep |
| `shutdown` | Shutdown (10s delay) |
| `restart` | Restart (10s delay) |

### ⚡ Direct Commands
| Command | Action |
|---------|--------|
| `ps: [command]` | Run any PowerShell command |
| `cmd: [command]` | Run any PowerShell command |

### 🚪 Exit
| Command | Action |
|---------|--------|
| `exit` / `quit` / `bye` | Close assistant |

---

## 🔄 Making It "Always On"

### Option 1: Run in Background Terminal
```powershell
Start-Process powershell -ArgumentList "-NoExit -Command cd c:\Github\local-assistant; node assistant.js"
```

### Option 2: Create a Startup Shortcut

1. Create `assistant.bat` in the project folder:
```batch
@echo off
cd c:\Github\local-assistant
node assistant.js
```

2. Create a shortcut to `assistant.bat`

3. Press `Win + R`, type `shell:startup`, press Enter

4. Move the shortcut to that folder

Now the assistant will start automatically when Windows boots!

### Option 3: Run as Windows Service (Advanced)

Using [node-windows](https://www.npmjs.com/package/node-windows):

```powershell
npm install -g node-windows

# Create service installer
node -e "
const Service = require('node-windows').Service;
const svc = new Service({
  name: 'Local Assistant',
  description: 'Always-on local command assistant',
  script: 'c:\\Github\\local-assistant\\assistant.js'
});
svc.on('install', () => svc.start());
svc.install();
"
```

---

## 🔮 Future Enhancements

| Feature | How to Implement |
|---------|------------------|
| **🎤 Voice Input** | Add `node-record-lpcm16` + Whisper API for speech-to-text |
| **🤖 AI Responses** | Connect to local [Ollama](https://ollama.ai/) LLM for intelligent responses |
| **⌨️ Global Hotkey** | Use `node-global-key-listener` to trigger assistant from anywhere |
| **🖥️ System Tray** | Use [Electron](https://www.electronjs.org/) for GUI with tray icon |
| **📋 Clipboard** | Add clipboard read/write commands |
| **📅 Reminders** | Add scheduled task reminders using node-cron |
| **🔊 Text-to-Speech** | Add `say.js` for voice responses |

### Example: Adding Ollama AI

```javascript
// Future: Connect to local Ollama
import Ollama from 'ollama';

async function askAI(prompt) {
  const response = await ollama.chat({
    model: 'llama2',
    messages: [{ role: 'user', content: prompt }],
  });
  return response.message.content;
}
```

### Example: Adding Voice Input

```javascript
// Future: Add voice recognition
import record from 'node-record-lpcm16';
import { Whisper } from 'whisper-node';

const whisper = new Whisper('base.en');
// Record → Transcribe → Execute
```

---

## 🏗️ Architecture

Inspired by Claude Code's tool patterns:

```
┌─────────────────────────────────────────────────────┐
│                 Local Assistant                      │
├─────────────────────────────────────────────────────┤
│  CommandParser    →  Parse natural language         │
│  PowerShellTool   →  Execute system commands        │
│  UI               →  Beautiful terminal output      │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   Windows System    │
              │   (PowerShell)      │
              └─────────────────────┘
```

---

## 📝 License

MIT - Feel free to modify and use!

---

## 🙏 Credits

Patterns inspired by [Claude Code](https://github.com/yasasbanukaofficial/claude-code) source.
