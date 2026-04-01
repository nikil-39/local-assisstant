/**
 * 🎤 VOICE-ENABLED LOCAL ASSISTANT
 * 
 * Press SPACE to start recording, release to stop.
 * Uses OpenAI Whisper API for speech-to-text.
 * 
 * SETUP:
 *   1. Install SoX: https://sourceforge.net/projects/sox/
 *   2. Add SoX to PATH
 *   3. Set OPENAI_API_KEY in .env file
 *   4. npm run voice
 */

import { spawn, exec } from 'child_process';
import * as readline from 'readline';
import chalk from 'chalk';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import OpenAI from 'openai';
import 'dotenv/config';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ═══════════════════════════════════════════════════════════════════════════
// 🔧 Configuration
// ═══════════════════════════════════════════════════════════════════════════

const CONFIG = {
  // Recording settings
  sampleRate: 16000,
  channels: 1,
  audioFile: path.join(__dirname, 'temp_recording.wav'),
  
  // Whisper settings
  whisperModel: 'whisper-1',
  
  // Voice activation
  useVoiceActivation: false, // Set to true for always-listening mode
  silenceThreshold: 0.01,
  silenceDuration: 1500, // ms of silence to stop recording
};

// ═══════════════════════════════════════════════════════════════════════════
// 🎨 Terminal UI
// ═══════════════════════════════════════════════════════════════════════════

const UI = {
  banner() {
    console.log(chalk.cyan(`
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   🎤 VOICE-ENABLED LOCAL ASSISTANT                                    ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║   Press ENTER to start recording • Press ENTER again to stop         ║
║   Type commands directly • Say "exit" or type "exit" to quit         ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    `));
  },

  recording() {
    console.log(chalk.red.bold('\n  🔴 RECORDING... (Press ENTER to stop)\n'));
  },

  processing() {
    process.stdout.write(chalk.yellow('  🔄 Transcribing...'));
  },

  transcribed(text) {
    console.log(chalk.magenta(`\n  🎤 You said: "${text}"`));
  },

  thinking() {
    process.stdout.write(chalk.yellow('  ⚡ Executing...'));
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
  },

  prompt() {
    process.stdout.write(chalk.green('\n  [ENTER=🎤 Voice | Type command]: '));
  }
};

// ═══════════════════════════════════════════════════════════════════════════
// 🎤 Voice Recorder using SoX
// ═══════════════════════════════════════════════════════════════════════════

class VoiceRecorder {
  constructor() {
    this.recording = false;
    this.process = null;
  }

  async checkSoX() {
    return new Promise((resolve) => {
      exec('sox --version', (error) => {
        resolve(!error);
      });
    });
  }

  start() {
    return new Promise((resolve, reject) => {
      this.recording = true;
      
      // Use SoX to record audio
      // Windows: rec command from SoX
      this.process = spawn('rec', [
        '-q',                    // Quiet
        '-r', CONFIG.sampleRate.toString(), // Sample rate
        '-c', CONFIG.channels.toString(),   // Channels
        '-b', '16',              // Bits
        CONFIG.audioFile,        // Output file
      ], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      this.process.on('error', (err) => {
        this.recording = false;
        reject(new Error(`Failed to start recording. Is SoX installed? Error: ${err.message}`));
      });

      resolve();
    });
  }

  stop() {
    return new Promise((resolve) => {
      if (this.process) {
        this.recording = false;
        
        // Send quit signal to SoX
        this.process.kill('SIGTERM');
        
        // Wait a bit for file to be written
        setTimeout(() => {
          resolve(CONFIG.audioFile);
        }, 500);
      } else {
        resolve(null);
      }
    });
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// 🔊 Speech-to-Text using OpenAI Whisper
// ═══════════════════════════════════════════════════════════════════════════

class WhisperTranscriber {
  constructor() {
    if (!process.env.OPENAI_API_KEY) {
      throw new Error('OPENAI_API_KEY not found in environment. Create a .env file with your key.');
    }
    this.openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY
    });
  }

  async transcribe(audioFile) {
    try {
      const response = await this.openai.audio.transcriptions.create({
        file: fs.createReadStream(audioFile),
        model: CONFIG.whisperModel,
        language: 'en',
      });
      
      // Clean up temp file
      try { fs.unlinkSync(audioFile); } catch {}
      
      return response.text;
    } catch (error) {
      throw new Error(`Transcription failed: ${error.message}`);
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// 🛠️ PowerShellTool (Same as before)
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
    const appMap = {
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
    };

    const key = appName.toLowerCase().trim();
    const command = appMap[key];

    if (command) {
      await this.execute(command);
      return `Opening ${appName}...`;
    } else {
      try {
        await this.execute(`Start-Process "${appName}"`);
        return `Trying to open ${appName}...`;
      } catch {
        throw new Error(`Unknown app: ${appName}`);
      }
    }
  }

  async searchWeb(query, engine = 'google') {
    const engines = {
      'google': `https://www.google.com/search?q=`,
      'youtube': `https://www.youtube.com/results?search_query=`,
      'github': `https://github.com/search?q=`,
    };
    const baseUrl = engines[engine] || engines['google'];
    const url = `${baseUrl}${encodeURIComponent(query)}`;
    await this.execute(`Start-Process "${url}"`);
    return `Searching for "${query}"...`;
  }

  async openUrl(url) {
    if (!url.startsWith('http')) url = 'https://' + url;
    await this.execute(`Start-Process "${url}"`);
    return `Opening ${url}...`;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// 🧠 Command Parser
// ═══════════════════════════════════════════════════════════════════════════

class CommandParser {
  parse(input) {
    const text = input.toLowerCase().trim();
    
    if (['exit', 'quit', 'bye', 'goodbye', 'stop', 'close assistant'].includes(text)) {
      return { action: 'exit' };
    }

    if (['help', 'what can you do', 'commands'].includes(text)) {
      return { action: 'help' };
    }

    // Open app
    const openMatch = text.match(/^(open|launch|start)\s+(.+)$/i);
    if (openMatch) {
      const target = openMatch[2];
      if (target.includes('.com') || target.includes('.org') || target.startsWith('http')) {
        return { action: 'url', target };
      }
      return { action: 'open', app: target };
    }

    // Search
    const searchMatch = text.match(/^(search|google|youtube|github)\s+(.+)$/i);
    if (searchMatch) {
      const engine = searchMatch[1].toLowerCase() === 'search' ? 'google' : searchMatch[1].toLowerCase();
      return { action: 'search', query: searchMatch[2], engine };
    }

    // Go to URL
    const gotoMatch = text.match(/^(go to|goto|navigate to|visit)\s+(.+)$/i);
    if (gotoMatch) {
      return { action: 'url', target: gotoMatch[2] };
    }

    // Time
    if (text.match(/^(what('?s| is) the )?(time|date)/i) || text === 'time') {
      return { action: 'time' };
    }

    // Lock
    if (text.match(/^lock/i)) {
      return { action: 'lock' };
    }

    // PowerShell command
    const psMatch = text.match(/^(run|execute|ps:?)\s+(.+)$/i);
    if (psMatch) {
      return { action: 'command', command: psMatch[2] };
    }

    return { action: 'unknown', input: text };
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// 🤖 Voice Assistant
// ═══════════════════════════════════════════════════════════════════════════

class VoiceAssistant {
  constructor() {
    this.ps = new PowerShellTool();
    this.parser = new CommandParser();
    this.recorder = new VoiceRecorder();
    this.transcriber = null;
    this.running = true;
    this.isRecording = false;
  }

  async init() {
    // Check SoX
    const hasSoX = await this.recorder.checkSoX();
    if (!hasSoX) {
      console.log(chalk.yellow(`
  ⚠️  SoX not found! Voice recording won't work.
  
  To install SoX on Windows:
    1. Download from: https://sourceforge.net/projects/sox/
    2. Install and add to PATH
    3. Restart terminal
  
  You can still type commands manually.
      `));
    }

    // Check OpenAI API key
    try {
      this.transcriber = new WhisperTranscriber();
      UI.info('Whisper API connected ✓');
    } catch (err) {
      console.log(chalk.yellow(`
  ⚠️  ${err.message}
  
  To enable voice:
    1. Create .env file in this folder
    2. Add: OPENAI_API_KEY=sk-your-key-here
    3. Restart the assistant
  
  You can still type commands manually.
      `));
    }
  }

  showHelp() {
    console.log(chalk.cyan(`
  ╔═══════════════════════════════════════════════════════════════════╗
  ║  🎤 VOICE COMMANDS (or type them!)                                ║
  ╠═══════════════════════════════════════════════════════════════════╣
  ║  "Open Outlook"        - Opens Outlook                            ║
  ║  "Open Chrome"         - Opens Chrome                             ║
  ║  "Open VS Code"        - Opens Visual Studio Code                 ║
  ║  "Search [query]"      - Google search                            ║
  ║  "YouTube [query]"     - YouTube search                           ║
  ║  "Go to [website]"     - Open a website                           ║
  ║  "What time is it"     - Show current time                        ║
  ║  "Lock"                - Lock screen                              ║
  ║  "Exit" / "Quit"       - Close assistant                          ║
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

        case 'time':
          const now = new Date();
          UI.response(`It's ${now.toLocaleTimeString()} on ${now.toLocaleDateString()}`);
          return;

        case 'lock':
          UI.thinking();
          await this.ps.execute('rundll32.exe user32.dll,LockWorkStation');
          UI.success('Locking screen...');
          return;

        case 'command':
          UI.thinking();
          const result = await this.ps.execute(parsed.command);
          console.log(chalk.cyan('\n  📤 Output:\n'));
          console.log(chalk.white('  ' + (result || '(no output)').split('\n').join('\n  ')));
          return;

        case 'unknown':
          UI.response(`I don't understand "${parsed.input}". Say "help" for commands.`);
          return;
      }
    } catch (err) {
      UI.error(err.message || err);
    }
  }

  async handleVoiceInput() {
    if (!this.transcriber) {
      UI.error('Voice not available. Type your command instead.');
      return null;
    }

    try {
      UI.recording();
      await this.recorder.start();
      
      // Wait for user to press Enter again
      await new Promise(resolve => {
        const onKeypress = () => {
          process.stdin.removeListener('data', onKeypress);
          resolve();
        };
        process.stdin.once('data', onKeypress);
      });

      const audioFile = await this.recorder.stop();
      
      if (!audioFile || !fs.existsSync(audioFile)) {
        UI.error('No audio recorded');
        return null;
      }

      UI.processing();
      const text = await this.transcriber.transcribe(audioFile);
      UI.transcribed(text);
      
      return text;
    } catch (err) {
      UI.error(`Voice error: ${err.message}`);
      return null;
    }
  }

  async run() {
    UI.banner();
    await this.init();

    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    });

    // Enable raw mode for key detection
    if (process.stdin.isTTY) {
      process.stdin.setRawMode(false);
    }

    const prompt = () => {
      if (!this.running) {
        rl.close();
        process.exit(0);
        return;
      }

      rl.question(chalk.green('\n  [ENTER=🎤 Voice | Type command]: '), async (input) => {
        input = input.trim();

        // Empty input = voice mode
        if (input === '' && this.transcriber) {
          const voiceText = await this.handleVoiceInput();
          if (voiceText) {
            const parsed = this.parser.parse(voiceText);
            await this.execute(parsed);
          }
        } else if (input) {
          // Text input
          const parsed = this.parser.parse(input);
          await this.execute(parsed);
        }

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

console.clear();
const assistant = new VoiceAssistant();
assistant.run().catch(console.error);
