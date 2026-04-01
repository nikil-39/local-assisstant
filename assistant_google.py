"""
🎤 VOICE ASSISTANT - Using Google Speech Recognition (FREE & Accurate!)

Windows SAPI is terrible for accuracy. This version uses Google's FREE speech API.

SETUP (one-time):
    pip install SpeechRecognition pyaudio

USAGE:
    python assistant_google.py
"""

import subprocess
import os
import sys
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# Auto-install dependencies
# ═══════════════════════════════════════════════════════════════════════════

def install_deps():
    packages = []
    try:
        import speech_recognition
    except ImportError:
        packages.append('SpeechRecognition')
    
    try:
        import pyaudio
    except ImportError:
        packages.append('pyaudio')
    
    if packages:
        print(f"  Installing: {', '.join(packages)}...")
        for pkg in packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg, '-q'])
        print("  ✅ Done! Restarting...\n")
        os.execv(sys.executable, [sys.executable] + sys.argv)

install_deps()

import speech_recognition as sr

# ═══════════════════════════════════════════════════════════════════════════
# 🎨 Terminal UI  
# ═══════════════════════════════════════════════════════════════════════════

class C:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def banner():
    print(f"""{C.CYAN}
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   🎤 VOICE ASSISTANT (Google Speech - FREE & Accurate!)              ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                       ║
║   Press ENTER to speak • Type commands • Say "exit" to quit          ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    {C.END}""")

# ═══════════════════════════════════════════════════════════════════════════
# 🎤 Google Speech Recognition (FREE!)
# ═══════════════════════════════════════════════════════════════════════════

class VoiceRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        
        print(f"{C.YELLOW}  🎤 Calibrating microphone (1 second)...{C.END}")
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print(f"{C.GREEN}  ✅ Microphone ready!{C.END}\n")
    
    def listen(self):
        """Listen and transcribe using Google Speech (FREE!)"""
        print(f"{C.RED}{C.BOLD}\n  🔴 LISTENING... (speak now, auto-stops when you pause){C.END}\n")
        
        try:
            with self.mic as source:
                # Listen with timeout
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=10)
            
            print(f"{C.YELLOW}  🔄 Transcribing with Google...{C.END}")
            
            # Use Google Speech Recognition (FREE, no API key needed!)
            text = self.recognizer.recognize_google(audio)
            return text
            
        except sr.WaitTimeoutError:
            print(f"{C.RED}  ⏰ No speech detected (timeout){C.END}")
            return None
        except sr.UnknownValueError:
            print(f"{C.RED}  ❓ Could not understand audio{C.END}")
            return None
        except sr.RequestError as e:
            print(f"{C.RED}  ❌ Google API error: {e}{C.END}")
            print(f"{C.YELLOW}     Check your internet connection{C.END}")
            return None
        except Exception as e:
            print(f"{C.RED}  ❌ Error: {e}{C.END}")
            return None

# ═══════════════════════════════════════════════════════════════════════════
# 🛠️ PowerShell Commands
# ═══════════════════════════════════════════════════════════════════════════

def run_ps(cmd):
    try:
        r = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True, timeout=30)
        return r.stdout.strip()
    except:
        return ""

APP_MAP = {
    'outlook': 'Start-Process outlook',
    'mail': 'Start-Process outlook',
    'email': 'Start-Process outlook',
    'word': 'Start-Process winword',
    'excel': 'Start-Process excel',
    'powerpoint': 'Start-Process powerpnt',
    'teams': 'Start-Process ms-teams:',
    'chrome': 'Start-Process chrome',
    'browser': 'Start-Process chrome',
    'firefox': 'Start-Process firefox',
    'edge': 'Start-Process msedge',
    'notepad': 'Start-Process notepad',
    'calculator': 'Start-Process calc',
    'calc': 'Start-Process calc',
    'explorer': 'Start-Process explorer',
    'files': 'Start-Process explorer',
    'terminal': 'Start-Process wt',
    'cmd': 'Start-Process cmd',
    'settings': 'Start-Process ms-settings:',
    'vscode': 'Start-Process code',
    'vs code': 'Start-Process code',
    'visual studio code': 'Start-Process code',
    'code': 'Start-Process code',
    'spotify': 'Start-Process spotify',
    'discord': 'Start-Process discord',
    'slack': 'Start-Process slack',
    'zoom': 'Start-Process zoom',
    'jira': 'Start-Process "https://rb-tracker.bosch.com"',
    'whatsapp': 'Start-Process WhatsApp:',
}

def open_app(name):
    key = name.lower().strip()
    # Try exact match
    if key in APP_MAP:
        run_ps(APP_MAP[key])
        return f"Opening {name}..."
    # Try partial match
    for app_key, cmd in APP_MAP.items():
        if app_key in key or key in app_key:
            run_ps(cmd)
            return f"Opening {app_key}..."
    # Try direct
    run_ps(f'Start-Process "{name}"')
    return f"Trying to open {name}..."

def search_web(query, engine='google'):
    engines = {
        'google': 'https://www.google.com/search?q=',
        'youtube': 'https://www.youtube.com/results?search_query=',
        'github': 'https://github.com/search?q=',
    }
    url = engines.get(engine, engines['google']) + query.replace(' ', '+')
    run_ps(f'Start-Process "{url}"')
    return f'Searching "{query}"...'

def open_url(url):
    if not url.startswith('http'):
        url = 'https://' + url
    run_ps(f'Start-Process "{url}"')
    return f'Opening {url}...'

# ═══════════════════════════════════════════════════════════════════════════
# 🧠 Command Parser
# ═══════════════════════════════════════════════════════════════════════════

def parse(text):
    import re
    t = text.lower().strip()
    
    # Exit
    if any(w in t for w in ['exit', 'quit', 'bye', 'goodbye', 'stop', 'close assistant']):
        return {'action': 'exit'}
    
    # Help
    if t in ['help', 'commands', 'what can you do']:
        return {'action': 'help'}
    
    # Open patterns: "open outlook", "launch chrome", "start teams"
    m = re.match(r'^(open|launch|start|run)\s+(.+)$', t)
    if m:
        target = m.group(2).strip()
        if any(x in target for x in ['.com', '.org', '.io', 'http']):
            return {'action': 'url', 'target': target}
        return {'action': 'open', 'app': target}
    
    # Just app name: "outlook", "chrome"
    for app in APP_MAP:
        if t == app or t == f"the {app}":
            return {'action': 'open', 'app': app}
    
    # Search: "search for cats", "google python tutorial", "youtube music"
    m = re.match(r'^(search|search for|google|youtube|github|find)\s+(.+)$', t)
    if m:
        engine = m.group(1).lower()
        if engine in ['search', 'search for', 'find']:
            engine = 'google'
        return {'action': 'search', 'query': m.group(2), 'engine': engine}
    
    # Go to URL: "go to google.com"
    m = re.match(r'^(go to|goto|visit|navigate to)\s+(.+)$', t)
    if m:
        return {'action': 'url', 'target': m.group(2)}
    
    # Time
    if any(w in t for w in ['time', 'date', 'what time', 'what day']):
        return {'action': 'time'}
    
    # Lock
    if 'lock' in t:
        return {'action': 'lock'}
    
    # PowerShell
    m = re.match(r'^(ps|powershell|run|execute)[:;]?\s+(.+)$', t)
    if m:
        return {'action': 'command', 'command': m.group(2)}
    
    return {'action': 'unknown', 'input': text}

# ═══════════════════════════════════════════════════════════════════════════
# 🤖 Execute Commands
# ═══════════════════════════════════════════════════════════════════════════

def show_help():
    print(f"""{C.CYAN}
  ╔═══════════════════════════════════════════════════════════════════╗
  ║  🎤 SAY THESE COMMANDS:                                           ║
  ╠═══════════════════════════════════════════════════════════════════╣
  ║  "Open Outlook"        - Opens Outlook                            ║
  ║  "Open Chrome"         - Opens Chrome                             ║
  ║  "Open VS Code"        - Opens Visual Studio Code                 ║
  ║  "Open Teams"          - Opens Microsoft Teams                    ║
  ║  "Search [anything]"   - Google search                            ║
  ║  "YouTube [anything]"  - YouTube search                           ║
  ║  "Go to google.com"    - Open a website                           ║
  ║  "What time is it"     - Show current time                        ║
  ║  "Lock"                - Lock screen                              ║
  ║  "Exit"                - Close assistant                          ║
  ╚═══════════════════════════════════════════════════════════════════╝
    {C.END}""")

def execute(parsed):
    action = parsed.get('action')
    
    if action == 'exit':
        print(f"{C.WHITE}\n  🤖 Goodbye! 👋\n{C.END}")
        return False
    
    elif action == 'help':
        show_help()
    
    elif action == 'open':
        print(f"{C.YELLOW}  ⚡ Opening...{C.END}")
        result = open_app(parsed['app'])
        print(f"{C.GREEN}  ✅ {result}{C.END}")
    
    elif action == 'url':
        print(f"{C.YELLOW}  ⚡ Opening...{C.END}")
        result = open_url(parsed['target'])
        print(f"{C.GREEN}  ✅ {result}{C.END}")
    
    elif action == 'search':
        print(f"{C.YELLOW}  ⚡ Searching...{C.END}")
        result = search_web(parsed['query'], parsed.get('engine', 'google'))
        print(f"{C.GREEN}  ✅ {result}{C.END}")
    
    elif action == 'time':
        now = datetime.now()
        print(f"{C.WHITE}\n  🤖 It's {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}\n{C.END}")
    
    elif action == 'lock':
        print(f"{C.YELLOW}  ⚡ Locking...{C.END}")
        run_ps('rundll32.exe user32.dll,LockWorkStation')
        print(f"{C.GREEN}  ✅ Locking screen...{C.END}")
    
    elif action == 'command':
        print(f"{C.YELLOW}  ⚡ Running...{C.END}")
        result = run_ps(parsed['command'])
        print(f"{C.CYAN}\n  📤 {result or '(no output)'}{C.END}")
    
    else:
        print(f"{C.WHITE}\n  🤖 I heard \"{parsed['input']}\" but don't understand it.")
        print(f"     Try: \"open outlook\", \"search cats\", \"what time is it\"{C.END}")
    
    return True

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    banner()
    
    # Initialize voice
    try:
        voice = VoiceRecognizer()
        voice_ok = True
    except Exception as e:
        print(f"{C.RED}  ❌ Voice not available: {e}{C.END}")
        print(f"{C.YELLOW}     You can still type commands.{C.END}\n")
        voice_ok = False
    
    running = True
    
    while running:
        try:
            print(f"{C.GREEN}\n  [Press ENTER for 🎤 Voice | Or type a command]{C.END}")
            user_input = input(f"{C.GREEN}  > {C.END}")
            
            # Empty input = voice mode
            if user_input.strip() == '':
                if voice_ok:
                    text = voice.listen()
                    if text:
                        print(f"{C.MAGENTA}\n  🎤 You said: \"{text}\"{C.END}")
                        parsed = parse(text)
                        running = execute(parsed)
                    # If no text recognized, just continue the loop
                else:
                    print(f"{C.YELLOW}  Voice not available. Type a command instead.{C.END}")
            
            # Text input
            else:
                parsed = parse(user_input.strip())
                running = execute(parsed)
                
        except KeyboardInterrupt:
            print(f"{C.WHITE}\n  🤖 Goodbye! 👋{C.END}")
            break
        except EOFError:
            # Handle Ctrl+Z or pipe input ending
            print(f"{C.WHITE}\n  🤖 Goodbye! 👋{C.END}")
            break
        except Exception as e:
            print(f"{C.RED}  ❌ Error: {e}{C.END}")
            # Don't exit on error, continue loop

if __name__ == '__main__':
    main()
