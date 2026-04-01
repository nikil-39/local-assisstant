"""
🎤 VOICE ASSISTANT - OFFLINE VERSION (No Internet Needed!)

Uses Vosk for OFFLINE speech recognition - works behind corporate proxy!

SETUP:
    pip install vosk sounddevice

USAGE:
    python assistant_offline.py
"""

import subprocess
import os
import sys
from datetime import datetime
import json
import queue
import zipfile
import urllib.request

# ═══════════════════════════════════════════════════════════════════════════
# Auto-install dependencies
# ═══════════════════════════════════════════════════════════════════════════

def install_deps():
    packages = []
    try:
        import vosk
    except ImportError:
        packages.append('vosk')
    
    try:
        import sounddevice
    except ImportError:
        packages.append('sounddevice')
    
    if packages:
        print(f"  Installing: {', '.join(packages)}...")
        for pkg in packages:
            # Use --trusted-host to bypass SSL issues with proxy
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', pkg, '-q',
                '--trusted-host', 'pypi.org',
                '--trusted-host', 'pypi.python.org', 
                '--trusted-host', 'files.pythonhosted.org'
            ])
        print("  ✅ Done! Please restart the script.\n")
        sys.exit(0)

install_deps()

import vosk
import sounddevice as sd

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
║   🎤 VOICE ASSISTANT - 100% OFFLINE (No Proxy Issues!)               ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║   Uses Vosk - Works behind corporate firewalls!                      ║
║                                                                       ║
║   Press ENTER to speak • Type commands • Say "exit" to quit          ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    {C.END}""")

# ═══════════════════════════════════════════════════════════════════════════
# 🎤 Vosk Offline Speech Recognition
# ═══════════════════════════════════════════════════════════════════════════

MODEL_PATH = os.path.join(os.path.dirname(__file__), "vosk-model-small-en-us")
MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"

def download_model():
    """Download Vosk model if not present"""
    if os.path.exists(MODEL_PATH):
        return True
    
    print(f"{C.YELLOW}  First time setup: Downloading speech model (~40MB)...{C.END}")
    print(f"{C.YELLOW}  This only happens once.{C.END}\n")
    
    zip_path = MODEL_PATH + ".zip"
    
    try:
        # Create a proxy handler if needed
        proxy_handler = urllib.request.ProxyHandler({
            'http': 'http://127.0.0.1:3128',
            'https': 'http://127.0.0.1:3128'
        })
        opener = urllib.request.build_opener(proxy_handler)
        urllib.request.install_opener(opener)
        
        # Download
        print(f"  Downloading from alphacephei.com...")
        urllib.request.urlretrieve(MODEL_URL, zip_path)
        
        # Extract
        print(f"  Extracting model...")
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(os.path.dirname(__file__))
        
        # Rename to expected path
        extracted_name = "vosk-model-small-en-us-0.15"
        if os.path.exists(os.path.join(os.path.dirname(__file__), extracted_name)):
            os.rename(
                os.path.join(os.path.dirname(__file__), extracted_name),
                MODEL_PATH
            )
        
        # Cleanup
        os.remove(zip_path)
        
        print(f"{C.GREEN}  ✅ Model downloaded successfully!{C.END}\n")
        return True
        
    except Exception as e:
        print(f"{C.RED}  ❌ Failed to download model: {e}{C.END}")
        print(f"{C.YELLOW}")
        print(f"  Manual download instructions:")
        print(f"  1. Download from: https://alphacephei.com/vosk/models")
        print(f"  2. Get: vosk-model-small-en-us-0.15.zip")
        print(f"  3. Extract to: {MODEL_PATH}")
        print(f"{C.END}")
        return False


class VoskRecognizer:
    """Offline speech recognition using Vosk"""
    
    def __init__(self):
        vosk.SetLogLevel(-1)  # Suppress Vosk logs
        
        if not os.path.exists(MODEL_PATH):
            if not download_model():
                raise Exception("Speech model not available")
        
        print(f"{C.CYAN}  Loading speech model...{C.END}")
        self.model = vosk.Model(MODEL_PATH)
        self.samplerate = 16000
        print(f"{C.GREEN}  ✅ Speech model loaded!{C.END}\n")
    
    def listen(self, timeout=8):
        """Listen and transcribe speech"""
        print(f"{C.RED}{C.BOLD}\n  🔴 LISTENING... (speak now, {timeout}s timeout){C.END}\n")
        
        q = queue.Queue()
        
        def callback(indata, frames, time, status):
            q.put(bytes(indata))
        
        rec = vosk.KaldiRecognizer(self.model, self.samplerate)
        
        try:
            with sd.RawInputStream(
                samplerate=self.samplerate,
                blocksize=8000,
                dtype='int16',
                channels=1,
                callback=callback
            ):
                result_text = ""
                silence_count = 0
                max_silence = 15  # ~2 seconds of silence
                
                import time
                start = time.time()
                
                while time.time() - start < timeout:
                    try:
                        data = q.get(timeout=0.1)
                    except queue.Empty:
                        continue
                    
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        if result.get('text'):
                            result_text = result['text']
                            break
                    else:
                        partial = json.loads(rec.PartialResult())
                        if partial.get('partial'):
                            silence_count = 0
                            # Show partial results
                            print(f"\r{C.YELLOW}  Hearing: {partial['partial'][:50]}...{C.END}", end='', flush=True)
                        else:
                            silence_count += 1
                            if silence_count > max_silence and result_text == "":
                                pass  # Keep waiting
                
                # Get final result
                final = json.loads(rec.FinalResult())
                if final.get('text'):
                    result_text = final['text']
                
                print()  # New line after partial results
                
                if result_text:
                    return result_text
                else:
                    print(f"{C.RED}  ⏰ No speech detected{C.END}")
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
}

def open_app(name):
    key = name.lower().strip()
    if key in APP_MAP:
        run_ps(APP_MAP[key])
        return f"Opening {name}..."
    for app_key, cmd in APP_MAP.items():
        if app_key in key or key in app_key:
            run_ps(cmd)
            return f"Opening {app_key}..."
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
    if any(w in t for w in ['exit', 'quit', 'bye', 'goodbye', 'stop']):
        return {'action': 'exit'}
    
    # Help
    if t in ['help', 'commands', 'what can you do']:
        return {'action': 'help'}
    
    # Open patterns
    m = re.match(r'^(open|launch|start|run)\s+(.+)$', t)
    if m:
        target = m.group(2).strip()
        if any(x in target for x in ['.com', '.org', '.io', 'http']):
            return {'action': 'url', 'target': target}
        return {'action': 'open', 'app': target}
    
    # Just app name
    for app in APP_MAP:
        if t == app or t == f"the {app}":
            return {'action': 'open', 'app': app}
    
    # Search
    m = re.match(r'^(search|search for|google|youtube|github|find)\s+(.+)$', t)
    if m:
        engine = m.group(1).lower()
        if engine in ['search', 'search for', 'find']:
            engine = 'google'
        return {'action': 'search', 'query': m.group(2), 'engine': engine}
    
    # Go to URL
    m = re.match(r'^(go to|goto|visit|navigate to)\s+(.+)$', t)
    if m:
        return {'action': 'url', 'target': m.group(2)}
    
    # Time
    if any(w in t for w in ['time', 'date', 'what time', 'what day']):
        return {'action': 'time'}
    
    # Lock
    if 'lock' in t:
        return {'action': 'lock'}
    
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
  ║  "Open Teams"          - Opens Microsoft Teams                    ║
  ║  "Open VS Code"        - Opens VS Code                            ║
  ║  "Search cats"         - Google search                            ║
  ║  "YouTube music"       - YouTube search                           ║
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
    
    else:
        print(f"{C.WHITE}\n  🤖 I heard \"{parsed['input']}\" but don't understand it.")
        print(f"     Try: \"open outlook\", \"search cats\", \"what time\"{C.END}")
    
    return True

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    banner()
    
    # Initialize voice
    try:
        voice = VoskRecognizer()
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
            
            if user_input.strip() == '':
                if voice_ok:
                    text = voice.listen()
                    if text:
                        print(f"{C.MAGENTA}\n  🎤 You said: \"{text}\"{C.END}")
                        parsed = parse(text)
                        running = execute(parsed)
                else:
                    print(f"{C.YELLOW}  Voice not available. Type a command.{C.END}")
            else:
                parsed = parse(user_input.strip())
                running = execute(parsed)
                
        except KeyboardInterrupt:
            print(f"{C.WHITE}\n  🤖 Goodbye! 👋{C.END}")
            break
        except EOFError:
            break
        except Exception as e:
            print(f"{C.RED}  ❌ Error: {e}{C.END}")

if __name__ == '__main__':
    main()
