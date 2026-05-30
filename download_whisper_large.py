"""Download whisper-large-v3 CTranslate2 model for faster-whisper (CUDA).

Uses local proxy (127.0.0.1:3128) to bypass Bosch 407 proxy auth.
Downloads from: https://huggingface.co/Systran/faster-whisper-large-v3

Required files: model.bin, config.json, tokenizer.json, vocabulary.txt
Total size: ~3 GB

Auto-retries on failure until download completes.
"""
import os
import sys
import time
from pathlib import Path

import httpx

LOCAL_PROXY = "http://127.0.0.1:3128"
REPO_BASE = "https://huggingface.co/Systran/faster-whisper-large-v3/resolve/main"
MODEL_DIR = Path(__file__).parent / "assets" / "whisper-large-v3"
MAX_RETRIES = 50  # Keep retrying aggressively
RETRY_DELAY = 5   # Seconds between retries

# Files needed for faster-whisper CTranslate2 model
FILES = [
    "model.bin",        # ~3 GB - the main weights
    "config.json",
    "tokenizer.json",
    "vocabulary.txt",
]


def download_file(url: str, dest: Path) -> bool:
    """Download a file with progress bar via local proxy. Supports resume."""
    existing_size = dest.stat().st_size if dest.exists() else 0
    
    # Check if already fully downloaded
    if existing_size > 0:
        # Do a HEAD request to get expected size
        try:
            head_r = httpx.head(url, proxy=LOCAL_PROXY, verify=False, timeout=30, follow_redirects=True)
            expected = int(head_r.headers.get("content-length", 0))
            if expected > 0 and existing_size >= expected:
                print(f"  Already complete: {dest.name} ({existing_size / 1024 / 1024:.1f} MB)")
                return True
            elif existing_size > 0:
                print(f"  Resuming: {dest.name} from {existing_size / 1024 / 1024:.1f} MB / {expected / 1024 / 1024:.1f} MB")
        except Exception:
            pass

    if existing_size == 0:
        print(f"  Downloading: {dest.name}")
    headers = {}
    if existing_size > 0:
        headers["Range"] = f"bytes={existing_size}-"
    
    try:
        with httpx.stream(
            "GET", url,
            proxy=LOCAL_PROXY, verify=False,
            timeout=httpx.Timeout(connect=30, read=120, write=30, pool=30),
            follow_redirects=True,
            headers=headers,
        ) as response:
            if response.status_code == 416:
                # Range not satisfiable = file already complete
                print(f"  Already complete: {dest.name}")
                return True
            if response.status_code not in (200, 206):
                print(f"    ERROR: HTTP {response.status_code}")
                return False
            
            # If server doesn't support range, start fresh
            if response.status_code == 200 and existing_size > 0:
                existing_size = 0
                
            total = int(response.headers.get("content-length", 0)) + existing_size
            downloaded = existing_size
            mode = "ab" if response.status_code == 206 else "wb"
            
            with open(dest, mode) as f:
                for chunk in response.iter_bytes(chunk_size=131072):
                    f.write(chunk)
                    f.flush()
                    downloaded += len(chunk)
                    if total > 0:
                        pct = downloaded * 100 / total
                        mb = downloaded / 1024 / 1024
                        total_mb = total / 1024 / 1024
                        sys.stdout.write(f"\r    {mb:.1f}/{total_mb:.1f} MB ({pct:.0f}%)")
                        sys.stdout.flush()
            print(f"\r    Done: {downloaded / 1024 / 1024:.1f} MB" + " " * 20)
        return True
    except Exception as e:
        current_size = dest.stat().st_size / 1024 / 1024 if dest.exists() else 0
        print(f"\n    Connection lost at {current_size:.1f} MB: {type(e).__name__}")
        return False


def download_file_with_retry(url: str, dest: Path) -> bool:
    """Download with automatic retry on failure."""
    for attempt in range(1, MAX_RETRIES + 1):
        if download_file(url, dest):
            return True
        print(f"    Retry {attempt}/{MAX_RETRIES} in {RETRY_DELAY}s...")
        time.sleep(RETRY_DELAY)
    print(f"    FAILED after {MAX_RETRIES} retries.")
    return False


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading whisper-large-v3 to: {MODEL_DIR}")
    print(f"Using proxy: {LOCAL_PROXY}")
    print(f"Auto-retry enabled: up to {MAX_RETRIES} retries per file")
    print()

    # Test proxy connectivity
    try:
        r = httpx.get("https://huggingface.co", proxy=LOCAL_PROXY, verify=False, timeout=10)
        print(f"Proxy connection OK (status {r.status_code})")
    except Exception as e:
        print(f"ERROR: Cannot reach HuggingFace via proxy: {e}")
        print("Make sure your local proxy (CNTLM/px) is running on port 3128.")
        sys.exit(1)

    print()
    all_ok = True
    for fname in FILES:
        url = f"{REPO_BASE}/{fname}"
        dest = MODEL_DIR / fname
        if not download_file_with_retry(url, dest):
            all_ok = False
            break

    if all_ok:
        print()
        print("=" * 60)
        print("SUCCESS! whisper-large-v3 model downloaded.")
        print(f"Path: {MODEL_DIR}")
        print()
        print("To activate, update config/settings.json:")
        print('  "whisper_model": "large-v3"')
        print()
        print("The model will use CUDA (your RTX A3000) automatically.")
        print("=" * 60)
    else:
        print()
        print("Download failed. Check proxy and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
