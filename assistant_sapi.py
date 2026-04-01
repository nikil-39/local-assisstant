"""
🎤 VOICE ASSISTANT - WINDOWS SAPI IMPROVED

Uses Windows Speech Recognition with better configuration.
NO pip installs needed!

USAGE:
    python assistant_sapi.py
"""

import subprocess
import os
import sys
from datetime import datetime

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
║   🎤 VOICE ASSISTANT - WINDOWS SAPI (Improved!)                      ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║   No pip installs needed! Uses Windows built-in speech.              ║
║                                                                       ║
║   TIPS: Speak SLOWLY and CLEARLY                                     ║
║   Say: "OPEN OUTLOOK" (not "openoutlook")                            ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    {C.END}""")

# ═══════════════════════════════════════════════════════════════════════════
# 🎤 Improved Windows Speech Recognition
# ═══════════════════════════════════════════════════════════════════════════

def listen_with_grammar(timeout=10):
    """
    Uses Windows SAPI with a constrained grammar for MUCH better accuracy.
    Instead of free dictation, we define expected commands.
    """
    
    print(f"{C.RED}{C.BOLD}\n  🔴 LISTENING... (speak clearly, e.g., 'OPEN OUTLOOK'){C.END}\n")
    
    # PowerShell script with constrained grammar choices
    ps_script = f'''
Add-Type -AssemblyName System.Speech

$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$recognizer.SetInputToDefaultAudioDevice()

# Build a grammar with specific commands (MUCH more accurate than dictation!)
$grammarBuilder = New-Object System.Speech.Recognition.GrammarBuilder

# Create choices for each command type
$openChoices = New-Object System.Speech.Recognition.Choices
$openChoices.Add(@("open", "launch", "start", "run"))

$appChoices = New-Object System.Speech.Recognition.Choices  
$appChoices.Add(@("outlook", "chrome", "teams", "excel", "word", "notepad", "calculator", "browser", "edge", "firefox", "spotify", "discord", "slack", "terminal", "settings", "explorer", "code", "jira", "files", "mail", "email"))

$searchChoices = New-Object System.Speech.Recognition.Choices
$searchChoices.Add(@("search", "google", "youtube", "find"))

$systemChoices = New-Object System.Speech.Recognition.Choices
$systemChoices.Add(@("time", "date", "lock", "help", "exit", "quit", "bye"))

# Build patterns
$openPattern = New-Object System.Speech.Recognition.GrammarBuilder($openChoices)
$openPattern.Append($appChoices)

$searchPattern = New-Object System.Speech.Recognition.GrammarBuilder($searchChoices)
# Allow any word after search
$searchPattern.AppendDictation()

$systemPattern = New-Object System.Speech.Recognition.GrammarBuilder($systemChoices)

# Combine all patterns
$allChoices = New-Object System.Speech.Recognition.Choices
$allChoices.Add($openPattern)
$allChoices.Add($searchPattern)
$allChoices.Add($systemPattern)

$finalGrammar = New-Object System.Speech.Recognition.Grammar($allChoices)
$recognizer.LoadGrammar($finalGrammar)

# Also load dictation as fallback
$dictGrammar = New-Object System.Speech.Recognition.DictationGrammar
$recognizer.LoadGrammar($dictGrammar)

$recognizer.InitialSilenceTimeout = [TimeSpan]::FromSeconds({timeout})
$recognizer.EndSilenceTimeout = [TimeSpan]::FromSeconds(2)
$recognizer.BabbleTimeout = [TimeSpan]::FromSeconds({timeout})

try {{
    $result = $recognizer.Recognize()
    if ($result -and $result.Text) {{
        Write-Output "TEXT:$($result.Text)"
        Write-Output "CONF:$([math]::Round($result.Confidence * 100))"
    }} else {{
        Write-Output "NONE"
    }}
}} catch {{
    Write-Output "ERROR:$($_.Exception.Message)"
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
        
        output = result.stdout.strip()
        
        if output.startswith('TEXT:'):
            lines = output.split('\n')
            text = lines[0].replace('TEXT:', '').strip()
            conf = 0
            for line in lines:
                if line.startswith('CONF:'):
                    conf = int(line.replace('CONF:', '').strip())
            
            print(f"{C.CYAN}  Confidence: {conf}%{C.END}")
            return text
            
        elif output == 'NONE':
            print(f"{C.YELLOW}  ⏰ No speech detected{C.END}")
            return None
        elif output.startswith('ERROR:'):
            print(f"{C.RED}  ❌ {output.replace('ERROR:', '')}{C.END}")
            return None
        else:
            return None
            
    except subprocess.TimeoutExpired:
        print(f"{C.YELLOW}  ⏰ Timeout{C.END}")
        return None
    except Exception as e:
        print(f"{C.RED}  ❌ Error: {e}{C.END}")
        return None


def listen_simple(timeout=8):
    """Simpler dictation-based recognition"""
    
    print(f"{C.RED}{C.BOLD}\n  🔴 LISTENING... (speak now){C.END}\n")
    
    ps_script = f'''
Add-Type -AssemblyName System.Speech
$r = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$r.SetInputToDefaultAudioDevice()
$r.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
$r.InitialSilenceTimeout = [TimeSpan]::FromSeconds({timeout})
$r.EndSilenceTimeout = [TimeSpan]::FromSeconds(1.5)
try {{
    $result = $r.Recognize()
    if ($result) {{ 
        Write-Output $result.Text
        Write-Output "---"
        Write-Output ([math]::Round($result.Confidence * 100))
    }}
}} catch {{}} finally {{ $r.Dispose() }}
'''
    
    try:
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True, text=True, timeout=timeout + 5
        )
        
        output = result.stdout.strip()
        if output and '---' in output:
            parts = output.split('---')
            text = parts[0].strip()
            conf = int(parts[1].strip()) if len(parts) > 1 else 0
            print(f"{C.CYAN}  Confidence: {conf}%{C.END}")
            return text
        return None
            
    except:
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
    for app_key in APP_MAP:
        if app_key in key or key in app_key:
            run_ps(APP_MAP[app_key])
            return f"Opening {app_key}..."
    run_ps(f'Start-Process "{name}"')
    return f"Trying to open {name}..."

def search_web(query, engine='google'):
    engines = {
        'google': 'https://www.google.com/search?q=',
        'youtube': 'https://www.youtube.com/results?search_query=',
    }
    url = engines.get(engine, engines['google']) + query.replace(' ', '+')
    run_ps(f'Start-Process "{url}"')
    return f'Searching "{query}"...'

# ═══════════════════════════════════════════════════════════════════════════
# 🧠 Command Parser (Fuzzy matching for poor recognition)
# ═══════════════════════════════════════════════════════════════════════════

def fuzzy_match(text, targets):
    """Find best matching target even with typos"""
    text = text.lower()
    for target in targets:
        if target in text or text in target:
            return target
        # Check if most letters match
        if len(text) > 3 and len(target) > 3:
            matches = sum(1 for c in text if c in target)
            if matches / len(text) > 0.6:
                return target
    return None

def parse(text):
    import re
    t = text.lower().strip()
    
    # Exit
    if any(w in t for w in ['exit', 'quit', 'bye', 'goodbye', 'stop', 'close']):
        return {'action': 'exit'}
    
    # Help  
    if 'help' in t:
        return {'action': 'help'}
    
    # Time
    if any(w in t for w in ['time', 'date', 'clock']):
        return {'action': 'time'}
    
    # Lock
    if 'lock' in t:
        return {'action': 'lock'}
    
    # Open patterns
    m = re.match(r'^(open|launch|start|run|the)\s*(.+)$', t)
    if m:
        app = m.group(2).strip()
        matched = fuzzy_match(app, APP_MAP.keys())
        if matched:
            return {'action': 'open', 'app': matched}
        return {'action': 'open', 'app': app}
    
    # Just app name
    matched = fuzzy_match(t, APP_MAP.keys())
    if matched:
        return {'action': 'open', 'app': matched}
    
    # Search
    m = re.match(r'^(search|google|youtube|find)\s*(.*)$', t)
    if m:
        engine = 'google' if m.group(1) in ['search', 'find', 'google'] else 'youtube'
        query = m.group(2).strip() if m.group(2) else 'test'
        return {'action': 'search', 'query': query, 'engine': engine}
    
    return {'action': 'unknown', 'input': text}

# ═══════════════════════════════════════════════════════════════════════════
# 🤖 Execute Commands
# ═══════════════════════════════════════════════════════════════════════════

def show_help():
    print(f"""{C.CYAN}
  ╔═══════════════════════════════════════════════════════════════════╗
  ║  🎤 SAY THESE COMMANDS (speak slowly & clearly):                  ║
  ╠═══════════════════════════════════════════════════════════════════╣
  ║  "OPEN OUTLOOK"       - Opens Outlook                             ║
  ║  "OPEN CHROME"        - Opens Chrome                              ║
  ║  "OPEN TEAMS"         - Opens Teams                               ║
  ║  "OPEN NOTEPAD"       - Opens Notepad                             ║
  ║  "OPEN CALCULATOR"    - Opens Calculator                          ║
  ║  "TIME"               - Shows time                                ║
  ║  "LOCK"               - Lock screen                               ║
  ║  "EXIT"               - Close assistant                           ║
  ╚═══════════════════════════════════════════════════════════════════╝
  
  TIP: Speak SLOWLY with pauses between words!
  Say "OPEN" ... pause ... "OUTLOOK" not "openoutlook"
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
        print(f"{C.WHITE}\n  🤖 Heard: \"{parsed['input']}\"\n     Didn't understand. Try: \"OPEN OUTLOOK\"{C.END}")
    
    return True

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    banner()
    
    print(f"{C.CYAN}  Testing speech engine...{C.END}")
    test = run_ps('Add-Type -AssemblyName System.Speech; Write-Output OK')
    if 'OK' in test:
        print(f"{C.GREEN}  ✅ Ready!\n{C.END}")
    else:
        print(f"{C.RED}  ❌ Speech not available{C.END}")
        return
    
    print(f"{C.YELLOW}  💡 TIP: Speak SLOWLY and CLEARLY for best results!{C.END}")
    print(f"{C.YELLOW}     Say: \"OPEN\" ... pause ... \"OUTLOOK\"{C.END}\n")
    
    running = True
    
    while running:
        try:
            print(f"{C.GREEN}\n  [Press ENTER for 🎤 Voice | Or type a command]{C.END}")
            user_input = input(f"{C.GREEN}  > {C.END}")
            
            if user_input.strip() == '':
                text = listen_simple()
                if text:
                    print(f"{C.MAGENTA}\n  🎤 Heard: \"{text}\"{C.END}")
                    parsed = parse(text)
                    running = execute(parsed)
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
