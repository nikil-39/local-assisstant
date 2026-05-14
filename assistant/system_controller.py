"""
System Controller Module - Handles file operations, app launching,
web browsing, system info, volume control, screenshots, and process management.
"""

import os
import re
import json
import shutil
import logging
import platform
import subprocess
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("jarvis.system")


class SystemController:
    """Controls system operations: apps, files, web, volume, screenshots, etc."""

    def __init__(self, commands_config: dict | None = None):
        self.commands_config = commands_config or {}
        self.app_aliases = self.commands_config.get("app_aliases", {})
        self.search_engines = self.commands_config.get("search_engines", {
            "google": "https://www.google.com/search?q=",
            "youtube": "https://www.youtube.com/results?search_query=",
            "github": "https://github.com/search?q=",
            "bing": "https://www.bing.com/search?q=",
        })

    # ── Application Management ──────────────────────────────────────────

    def open_app(self, app_name: str) -> str:
        """Launch an application by name. Tries aliases, then PATH, then Start Menu shortcuts."""
        key = app_name.lower().strip()

        # 1) Check aliases (exact match)
        target = self.app_aliases.get(key)

        # 2) Try fuzzy: remove common words and retry
        if not target:
            for word in ("open", "launch", "start", "run", "the", "application", "app", "please"):
                key = key.replace(word, "").strip()
            target = self.app_aliases.get(key)

        # 3) Try partial match against alias keys
        if not target:
            for alias_key, alias_val in self.app_aliases.items():
                if key in alias_key or alias_key in key:
                    target = alias_val
                    break

        if not target:
            target = key  # fallback: try the raw name

        try:
            if target.endswith(":"):
                # URI scheme (ms-teams:, ms-settings:, WhatsApp:)
                subprocess.Popen(["cmd", "/c", "start", "", target], shell=False)
            elif os.path.isfile(target):
                # Full path to executable
                subprocess.Popen([target], shell=False)
            elif target.startswith("http://") or target.startswith("https://"):
                # URL
                subprocess.Popen(["cmd", "/c", "start", "", target], shell=False)
            else:
                # Try Start-Process which searches PATH and App Paths registry
                result = subprocess.run(
                    ["powershell", "-Command", f'Start-Process "{target}"'],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode != 0:
                    # Last resort: search Start Menu shortcuts
                    return self._open_via_start_menu(app_name, target)
            return f"Opening {app_name}..."
        except Exception as e:
            logger.error(f"Failed to open {app_name}: {e}")
            return self._open_via_start_menu(app_name, target)

    def _open_via_start_menu(self, app_name: str, target: str) -> str:
        """Search Start Menu for a matching shortcut and launch it."""
        try:
            search_name = app_name.lower()
            search_dirs = [
                Path(os.environ.get("ProgramData", "C:\\ProgramData")) / "Microsoft\\Windows\\Start Menu\\Programs",
                Path.home() / "AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs",
            ]
            for search_dir in search_dirs:
                if not search_dir.exists():
                    continue
                for lnk in search_dir.rglob("*.lnk"):
                    lnk_name = lnk.stem.lower()
                    if search_name in lnk_name or lnk_name in search_name:
                        os.startfile(str(lnk))
                        return f"Opening {lnk.stem}..."

            # Nothing found
            return f"Could not find '{app_name}'. Try the exact app name."
        except Exception as e:
            return f"Failed to open {app_name}: {e}"

    def close_app(self, app_name: str) -> str:
        """Close an application by process name."""
        key = app_name.lower().strip()
        target = self.app_aliases.get(key, key)

        # Map common names to process names
        process_map = {
            "chrome": "chrome", "firefox": "firefox", "edge": "msedge",
            "notepad": "notepad", "outlook": "outlook", "teams": "teams",
            "word": "winword", "excel": "excel", "code": "code",
            "spotify": "spotify", "discord": "discord", "slack": "slack",
        }
        proc_name = process_map.get(target, target)

        try:
            subprocess.run(
                ["taskkill", "/IM", f"{proc_name}.exe", "/F"],
                capture_output=True, text=True, timeout=10,
            )
            return f"Closed {app_name}."
        except Exception as e:
            return f"Could not close {app_name}: {e}"

    # ── Web Operations ──────────────────────────────────────────────────

    def web_search(self, query: str, engine: str = "google") -> str:
        """Search the web using a specified search engine."""
        base_url = self.search_engines.get(engine.lower(), self.search_engines["google"])
        url = base_url + query.replace(" ", "+")
        return self.open_url(url, f'Searching "{query}" on {engine}')

    def open_url(self, url: str, message: str | None = None) -> str:
        """Open a URL in the default browser."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            subprocess.Popen(["cmd", "/c", "start", "", url], shell=False)
            return message or f"Opening {url}..."
        except Exception as e:
            return f"Failed to open URL: {e}"

    def open_and_search(self, app: str, query: str) -> str:
        """Open browser app and search."""
        browser_apps = {"chrome", "firefox", "edge", "browser", "brave"}
        if app.lower() in browser_apps:
            return self.web_search(query)
        else:
            self.open_app(app)
            return f"Opened {app}. (Search for '{query}' manually.)"

    # ── File Operations ─────────────────────────────────────────────────

    def create_file(self, name: str, file_type: str = "file") -> str:
        """Create a file or folder on the Desktop."""
        desktop = Path.home() / "Desktop"
        target = desktop / name

        try:
            if file_type in ("folder", "directory"):
                target.mkdir(parents=True, exist_ok=True)
                return f"Folder '{name}' created on Desktop."
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.touch()
                return f"File '{name}' created on Desktop."
        except Exception as e:
            return f"Failed to create {file_type}: {e}"

    def delete_file(self, name: str) -> str:
        """Delete a file or folder from the Desktop."""
        desktop = Path.home() / "Desktop"
        target = desktop / name

        if not target.exists():
            return f"'{name}' not found on Desktop."

        try:
            if target.is_dir():
                shutil.rmtree(target)
                return f"Folder '{name}' deleted."
            else:
                target.unlink()
                return f"File '{name}' deleted."
        except Exception as e:
            return f"Failed to delete: {e}"

    def list_files(self, path_str: str) -> str:
        """List files in a directory."""
        # Expand common folder names
        folder_map = {
            "desktop": Path.home() / "Desktop",
            "documents": Path.home() / "Documents",
            "downloads": Path.home() / "Downloads",
            "pictures": Path.home() / "Pictures",
            "music": Path.home() / "Music",
            "videos": Path.home() / "Videos",
            "my documents": Path.home() / "Documents",
            "my desktop": Path.home() / "Desktop",
        }

        path = folder_map.get(path_str.lower().strip(), Path(path_str))

        if not path.exists():
            return f"Directory '{path_str}' not found."
        if not path.is_dir():
            return f"'{path_str}' is not a directory."

        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            if not items:
                return f"'{path_str}' is empty."

            lines = []
            for item in items[:30]:  # Limit output
                icon = "📁" if item.is_dir() else "📄"
                lines.append(f"  {icon} {item.name}")

            result = f"Files in {path_str} ({len(items)} items):\n" + "\n".join(lines)
            if len(items) > 30:
                result += f"\n  ... and {len(items) - 30} more"
            return result
        except PermissionError:
            return f"Permission denied for '{path_str}'."

    def search_files(self, query: str, search_path: str | None = None) -> str:
        """Search for files by name."""
        base = Path(search_path) if search_path else Path.home()
        results = []
        try:
            for item in base.rglob(f"*{query}*"):
                results.append(str(item))
                if len(results) >= 15:
                    break
        except PermissionError:
            pass

        if results:
            return f"Found {len(results)} matches:\n" + "\n".join(f"  📄 {r}" for r in results)
        return f"No files matching '{query}' found."

    def open_file(self, path_str: str) -> str:
        """Open a file with the default application."""
        path = Path(path_str)
        if not path.exists():
            # Try desktop
            desktop_path = Path.home() / "Desktop" / path_str
            if desktop_path.exists():
                path = desktop_path
            else:
                return f"File '{path_str}' not found."

        try:
            os.startfile(str(path))
            return f"Opening '{path.name}'..."
        except Exception as e:
            return f"Failed to open file: {e}"

    # ── System Information ──────────────────────────────────────────────

    def get_system_info(self) -> str:
        """Get comprehensive system information."""
        try:
            info = []
            info.append(f"💻 Computer: {platform.node()}")
            info.append(f"🖥️ OS: {platform.system()} {platform.release()} ({platform.version()})")
            info.append(f"🔧 Architecture: {platform.machine()}")
            info.append(f"🧮 Processor: {platform.processor()}")

            # CPU / Memory via PowerShell
            ps_cmd = (
                "$os = Get-CimInstance Win32_OperatingSystem; "
                "$cpu = Get-CimInstance Win32_Processor; "
                "Write-Output \"CPU: $($cpu.Name)\"; "
                "Write-Output \"Cores: $($cpu.NumberOfCores) / Threads: $($cpu.NumberOfLogicalProcessors)\"; "
                "$totalMem = [math]::Round($os.TotalVisibleMemorySize/1MB, 1); "
                "$freeMem = [math]::Round($os.FreePhysicalMemory/1MB, 1); "
                "Write-Output \"RAM: $($totalMem) GB total, $($freeMem) GB free\""
            )
            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=10,
            )
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    info.append(f"  {line.strip()}")

            return "\n".join(info)
        except Exception as e:
            return f"Error getting system info: {e}"

    def get_battery(self) -> str:
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "(Get-CimInstance Win32_Battery | Select-Object EstimatedChargeRemaining, BatteryStatus | ConvertTo-Json)"],
                capture_output=True, text=True, timeout=10,
            )
            if result.stdout.strip():
                data = json.loads(result.stdout.strip())
                charge = data.get("EstimatedChargeRemaining", "N/A")
                status_map = {1: "Discharging", 2: "AC Power", 3: "Fully Charged", 4: "Low", 5: "Critical"}
                status = status_map.get(data.get("BatteryStatus", 0), "Unknown")
                return f"🔋 Battery: {charge}% ({status})"
            return "🔋 No battery detected (desktop PC?)."
        except Exception:
            return "Could not retrieve battery info."

    def get_cpu_info(self) -> str:
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "(Get-CimInstance Win32_Processor).LoadPercentage"],
                capture_output=True, text=True, timeout=10,
            )
            load = result.stdout.strip() or "N/A"
            return f"🧮 CPU Usage: {load}%"
        except Exception:
            return "Could not retrieve CPU info."

    def get_memory_info(self) -> str:
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "$os = Get-CimInstance Win32_OperatingSystem; "
                 "$total = [math]::Round($os.TotalVisibleMemorySize/1MB, 1); "
                 "$free = [math]::Round($os.FreePhysicalMemory/1MB, 1); "
                 "$used = [math]::Round($total - $free, 1); "
                 "Write-Output \"Total: ${total}GB | Used: ${used}GB | Free: ${free}GB\""],
                capture_output=True, text=True, timeout=10,
            )
            return f"💾 RAM: {result.stdout.strip()}"
        except Exception:
            return "Could not retrieve memory info."

    def get_disk_info(self) -> str:
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-PSDrive -PSProvider FileSystem | ForEach-Object { "
                 "$total = [math]::Round($_.Used/1GB + $_.Free/1GB, 1); "
                 "$used = [math]::Round($_.Used/1GB, 1); "
                 "$free = [math]::Round($_.Free/1GB, 1); "
                 "\"$($_.Name): ${total}GB total, ${used}GB used, ${free}GB free\" }"],
                capture_output=True, text=True, timeout=10,
            )
            return f"💿 Drives:\n{result.stdout.strip()}"
        except Exception:
            return "Could not retrieve disk info."

    def get_ip_address(self) -> str:
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike '*Loopback*' } | "
                 "Select-Object -First 1 IPAddress).IPAddress"],
                capture_output=True, text=True, timeout=10,
            )
            ip = result.stdout.strip() or "Not found"
            return f"🌐 IP Address: {ip}"
        except Exception:
            return "Could not retrieve IP address."

    # ── Volume Control ──────────────────────────────────────────────────

    def set_volume(self, level: int) -> str:
        """Set system volume to a specific level (0-100)."""
        level = max(0, min(100, level))
        try:
            # Use PowerShell with audio COM object
            ps_cmd = (
                "$wshShell = New-Object -ComObject WScript.Shell; "
                "1..50 | ForEach-Object { $wshShell.SendKeys([char]174) }; "  # Volume down to 0
                f"1..{level // 2} | ForEach-Object {{ $wshShell.SendKeys([char]175) }}"  # Volume up
            )
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, timeout=15)
            return f"🔊 Volume set to ~{level}%."
        except Exception as e:
            return f"Failed to set volume: {e}"

    def adjust_volume(self, direction: str) -> str:
        """Adjust volume up/down/mute/unmute."""
        key_map = {
            "up": "[char]175",     # VK_VOLUME_UP
            "down": "[char]174",   # VK_VOLUME_DOWN
            "mute": "[char]173",   # VK_VOLUME_MUTE
            "unmute": "[char]173", # Toggle mute
        }
        key = key_map.get(direction.lower(), "[char]175")
        steps = 5 if direction.lower() in ("up", "down") else 1

        try:
            ps_cmd = f"$w = New-Object -ComObject WScript.Shell; 1..{steps} | ForEach-Object {{ $w.SendKeys({key}) }}"
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, timeout=10)
            return f"🔊 Volume {direction}."
        except Exception as e:
            return f"Volume control failed: {e}"

    # ── Screenshot ──────────────────────────────────────────────────────

    def take_screenshot(self, save_dir: str | None = None) -> str:
        """Capture a screenshot and save to disk."""
        save_path = Path(save_dir) if save_dir else Path.home() / "Desktop" / "screenshots"
        save_path.mkdir(parents=True, exist_ok=True)
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = save_path / filename

        try:
            ps_cmd = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
                "$bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height); "
                "$graphics = [System.Drawing.Graphics]::FromImage($bitmap); "
                "$graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size); "
                f"$bitmap.Save('{filepath}'); "
                "$graphics.Dispose(); $bitmap.Dispose()"
            )
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, timeout=10)

            if filepath.exists():
                return f"📸 Screenshot saved: {filepath}"
            return "Screenshot capture failed."
        except Exception as e:
            return f"Screenshot error: {e}"

    # ── Screen Lock ─────────────────────────────────────────────────────

    def lock_screen(self) -> str:
        try:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], timeout=5)
            return "🔒 Screen locked."
        except Exception as e:
            return f"Failed to lock screen: {e}"

    # ── Process Management ──────────────────────────────────────────────

    def list_processes(self, limit: int = 20) -> str:
        """List top running processes by memory usage."""
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 f"Get-Process | Sort-Object -Property WorkingSet64 -Descending | "
                 f"Select-Object -First {limit} Name, "
                 "@{Name='Memory(MB)';Expression={{[math]::Round($_.WorkingSet64/1MB, 1)}}}, "
                 "CPU | Format-Table -AutoSize | Out-String"],
                capture_output=True, text=True, timeout=10,
            )
            return f"📋 Top {limit} Processes:\n{result.stdout.strip()}"
        except Exception as e:
            return f"Could not list processes: {e}"

    # ── Music / Media ───────────────────────────────────────────────────

    def play_music(self) -> str:
        """Open default music player."""
        try:
            music_dir = Path.home() / "Music"
            if music_dir.exists():
                mp3_files = list(music_dir.glob("*.mp3"))
                if mp3_files:
                    os.startfile(str(mp3_files[0]))
                    return f"🎵 Playing: {mp3_files[0].name}"
            # Fallback: open Spotify or Groove Music
            self.open_app("spotify")
            return "🎵 Opening Spotify..."
        except Exception:
            return "🎵 No music player found. Try 'open spotify'."

    def pause_music(self) -> str:
        """Send media pause key."""
        try:
            ps_cmd = "$w = New-Object -ComObject WScript.Shell; $w.SendKeys([char]179)"
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, timeout=5)
            return "⏸️ Media paused."
        except Exception:
            return "Could not pause media."

    # ── Dispatcher ──────────────────────────────────────────────────────

    def execute(self, action: str, data: dict) -> str:
        """Execute an action based on CommandResult data."""
        dispatch = {
            "open_app": lambda: self.open_app(data.get("app", "")),
            "close_app": lambda: self.close_app(data.get("app", "")),
            "web_search": lambda: self.web_search(data.get("query", ""), data.get("engine", "google")),
            "open_url": lambda: self.open_url(data.get("url", "")),
            "open_and_search": lambda: self.open_and_search(data.get("app", "chrome"), data.get("query", "")),
            "create_file": lambda: self.create_file(data.get("name", "untitled.txt"), data.get("type", "file")),
            "delete_file": lambda: self.delete_file(data.get("name", "")),
            "list_files": lambda: self.list_files(data.get("path", "Desktop")),
            "search_files": lambda: self.search_files(data.get("query", "")),
            "open_file": lambda: self.open_file(data.get("path", "")),
            "screenshot": lambda: self.take_screenshot(data.get("save_dir")),
            "volume": lambda: self.set_volume(data.get("level", 50)),
            "volume_adjust": lambda: self.adjust_volume(data.get("direction", "up")),
            "volume_toggle": lambda: self.adjust_volume(data.get("action", "mute")),
            "lock": lambda: self.lock_screen(),
            "system_info": lambda: self.get_system_info(),
            "battery": lambda: self.get_battery(),
            "cpu_info": lambda: self.get_cpu_info(),
            "memory_info": lambda: self.get_memory_info(),
            "disk_info": lambda: self.get_disk_info(),
            "ip_address": lambda: self.get_ip_address(),
            "list_processes": lambda: self.list_processes(),
            "play_music": lambda: self.play_music(),
            "pause_music": lambda: self.pause_music(),
        }

        handler = dispatch.get(action)
        if handler:
            return handler()
        return ""
