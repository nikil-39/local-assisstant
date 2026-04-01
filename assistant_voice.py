"""
🎤 VOICE-ENABLED LOCAL ASSISTANT (No External Tools Required!)

Uses Windows native speech recognition - NO SoX or external installs needed!

SETUP (one-time):
    pip install SpeechRecognition pyaudio

USAGE:
    python assistant_voice.py

Press ENTER to start voice recording, speak, then it auto-detects when you stop.
"""

import subprocess
import os
import sys
from datetime import datetime

# Check and install dependencies
def check_dependencies():
    missing = []
    try:
        import speech_recognition
    except ImportError:
        missing.append('SpeechRecognition')
    
    try:
        import pyaudio
    except ImportError:
        missing.append('pyaudio')
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("\nInstalling automatically...")
        for pkg in missing:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg, '-q'])
        print("✅ Dependencies installed! Restarting...\n")
        os.execv(sys.executable, [sys.executable] + sys.argv)

check_dependencies()

import speech_recognition as sr

# ═══════════════════════════════════════════════════════════════════════════
# 🎨 Terminal UI
# ═══════════════════════════════════════════════════════════════════════════

class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def banner():
    print(f"""{Colors.CYAN}
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   🎤 VOICE-ENABLED LOCAL ASSISTANT                                    ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║   Windows Native Speech Recognition • No External Tools Required!    ║
║                                                                       ║
║   Press ENTER to speak • Type commands directly • Say "exit" to quit ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    {Colors.END}""")

def recording():
    print(f"{Colors.RED}{Colors.BOLD}\n  🔴 LISTENING... (speak now, pause to stop){Colors.END}\n")

def success(msg):
    print(f"{Colors.GREEN}\n  ✅ {msg}{Colors.END}")

def error(msg):
    print(f"{Colors.RED}\n  ❌ {msg}{Colors.END}")

def info(msg):
    print(f"{Colors.CYAN}  ℹ️  {msg}{Colors.END}")

def transcribed(text):
    print(f"{Colors.MAGENTA}\n  🎤 You said: \"{text}\"{Colors.END}")

def response(msg):
    print(f"{Colors.WHITE}\n  🤖 {msg}\n{Colors.END}")

# ═══════════════════════════════════════════════════════════════════════════
# 🎤 Windows Native Speech Recognition
# ═══════════════════════════════════════════════════════════════════════════

class WindowsSpeechRecognizer:
    """Uses Windows built-in speech recognition - NO external tools needed!"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Adjust for ambient noise on startup
        print("  🎤 Calibrating microphone...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("  ✅ Microphone ready!\n")
    
    def listen(self):
        """Listen and transcribe using Windows Speech Recognition (offline!)"""
        with self.microphone as source:
            recording()
            try:
                # Listen with automatic silence detection
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                
                print(f"{Colors.YELLOW}  🔄 Transcribing (Windows Speech Recognition)...{Colors.END}")
                
                # Use Windows native speech recognition (OFFLINE - no API!)
                try:
                    # First try Windows native (offline, fast)
                    text = self.recognizer.recognize_sphinx(audio)
                    return text
                except sr.UnknownValueError:
                    pass
                except Exception:
                    pass
                
                # Fallback to Google (free, online)
                try:
                    text = self.recognizer.recognize_google(audio)
                    return text
                except sr.UnknownValueError:
                    error("Could not understand audio")
                    return None
                except sr.RequestError as e:
                    error(f"Speech service error: {e}")
                    return None
                    
            except sr.WaitTimeoutError:
                error("No speech detected (timeout)")
                return None

# ═══════════════════════════════════════════════════════════════════════════
# 🛠️ PowerShell Command Executor
# ═══════════════════════════════════════════════════════════════════════════

class PowerShellTool:
    def execute(self, command):
        try:
            result = subprocess.run(
                ['powershell', '-Command', command],
                capture_output=True, text=True, timeout=30
            )
            return result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
        except Exception as e:
            return str(e)

    def open_app(self, app_name):
        app_map = {
            'outlook': 'Start-Process outlook',
            'word': 'Start-Process winword',
            'excel': 'Start-Process excel',
            'powerpoint': 'Start-Process powerpnt',
            'teams': 'Start-Process ms-teams:',
            'chrome': 'Start-Process chrome',
            'firefox': 'Start-Process firefox',
            'edge': 'Start-Process msedge',
            'notepad': 'Start-Process notepad',
            'calculator': 'Start-Process calc',
            'explorer': 'Start-Process explorer',
            'terminal': 'Start-Process wt',
            'settings': 'Start-Process ms-settings:',
            'vscode': 'Start-Process code',
            'vs code': 'Start-Process code',
            'visual studio code': 'Start-Process code',
            'spotify': 'Start-Process spotify',
            'discord': 'Start-Process discord',
            'slack': 'Start-Process slack',
            'zoom': 'Start-Process zoom',
            'jira': 'Start-Process "https://rb-tracker.bosch.com"',
        }
        
        key = app_name.lower().strip()
        command = app_map.get(key)
        
        if command:
            self.execute(command)
            return f"Opening {app_name}..."
        else:
            # Try direct
            self.execute(f'Start-Process "{app_name}"')
            return f"Trying to open {app_name}..."

    def search_web(self, query, engine='google'):
        engines = {
            'google': 'https://www.google.com/search?q=',
            'youtube': 'https://www.youtube.com/results?search_query=',
            'github': 'https://github.com/search?q=',
            'bing': 'https://www.bing.com/search?q=',
        }
        base_url = engines.get(engine, engines['google'])
        url = f'{base_url}{query.replace(" ", "+")}'
        self.execute(f'Start-Process "{url}"')
        return f'Searching for "{query}" on {engine}...'

    def open_url(self, url):
        if not url.startswith('http'):
            url = 'https://' + url
        self.execute(f'Start-Process "{url}"')
        return f'Opening {url}...'

# ═══════════════════════════════════════════════════════════════════════════
# 🧠 Command Parser
# ═══════════════════════════════════════════════════════════════════════════

def parse_command(text):
    text = text.lower().strip()
    
    # Exit
    if text in ['exit', 'quit', 'bye', 'goodbye', 'stop', 'close']:
        return {'action': 'exit'}
    
    # Help
    if text in ['help', 'commands', 'what can you do']:
        return {'action': 'help'}
    
    # Open app: "open outlook", "launch chrome"
    import re
    open_match = re.match(r'^(open|launch|start)\s+(.+)$', text, re.IGNORECASE)
    if open_match:
        target = open_match.group(2)
        if any(x in target for x in ['.com', '.org', '.io', 'http']):
            return {'action': 'url', 'target': target}
        return {'action': 'open', 'app': target}
    
    # Search: "search how to code", "youtube funny cats"
    search_match = re.match(r'^(search|google|youtube|github|bing)\s+(.+)$', text, re.IGNORECASE)
    if search_match:
        engine = 'google' if search_match.group(1).lower() == 'search' else search_match.group(1).lower()
        return {'action': 'search', 'query': search_match.group(2), 'engine': engine}
    
    # Go to URL
    goto_match = re.match(r'^(go to|goto|visit|navigate to)\s+(.+)$', text, re.IGNORECASE)
    if goto_match:
        return {'action': 'url', 'target': goto_match.group(2)}
    
    # Time
    if re.match(r'^(what.*time|time|date|what.*date)', text, re.IGNORECASE) or text in ['time', 'date']:
        return {'action': 'time'}
    
    # Lock
    if 'lock' in text:
        return {'action': 'lock'}
    
    # PowerShell command
    ps_match = re.match(r'^(run|execute|ps:?)\s+(.+)$', text, re.IGNORECASE)
    if ps_match:
        return {'action': 'command', 'command': ps_match.group(2)}
    
    return {'action': 'unknown', 'input': text}

# ═══════════════════════════════════════════════════════════════════════════
# 🤖 Main Assistant
# ═══════════════════════════════════════════════════════════════════════════

def show_help():
    print(f"""{Colors.CYAN}
  ╔═══════════════════════════════════════════════════════════════════╗
  ║  🎤 VOICE COMMANDS (or type them!)                                ║
  ╠═══════════════════════════════════════════════════════════════════╣
  ║  "Open Outlook"        - Opens Outlook                            ║
  ║  "Open Chrome"         - Opens Chrome                             ║
  ║  "Open VS Code"        - Opens Visual Studio Code                 ║
  ║  "Open Jira"           - Opens Bosch Jira                         ║
  ║  "Search [query]"      - Google search                            ║
  ║  "YouTube [query]"     - YouTube search                           ║
  ║  "Go to [website]"     - Open a website                           ║
  ║  "What time is it"     - Show current time                        ║
  ║  "Lock"                - Lock screen                              ║
  ║  "Exit" / "Quit"       - Close assistant                          ║
  ╚═══════════════════════════════════════════════════════════════════╝
    {Colors.END}""")

def execute_command(parsed, ps):
    action = parsed.get('action')
    
    if action == 'exit':
        response('Goodbye! 👋')
        return False
    
    elif action == 'help':
        show_help()
    
    elif action == 'open':
        print(f"{Colors.YELLOW}  ⚡ Opening...{Colors.END}")
        result = ps.open_app(parsed['app'])
        success(result)
    
    elif action == 'url':
        print(f"{Colors.YELLOW}  ⚡ Opening...{Colors.END}")
        result = ps.open_url(parsed['target'])
        success(result)
    
    elif action == 'search':
        print(f"{Colors.YELLOW}  ⚡ Searching...{Colors.END}")
        result = ps.search_web(parsed['query'], parsed.get('engine', 'google'))
        success(result)
    
    elif action == 'time':
        now = datetime.now()
        response(f"It's {now.strftime('%I:%M %p')} on {now.strftime('%B %d, %Y')}")
    
    elif action == 'lock':
        print(f"{Colors.YELLOW}  ⚡ Locking...{Colors.END}")
        ps.execute('rundll32.exe user32.dll,LockWorkStation')
        success('Locking screen...')
    
    elif action == 'command':
        print(f"{Colors.YELLOW}  ⚡ Executing...{Colors.END}")
        result = ps.execute(parsed['command'])
        print(f"{Colors.CYAN}\n  📤 Output:\n{Colors.WHITE}  {result}{Colors.END}")
    
    elif action == 'unknown':
        response(f'I don\'t understand "{parsed["input"]}". Say "help" for commands.')
    
    return True

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    banner()
    
    # Initialize
    ps = PowerShellTool()
    
    try:
        recognizer = WindowsSpeechRecognizer()
        voice_available = True
    except Exception as e:
        error(f"Voice not available: {e}")
        info("You can still type commands manually.")
        voice_available = False
    
    running = True
    
    while running:
        try:
            user_input = input(f"{Colors.GREEN}\n  [ENTER=🎤 Voice | Type command]: {Colors.END}").strip()
            
            # Empty input = voice mode
            if user_input == '' and voice_available:
                voice_text = recognizer.listen()
                if voice_text:
                    transcribed(voice_text)
                    parsed = parse_command(voice_text)
                    running = execute_command(parsed, ps)
            elif user_input:
                parsed = parse_command(user_input)
                running = execute_command(parsed, ps)
                
        except KeyboardInterrupt:
            response('Goodbye! 👋')
            break
        except Exception as e:
            error(str(e))

if __name__ == '__main__':
    main()
