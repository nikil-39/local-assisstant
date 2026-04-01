/**
 * 🤖 LOCAL COMMAND ASSISTANT
 * 
 * An always-on local assistant that executes system commands.
 * Inspired by Claude Code's PowerShellTool and BashTool patterns.
 * 
 * NO API REQUIRED - runs completely offline!
 * 
 * Commands:
 *   - "open outlook" / "open chrome" / "open [app]"
 *   - "search [query]" - opens browser search
 *   - "type [text]" - types text (for automation)
 *   - "run [command]" - execute any PowerShell command
 *   - "help" - show all commands
 *   - "exit" - quit assistant
 */

import { spawn, exec } from 'child_process';
import * as readline from 'readline';
import chalk from 'chalk';

// ═══════════════════════════════════════════════════════════════════════════
// 🎨 Terminal UI
// ═══════════════════════════════════════════════════════════════════════════

const UI = {
  banner() {
    console.log(chalk.cyan(`
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   🤖 LOCAL COMMAND ASSISTANT                                          ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║   Always-on • Offline • No API Required                               ║
║                                                                       ║
║   Say "help" for commands or just tell me what to do!                 ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    `));
  },

  thinking() {
    process.stdout.write(chalk.yellow('  🔄 Processing...'));
  },

  success(msg) {
    console.log(chalk.green(`\n  ✅ ${msg}`));
  },

  error(msg) {
    console.log(chalk.red(`\n  ❌ ${msg}`));
  },

  info(msg) {
    console.log(chalk.cyan(`  ℹ️  ${msg}`));
  },

  response(msg) {
    console.log(chalk.white(`\n  🤖 ${msg}\n`));
  }
};

// ═══════════════════════════════════════════════════════════════════════════
// 🛠️ PowerShellTool (Inspired by Claude Code)
// ═══════════════════════════════════════════════════════════════════════════

class PowerShellTool {
  async execute(command) {
    return new Promise((resolve, reject) => {
      exec(`powershell -Command "${command}"`, (error, stdout, stderr) => {
        if (error) {
          reject(stderr || error.message);
        } else {
          resolve(stdout.trim());
        }
      });
    });
  }

  async openApp(appName) {
    // Map friendly names to actual commands
    const appMap = {
      // Microsoft Office
      'outlook': 'Start-Process outlook',
      'word': 'Start-Process winword',
      'excel': 'Start-Process excel',
      'powerpoint': 'Start-Process powerpnt',
      'teams': 'Start-Process ms-teams:',
      'onenote': 'Start-Process onenote',
      
      // Browsers
      'chrome': 'Start-Process chrome',
      'firefox': 'Start-Process firefox',
      'edge': 'Start-Process msedge',
      'brave': 'Start-Process brave',
      
      // System
      'notepad': 'Start-Process notepad',
      'calculator': 'Start-Process calc',
      'explorer': 'Start-Process explorer',
      'terminal': 'Start-Process wt',
      'cmd': 'Start-Process cmd',
      'powershell': 'Start-Process powershell',
      'settings': 'Start-Process ms-settings:',
      'control panel': 'Start-Process control',
      'task manager': 'Start-Process taskmgr',
      
      // Dev Tools
      'vscode': 'Start-Process code',
      'vs code': 'Start-Process code',
      'visual studio code': 'Start-Process code',
      'git bash': 'Start-Process "C:\\Program Files\\Git\\git-bash.exe"',
      
      // Media
      'spotify': 'Start-Process spotify',
      'vlc': 'Start-Process vlc',
      
      // Communication
      'discord': 'Start-Process discord',
      'slack': 'Start-Process slack',
      'zoom': 'Start-Process zoom',
      'whatsapp': 'Start-Process WhatsApp:',
      'telegram': 'Start-Process Telegram',
      
      // Others
      'steam': 'Start-Process steam',
      'obs': 'Start-Process "obs64"',
    };

    const key = appName.toLowerCase().trim();
    const command = appMap[key];

    if (command) {
      await this.execute(command);
      return `Opening ${appName}...`;
    } else {
      // Try to open it directly
      try {
        await this.execute(`Start-Process "${appName}"`);
        return `Trying to open ${appName}...`;
      } catch {
        throw new Error(`Unknown app: ${appName}. Try "run Start-Process [app]" for custom apps.`);
      }
    }
  }

  async searchWeb(query, engine = 'google') {
    const engines = {
      'google': `https://www.google.com/search?q=`,
      'bing': `https://www.bing.com/search?q=`,
      'duckduckgo': `https://duckduckgo.com/?q=`,
      'youtube': `https://www.youtube.com/results?search_query=`,
      'github': `https://github.com/search?q=`,
    };

    const baseUrl = engines[engine] || engines['google'];
    const url = `${baseUrl}${encodeURIComponent(query)}`;
    await this.execute(`Start-Process "${url}"`);
    return `Searching for "${query}" on ${engine}...`;
  }

  async openUrl(url) {
    if (!url.startsWith('http')) {
      url = 'https://' + url;
    }
    await this.execute(`Start-Process "${url}"`);
    return `Opening ${url}...`;
  }

  async getSystemInfo() {
    const info = await this.execute(`
      $os = Get-CimInstance Win32_OperatingSystem
      $cpu = Get-CimInstance Win32_Processor
      $mem = [math]::Round($os.FreePhysicalMemory/1MB, 2)
      Write-Output "OS: $($os.Caption)"
      Write-Output "CPU: $($cpu.Name)"
      Write-Output "Free RAM: $mem GB"
    `);
    return info;
  }

  async listProcesses() {
    return await this.execute('Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet | Format-Table');
  }

  async killProcess(name) {
    await this.execute(`Stop-Process -Name "${name}" -Force`);
    return `Killed process: ${name}`;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// 🧠 Command Parser (Simple NLP)
// ═══════════════════════════════════════════════════════════════════════════

class CommandParser {
  constructor(powerShell) {
    this.ps = powerShell;
  }

  async parse(input) {
    const text = input.toLowerCase().trim();
    
    // Exit commands
    if (['exit', 'quit', 'bye', 'goodbye', 'close'].includes(text)) {
      return { action: 'exit' };
    }

    // Help
    if (['help', '?', 'commands', 'what can you do'].includes(text)) {
      return { action: 'help' };
    }

    // Open app: "open outlook", "launch chrome", "start notepad"
    const openMatch = text.match(/^(open|launch|start|run)\s+(.+)$/i);
    if (openMatch) {
      const target = openMatch[2];
      
      // Check if it's a URL
      if (target.includes('.com') || target.includes('.org') || target.includes('.io') || target.startsWith('http')) {
        return { action: 'url', target };
      }
      
      // Check if it's a PowerShell command
      if (target.startsWith('powershell') || openMatch[1].toLowerCase() === 'run') {
        return { action: 'command', command: target };
      }
      
      return { action: 'open', app: target };
    }

    // Search: "search how to code", "google react hooks", "youtube funny cats"
    const searchMatch = text.match(/^(search|google|bing|youtube|github)\s+(.+)$/i);
    if (searchMatch) {
      const engine = searchMatch[1].toLowerCase() === 'search' ? 'google' : searchMatch[1].toLowerCase();
      return { action: 'search', query: searchMatch[2], engine };
    }

    // Go to URL: "go to github.com", "navigate to google.com"
    const gotoMatch = text.match(/^(go to|goto|navigate to|visit)\s+(.+)$/i);
    if (gotoMatch) {
      return { action: 'url', target: gotoMatch[2] };
    }

    // System info: "system info", "pc info", "computer status"
    if (text.match(/^(system|pc|computer|cpu|memory|ram)\s*(info|status|stats)?$/i)) {
      return { action: 'sysinfo' };
    }

    // List processes: "show processes", "what's running", "task list"
    if (text.match(/^(show|list|running)\s*(processes|tasks|apps)?$|^(what'?s running|task list)$/i)) {
      return { action: 'processes' };
    }

    // Kill process: "kill chrome", "close spotify", "end process notepad"
    const killMatch = text.match(/^(kill|close|end|stop)\s+(process\s+)?(.+)$/i);
    if (killMatch && !['exit', 'quit', 'bye', 'assistant'].includes(killMatch[3])) {
      return { action: 'kill', process: killMatch[3] };
    }

    // Time: "what time is it", "time", "date"
    if (text.match(/^(what('?s| is) the )?(time|date|day)/i) || text === 'time' || text === 'date') {
      return { action: 'time' };
    }

    // Lock screen
    if (text.match(/^lock\s*(screen|pc|computer)?$/i)) {
      return { action: 'lock' };
    }

    // Sleep/hibernate
    if (text.match(/^(sleep|hibernate)\s*(pc|computer)?$/i)) {
      return { action: 'sleep' };
    }

    // Shutdown
    if (text.match(/^shut\s*down$/i)) {
      return { action: 'shutdown' };
    }

    // Restart
    if (text.match(/^restart$/i)) {
      return { action: 'restart' };
    }

    // Volume control
    const volumeMatch = text.match(/^(mute|unmute|volume\s*(up|down|\d+))/i);
    if (volumeMatch) {
      return { action: 'volume', command: volumeMatch[0] };
    }

    // Screenshot
    if (text.match(/^(screenshot|screen\s*shot|capture\s*screen)/i)) {
      return { action: 'screenshot' };
    }

    // Direct PowerShell command: "ps: Get-Date"
    const psMatch = text.match(/^(ps|powershell|cmd):\s*(.+)$/i);
    if (psMatch) {
      return { action: 'command', command: psMatch[2] };
    }

    // Unknown
    return { action: 'unknown', input: text };
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// 🤖 Assistant
// ═══════════════════════════════════════════════════════════════════════════

class LocalAssistant {
  constructor() {
    this.ps = new PowerShellTool();
    this.parser = new CommandParser(this.ps);
    this.running = true;
  }

  showHelp() {
    console.log(chalk.cyan(`
  ╔═══════════════════════════════════════════════════════════════════╗
  ║  📚 AVAILABLE COMMANDS                                            ║
  ╠═══════════════════════════════════════════════════════════════════╣
  ║                                                                   ║
  ║  🚀 OPEN APPS                                                     ║
  ║     "open outlook"     - Open Microsoft Outlook                   ║
  ║     "open chrome"      - Open Google Chrome                       ║
  ║     "open vscode"      - Open Visual Studio Code                  ║
  ║     "open calculator"  - Open Calculator                          ║
  ║     "open [any app]"   - Try to open any app by name              ║
  ║                                                                   ║
  ║  🔍 SEARCH                                                        ║
  ║     "search [query]"   - Google search                            ║
  ║     "youtube [query]"  - YouTube search                           ║
  ║     "github [query]"   - GitHub search                            ║
  ║                                                                   ║
  ║  🌐 WEB                                                           ║
  ║     "go to github.com" - Open a website                           ║
  ║                                                                   ║
  ║  💻 SYSTEM                                                        ║
  ║     "system info"      - Show PC info                             ║
  ║     "show processes"   - List running processes                   ║
  ║     "kill chrome"      - Kill a process                           ║
  ║     "time" / "date"    - Show current time                        ║
  ║     "lock"             - Lock screen                              ║
  ║     "screenshot"       - Take a screenshot                        ║
  ║                                                                   ║
  ║  ⚡ DIRECT COMMANDS                                                ║
  ║     "ps: [command]"    - Run any PowerShell command               ║
  ║                                                                   ║
  ║  🚪 EXIT                                                          ║
  ║     "exit" / "quit"    - Close assistant                          ║
  ║                                                                   ║
  ╚═══════════════════════════════════════════════════════════════════╝
    `));
  }

  async execute(parsed) {
    try {
      switch (parsed.action) {
        case 'exit':
          this.running = false;
          UI.response('Goodbye! 👋');
          return;

        case 'help':
          this.showHelp();
          return;

        case 'open':
          UI.thinking();
          const openResult = await this.ps.openApp(parsed.app);
          UI.success(openResult);
          return;

        case 'url':
          UI.thinking();
          const urlResult = await this.ps.openUrl(parsed.target);
          UI.success(urlResult);
          return;

        case 'search':
          UI.thinking();
          const searchResult = await this.ps.searchWeb(parsed.query, parsed.engine);
          UI.success(searchResult);
          return;

        case 'sysinfo':
          UI.thinking();
          const sysInfo = await this.ps.getSystemInfo();
          console.log(chalk.cyan('\n  📊 System Info:\n'));
          console.log(chalk.white('  ' + sysInfo.split('\n').join('\n  ')));
          return;

        case 'processes':
          UI.thinking();
          const procs = await this.ps.listProcesses();
          console.log(chalk.cyan('\n  📊 Top Processes:\n'));
          console.log(chalk.white('  ' + procs.split('\n').join('\n  ')));
          return;

        case 'kill':
          UI.thinking();
          const killResult = await this.ps.killProcess(parsed.process);
          UI.success(killResult);
          return;

        case 'time':
          const now = new Date();
          UI.response(`It's ${now.toLocaleTimeString()} on ${now.toLocaleDateString()}`);
          return;

        case 'lock':
          UI.thinking();
          await this.ps.execute('rundll32.exe user32.dll,LockWorkStation');
          UI.success('Locking screen...');
          return;

        case 'sleep':
          UI.response('Putting computer to sleep...');
          await this.ps.execute('rundll32.exe powrprof.dll,SetSuspendState 0,1,0');
          return;

        case 'shutdown':
          UI.response('⚠️  Shutting down in 10 seconds... (run "shutdown /a" to cancel)');
          await this.ps.execute('shutdown /s /t 10');
          return;

        case 'restart':
          UI.response('⚠️  Restarting in 10 seconds... (run "shutdown /a" to cancel)');
          await this.ps.execute('shutdown /r /t 10');
          return;

        case 'screenshot':
          UI.thinking();
          const screenshotPath = `$env:USERPROFILE\\Desktop\\screenshot_${Date.now()}.png`;
          await this.ps.execute(`
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.Screen]::PrimaryScreen | ForEach-Object {
              $bitmap = New-Object System.Drawing.Bitmap($_.Bounds.Width, $_.Bounds.Height)
              $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
              $graphics.CopyFromScreen($_.Bounds.Location, [System.Drawing.Point]::Empty, $_.Bounds.Size)
              $bitmap.Save("${screenshotPath}")
            }
          `);
          UI.success(`Screenshot saved to Desktop!`);
          return;

        case 'command':
          UI.thinking();
          try {
            const result = await this.ps.execute(parsed.command);
            console.log(chalk.cyan('\n  📤 Output:\n'));
            console.log(chalk.white('  ' + (result || '(no output)').split('\n').join('\n  ')));
          } catch (err) {
            UI.error(err);
          }
          return;

        case 'unknown':
          UI.response(`I don't understand "${parsed.input}". Say "help" for available commands.`);
          // Suggest similar commands
          const suggestions = this.getSuggestions(parsed.input);
          if (suggestions.length > 0) {
            UI.info(`Did you mean: ${suggestions.join(', ')}?`);
          }
          return;

        default:
          UI.error('Unknown action');
      }
    } catch (err) {
      UI.error(err.message || err);
    }
  }

  getSuggestions(input) {
    const commands = ['open', 'search', 'youtube', 'github', 'go to', 'system info', 'processes', 'time', 'help'];
    return commands.filter(cmd => 
      cmd.includes(input.toLowerCase()) || 
      input.toLowerCase().includes(cmd.split(' ')[0])
    ).slice(0, 3);
  }

  async run() {
    UI.banner();

    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    });

    const prompt = () => {
      rl.question(chalk.green('\n  You: '), async (input) => {
        if (!input.trim()) {
          if (this.running) prompt();
          return;
        }

        const parsed = await this.parser.parse(input);
        await this.execute(parsed);

        if (this.running) {
          prompt();
        } else {
          rl.close();
          process.exit(0);
        }
      });
    };

    prompt();
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// 🚀 START
// ═══════════════════════════════════════════════════════════════════════════

const assistant = new LocalAssistant();
assistant.run();
