"""
🎤 VOICE ASSISTANT + BOSCH LLM FARM

Uses:
- Windows Built-in Speech Recognition (no external tools!)
- Bosch LLM Farm for intelligent command parsing

This version uses YOUR company's LLM Farm to understand complex commands!

SETUP:
    Set environment variable: GENAIPLATFORM_FARM_SUBSCRIPTION_KEY=your-key

USAGE:
    python assistant_llm.py
"""

import subprocess
import os
import sys
from datetime import datetime
import json
import httpx

# ═══════════════════════════════════════════════════════════════════════════
# 🔧 Configuration - Bosch LLM Farm (same as your jira_summarization)
# ═══════════════════════════════════════════════════════════════════════════

LLM_CONFIG = {
    "api_key": os.getenv("GENAIPLATFORM_FARM_SUBSCRIPTION_KEY"),  # Set env var or use .env file
    "base_url": "https://aoai-farm.bosch-temp.com/api/openai/deployments/askbosch-prod-farm-openai-gpt-4o-mini-2024-07-18",
    "model": "gpt-4o-mini",
    "proxy": "http://127.0.0.1:3128"
}

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
║   🎤 VOICE ASSISTANT + BOSCH LLM FARM                                ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║   Windows Speech Recognition + GPT-4o-mini for smart commands!       ║
║                                                                       ║
║   Press ENTER to speak • Type commands • Say "exit" to quit          ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    {Colors.END}""")

# ═══════════════════════════════════════════════════════════════════════════
# 🧠 Bosch LLM Farm Client
# ═══════════════════════════════════════════════════════════════════════════

class BoschLLM:
    def __init__(self):
        self.api_key = LLM_CONFIG["api_key"]
        self.base_url = LLM_CONFIG["base_url"]
        self.available = False
        
        # Remove proxy env vars temporarily (same as your jira code)
        self.proxy_backup = {}
        for var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
            if var in os.environ:
                self.proxy_backup[var] = os.environ[var]
                del os.environ[var]
        
        self.client = httpx.Client(
            proxy=LLM_CONFIG["proxy"],
            verify=False,
            timeout=30.0
        )
        
        # Test connection
        try:
            self._test_connection()
            self.available = True
            print(f"{Colors.GREEN}  ✅ Bosch LLM Farm connected!{Colors.END}")
        except Exception as e:
            print(f"{Colors.YELLOW}  ⚠️  LLM Farm not available: {e}")
            print(f"     Using simple pattern matching instead.{Colors.END}")
    
    def _test_connection(self):
        # Simple test
        response = self.chat("Say OK", max_tokens=10)
        if not response:
            raise Exception("No response from LLM Farm")
    
    def chat(self, prompt, max_tokens=200):
        try:
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "genaiplatform-farm-subscription-key": self.api_key,
                },
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.1
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return None
    
    def parse_command(self, user_input):
        """Use LLM to understand the command and return structured action"""
        
        prompt = f'''You are a command parser for a local assistant. Parse the user's request and return ONLY a JSON object.

Available actions:
- {{"action": "open", "app": "outlook/chrome/teams/vscode/excel/word/calculator/notepad/jira"}}
- {{"action": "search", "query": "search terms", "engine": "google/youtube/github"}}
- {{"action": "url", "target": "website.com"}}
- {{"action": "time"}}
- {{"action": "lock"}}
- {{"action": "exit"}}
- {{"action": "help"}}
- {{"action": "unknown", "input": "original text"}}

User said: "{user_input}"

Return ONLY the JSON object, no explanation:'''

        response = self.chat(prompt, max_tokens=100)
        
        if response:
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{[^}]+\}', response)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        # Fallback to simple parsing
        return None
    
    def __del__(self):
        # Restore proxy vars
        for var, value in self.proxy_backup.items():
            os.environ[var] = value

# ═══════════════════════════════════════════════════════════════════════════
# 🎤 Windows Speech Recognition
# ═══════════════════════════════════════════════════════════════════════════

def listen_windows_native(timeout=10):
    print(f"{Colors.RED}{Colors.BOLD}\n  🔴 LISTENING... (speak now){Colors.END}\n")
    
    ps_script = f'''
Add-Type -AssemblyName System.Speech
$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$recognizer.SetInputToDefaultAudioDevice()
$grammar = New-Object System.Speech.Recognition.DictationGrammar
$recognizer.LoadGrammar($grammar)
$recognizer.InitialSilenceTimeout = [TimeSpan]::FromSeconds({timeout})
$recognizer.EndSilenceTimeout = [TimeSpan]::FromSeconds(2)
try {{
    $result = $recognizer.Recognize()
    if ($result) {{ Write-Output $result.Text }}
}} catch {{}}
finally {{ $recognizer.Dispose() }}
'''
    
    try:
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True, text=True, timeout=timeout + 5
        )
        text = result.stdout.strip()
        return text if text else None
    except:
        return None

# ═══════════════════════════════════════════════════════════════════════════
# 🛠️ Command Executor
# ═══════════════════════════════════════════════════════════════════════════

def run_ps(cmd):
    try:
        r = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True, timeout=30)
        return r.stdout.strip()
    except:
        return ""

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
    'explorer': 'Start-Process explorer',
    'terminal': 'Start-Process wt',
    'settings': 'Start-Process ms-settings:',
    'vscode': 'Start-Process code',
    'vs code': 'Start-Process code',
    'code': 'Start-Process code',
    'spotify': 'Start-Process spotify',
    'discord': 'Start-Process discord',
    'jira': 'Start-Process "https://rb-tracker.bosch.com"',
}

def simple_parse(text):
    """Fallback simple parser"""
    import re
    text = text.lower().strip()
    
    if any(w in text for w in ['exit', 'quit', 'bye']):
        return {'action': 'exit'}
    if text in ['help', 'commands']:
        return {'action': 'help'}
    
    m = re.match(r'^(open|launch|start)\s+(.+)$', text)
    if m:
        return {'action': 'open', 'app': m.group(2)}
    
    m = re.match(r'^(search|google|youtube|github)\s+(.+)$', text)
    if m:
        engine = 'google' if m.group(1) in ['search'] else m.group(1)
        return {'action': 'search', 'query': m.group(2), 'engine': engine}
    
    if 'time' in text or 'date' in text:
        return {'action': 'time'}
    if 'lock' in text:
        return {'action': 'lock'}
    
    return {'action': 'unknown', 'input': text}

def execute(parsed):
    action = parsed.get('action')
    
    if action == 'exit':
        print(f"{Colors.WHITE}\n  🤖 Goodbye! 👋\n{Colors.END}")
        return False
    
    elif action == 'help':
        print(f"""{Colors.CYAN}
  Commands: open [app], search [query], youtube [query], go to [website]
  Apps: outlook, chrome, teams, vscode, excel, word, jira, calculator
  System: time, lock, exit{Colors.END}""")
    
    elif action == 'open':
        app = parsed.get('app', '').lower()
        cmd = APP_MAP.get(app)
        if cmd:
            run_ps(cmd)
            print(f"{Colors.GREEN}  ✅ Opening {app}...{Colors.END}")
        else:
            run_ps(f'Start-Process "{app}"')
            print(f"{Colors.GREEN}  ✅ Trying to open {app}...{Colors.END}")
    
    elif action == 'url':
        url = parsed.get('target', '')
        if not url.startswith('http'):
            url = 'https://' + url
        run_ps(f'Start-Process "{url}"')
        print(f"{Colors.GREEN}  ✅ Opening {url}...{Colors.END}")
    
    elif action == 'search':
        query = parsed.get('query', '')
        engine = parsed.get('engine', 'google')
        engines = {
            'google': 'https://www.google.com/search?q=',
            'youtube': 'https://www.youtube.com/results?search_query=',
            'github': 'https://github.com/search?q=',
        }
        url = engines.get(engine, engines['google']) + query.replace(' ', '+')
        run_ps(f'Start-Process "{url}"')
        print(f"{Colors.GREEN}  ✅ Searching '{query}' on {engine}...{Colors.END}")
    
    elif action == 'time':
        now = datetime.now()
        print(f"{Colors.WHITE}\n  🤖 {now.strftime('%I:%M %p, %A %B %d, %Y')}\n{Colors.END}")
    
    elif action == 'lock':
        run_ps('rundll32.exe user32.dll,LockWorkStation')
        print(f"{Colors.GREEN}  ✅ Locking screen...{Colors.END}")
    
    else:
        print(f"{Colors.WHITE}\n  🤖 I don't understand. Try: open outlook, search cats, youtube music{Colors.END}")
    
    return True

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    os.system('cls')
    banner()
    
    # Disable SSL warnings
    import warnings
    warnings.filterwarnings('ignore')
    
    # Initialize LLM
    print(f"{Colors.CYAN}  Connecting to Bosch LLM Farm...{Colors.END}")
    llm = BoschLLM()
    
    # Check voice
    print(f"{Colors.CYAN}  Testing speech recognition...{Colors.END}")
    test = run_ps('Add-Type -AssemblyName System.Speech; Write-Output OK')
    voice_ok = 'OK' in test
    if voice_ok:
        print(f"{Colors.GREEN}  ✅ Voice ready!\n{Colors.END}")
    else:
        print(f"{Colors.YELLOW}  ⚠️  Voice may not work\n{Colors.END}")
    
    running = True
    while running:
        try:
            inp = input(f"{Colors.GREEN}\n  [ENTER=🎤 | Type]: {Colors.END}").strip()
            
            if inp == '' and voice_ok:
                text = listen_windows_native()
                if text:
                    print(f"{Colors.MAGENTA}  🎤 \"{text}\"{Colors.END}")
                    # Try LLM parsing first
                    if llm.available:
                        print(f"{Colors.YELLOW}  🧠 Parsing with LLM...{Colors.END}")
                        parsed = llm.parse_command(text)
                    else:
                        parsed = None
                    # Fallback
                    if not parsed:
                        parsed = simple_parse(text)
                    running = execute(parsed)
            elif inp:
                if llm.available:
                    parsed = llm.parse_command(inp)
                else:
                    parsed = None
                if not parsed:
                    parsed = simple_parse(inp)
                running = execute(parsed)
                
        except KeyboardInterrupt:
            print(f"\n  👋 Bye!")
            break
        except Exception as e:
            print(f"{Colors.RED}  ❌ {e}{Colors.END}")

if __name__ == '__main__':
    main()
