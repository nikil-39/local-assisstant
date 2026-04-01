"""
🎤 VOICE ASSISTANT - ZERO EXTERNAL DEPENDENCIES VERSION

Uses ONLY Windows built-in capabilities:
- Windows Speech Recognition (SAPI)
- PowerShell for commands

NO pip install needed! Just run:
    python assistant_windows.py
"""

import subprocess
import os
import sys
from datetime import datetime
import tempfile
import time

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
║   🎤 VOICE ASSISTANT (Windows Native - Zero Dependencies!)           ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║   Uses Windows Built-in Speech Recognition (SAPI)                    ║
║                                                                       ║
║   Press ENTER to speak • Type commands directly • Say "exit" to quit ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    {Colors.END}""")

# ═══════════════════════════════════════════════════════════════════════════
# 🎤 Windows Native Speech Recognition (via PowerShell + SAPI)
# ═══════════════════════════════════════════════════════════════════════════

def listen_windows_native(timeout=10):
    """
    Uses Windows Speech Recognition (SAPI) via PowerShell.
    NO external tools or pip packages needed!
    """
    
    print(f"{Colors.RED}{Colors.BOLD}\n  🔴 LISTENING... (speak now, will auto-stop after silence){Colors.END}\n")
    
    # PowerShell script that uses Windows Speech API (SAPI)
    ps_script = f'''
Add-Type -AssemblyName System.Speech
$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$recognizer.SetInputToDefaultAudioDevice()

# Create grammar that accepts any dictation
$grammar = New-Object System.Speech.Recognition.DictationGrammar
$recognizer.LoadGrammar($grammar)

# Set timeout
$recognizer.InitialSilenceTimeout = [TimeSpan]::FromSeconds({timeout})
$recognizer.EndSilenceTimeout = [TimeSpan]::FromSeconds(2)

try {{
    $result = $recognizer.Recognize()
    if ($result) {{
        Write-Output $result.Text
    }}
}} catch {{
    Write-Output ""
}} finally {{
    $recognizer.Dispose()
}}
'''
    
    try:
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True, 
            text=True, 
            timeout=timeout + 5
        )
        
        text = result.stdout.strip()
        if text:
            return text
        else:
            print(f"{Colors.RED}  ❌ Could not understand. Try speaking more clearly.{Colors.END}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"{Colors.RED}  ❌ Timeout - no speech detected{Colors.END}")
        return None
    except Exception as e:
        print(f"{Colors.RED}  ❌ Speech recognition error: {e}{Colors.END}")
        return None

# ═══════════════════════════════════════════════════════════════════════════
# 🛠️ PowerShell Command Executor
# ═══════════════════════════════════════════════════════════════════════════

def run_powershell(command):
    try:
        result = subprocess.run(
            ['powershell', '-Command', command],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
    except Exception as e:
        return str(e)

APP_MAP = {
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
    'telegram': 'Start-Process Telegram',
}

def open_app(name):
    key = name.lower().strip()
    command = APP_MAP.get(key)
    if command:
        run_powershell(command)
        return f"Opening {name}..."
    else:
        run_powershell(f'Start-Process "{name}"')
        return f"Trying to open {name}..."

def search_web(query, engine='google'):
    engines = {
        'google': 'https://www.google.com/search?q=',
        'youtube': 'https://www.youtube.com/results?search_query=',
        'github': 'https://github.com/search?q=',
        'bing': 'https://www.bing.com/search?q=',
    }
    url = engines.get(engine, engines['google']) + query.replace(' ', '+')
    run_powershell(f'Start-Process "{url}"')
    return f'Searching "{query}" on {engine}...'

def open_url(url):
    if not url.startswith('http'):
        url = 'https://' + url
    run_powershell(f'Start-Process "{url}"')
    return f'Opening {url}...'

# ═══════════════════════════════════════════════════════════════════════════
# 🧠 Natural Language Parser
# ═══════════════════════════════════════════════════════════════════════════

def parse_command(text):
    import re
    text = text.lower().strip()
    
    # Exit commands
    if any(word in text for word in ['exit', 'quit', 'bye', 'goodbye', 'stop assistant', 'close assistant']):
        return {'action': 'exit'}
    
    # Help
    if text in ['help', 'commands', 'what can you do', 'help me']:
        return {'action': 'help'}
    
    # Open app patterns
    patterns = [
        r'^(open|launch|start|run)\s+(.+)$',
        r'^(.+)\s+(open|launch)$',  # "outlook open"
    ]
    for pattern in patterns:
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            target = match.group(2) if 'open' in match.group(1).lower() else match.group(1)
            target = target.strip()
            # Check if it's a URL
            if any(x in target for x in ['.com', '.org', '.io', '.net', 'http', 'www']):
                return {'action': 'url', 'target': target}
            return {'action': 'open', 'app': target}
    
    # Search patterns
    search_match = re.match(r'^(search|google|youtube|github|bing|find)\s+(.+)$', text, re.IGNORECASE)
    if search_match:
        engine = 'google' if search_match.group(1).lower() in ['search', 'find'] else search_match.group(1).lower()
        return {'action': 'search', 'query': search_match.group(2), 'engine': engine}
    
    # "search for X" pattern
    search_for = re.match(r'^search\s+for\s+(.+)$', text, re.IGNORECASE)
    if search_for:
        return {'action': 'search', 'query': search_for.group(1), 'engine': 'google'}
    
    # Go to URL
    goto_match = re.match(r'^(go to|goto|visit|navigate to|open)\s+([\w\.]+\.(com|org|io|net|gov|edu).*)$', text, re.IGNORECASE)
    if goto_match:
        return {'action': 'url', 'target': goto_match.group(2)}
    
    # Time/Date
    if any(word in text for word in ['time', 'date', 'what time', 'what day']):
        return {'action': 'time'}
    
    # Lock screen
    if 'lock' in text and ('screen' in text or 'computer' in text or 'pc' in text or text == 'lock'):
        return {'action': 'lock'}
    
    # Direct PowerShell
    ps_match = re.match(r'^(ps|powershell|execute|command)[:;]?\s+(.+)$', text, re.IGNORECASE)
    if ps_match:
        return {'action': 'command', 'command': ps_match.group(2)}
    
    # Unknown - but try to be smart
    # If it looks like an app name, try to open it
    if len(text.split()) == 1 and text in APP_MAP:
        return {'action': 'open', 'app': text}
    
    return {'action': 'unknown', 'input': text}

# ═══════════════════════════════════════════════════════════════════════════
# 🤖 Main
# ═══════════════════════════════════════════════════════════════════════════

def show_help():
    print(f"""{Colors.CYAN}
  ╔═══════════════════════════════════════════════════════════════════╗
  ║  🎤 VOICE COMMANDS (or type them!)                                ║
  ╠═══════════════════════════════════════════════════════════════════╣
  ║  "Open Outlook"        - Opens Outlook                            ║
  ║  "Open Chrome"         - Opens Chrome                             ║
  ║  "Open VS Code"        - Opens Visual Studio Code                 ║
  ║  "Open Teams"          - Opens Microsoft Teams                    ║
  ║  "Open Jira"           - Opens Bosch Jira                         ║
  ║  "Search [query]"      - Google search                            ║
  ║  "YouTube [query]"     - YouTube search                           ║
  ║  "Go to google.com"    - Open a website                           ║
  ║  "What time is it"     - Show current time                        ║
  ║  "Lock screen"         - Lock your PC                             ║
  ║  "Exit"                - Close assistant                          ║
  ╚═══════════════════════════════════════════════════════════════════╝
    {Colors.END}""")

def execute(parsed):
    action = parsed.get('action')
    
    if action == 'exit':
        print(f"{Colors.WHITE}\n  🤖 Goodbye! 👋\n{Colors.END}")
        return False
    
    elif action == 'help':
        show_help()
    
    elif action == 'open':
        print(f"{Colors.YELLOW}  ⚡ Opening...{Colors.END}")
        result = open_app(parsed['app'])
        print(f"{Colors.GREEN}\n  ✅ {result}{Colors.END}")
    
    elif action == 'url':
        print(f"{Colors.YELLOW}  ⚡ Opening...{Colors.END}")
        result = open_url(parsed['target'])
        print(f"{Colors.GREEN}\n  ✅ {result}{Colors.END}")
    
    elif action == 'search':
        print(f"{Colors.YELLOW}  ⚡ Searching...{Colors.END}")
        result = search_web(parsed['query'], parsed.get('engine', 'google'))
        print(f"{Colors.GREEN}\n  ✅ {result}{Colors.END}")
    
    elif action == 'time':
        now = datetime.now()
        print(f"{Colors.WHITE}\n  🤖 It's {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}\n{Colors.END}")
    
    elif action == 'lock':
        print(f"{Colors.YELLOW}  ⚡ Locking screen...{Colors.END}")
        run_powershell('rundll32.exe user32.dll,LockWorkStation')
        print(f"{Colors.GREEN}\n  ✅ Screen locked{Colors.END}")
    
    elif action == 'command':
        print(f"{Colors.YELLOW}  ⚡ Executing PowerShell...{Colors.END}")
        result = run_powershell(parsed['command'])
        print(f"{Colors.CYAN}\n  📤 Output:\n{Colors.WHITE}  {result or '(no output)'}{Colors.END}")
    
    elif action == 'unknown':
        print(f"{Colors.WHITE}\n  🤖 I don't understand \"{parsed['input']}\". Say \"help\" for commands.{Colors.END}")
    
    return True

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    banner()
    
    # Test Windows Speech Recognition
    print(f"{Colors.CYAN}  Testing Windows Speech Recognition...{Colors.END}")
    test_result = run_powershell('Add-Type -AssemblyName System.Speech; Write-Output "OK"')
    if 'OK' in test_result:
        print(f"{Colors.GREEN}  ✅ Windows Speech Recognition available!{Colors.END}\n")
        voice_available = True
    else:
        print(f"{Colors.YELLOW}  ⚠️  Voice may not work. You can still type commands.{Colors.END}\n")
        voice_available = False
    
    running = True
    
    while running:
        try:
            user_input = input(f"{Colors.GREEN}\n  [ENTER=🎤 Voice | Type command]: {Colors.END}").strip()
            
            if user_input == '' and voice_available:
                # Voice input
                voice_text = listen_windows_native(timeout=10)
                if voice_text:
                    print(f"{Colors.MAGENTA}\n  🎤 You said: \"{voice_text}\"{Colors.END}")
                    parsed = parse_command(voice_text)
                    running = execute(parsed)
            elif user_input:
                # Text input
                parsed = parse_command(user_input)
                running = execute(parsed)
                
        except KeyboardInterrupt:
            print(f"{Colors.WHITE}\n  🤖 Goodbye! 👋\n{Colors.END}")
            break
        except Exception as e:
            print(f"{Colors.RED}\n  ❌ Error: {e}{Colors.END}")

if __name__ == '__main__':
    main()
