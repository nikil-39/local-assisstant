"""Download the Vosk English speech recognition model (~50MB, offline)."""
import os
import sys
import zipfile
import shutil
import io

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
MODEL_DIR = os.path.join(os.path.dirname(__file__), "assets", "vosk-model")
TEMP_ZIP = os.path.join(os.path.dirname(__file__), "assets", "vosk-model.zip")

# Local proxy (Bosch RB Local Proxy) — bypasses 407 auth issues
LOCAL_PROXY = "http://127.0.0.1:3128"


def download_model():
    if os.path.isdir(MODEL_DIR) and os.listdir(MODEL_DIR):
        print(f"Model already exists at {MODEL_DIR}")
        return True

    try:
        import httpx
    except ImportError:
        print("httpx not installed. Run: pip install httpx")
        return False

    print(f"Downloading Vosk model from {MODEL_URL}...")
    print("This is ~50MB, one-time download for offline speech recognition.")
    print(f"Using proxy: {LOCAL_PROXY}")
    print()

    try:
        data = bytearray()
        with httpx.stream(
            "GET", MODEL_URL,
            proxy=LOCAL_PROXY, verify=False,
            timeout=300, follow_redirects=True,
        ) as response:
            total = int(response.headers.get("content-length", 0))
            downloaded = 0
            for chunk in response.iter_bytes(chunk_size=65536):
                data.extend(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded * 100 / total
                    mb = downloaded / 1024 / 1024
                    total_mb = total / 1024 / 1024
                    sys.stdout.write(f"\r  Downloading: {mb:.1f}/{total_mb:.1f} MB ({pct:.0f}%)")
                    sys.stdout.flush()

        print("\n  Download complete!")
    except Exception as e:
        print(f"\n  Download failed: {e}")
        print("\n  MANUAL DOWNLOAD INSTRUCTIONS:")
        print(f"  1. Download from: {MODEL_URL}")
        print(f"  2. Extract to: {MODEL_DIR}")
        print("  3. Make sure the 'am', 'conf', 'graph' folders are directly inside vosk-model/")
        return False

    print("  Extracting...")
    try:
        os.makedirs(MODEL_DIR, exist_ok=True)
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")

        # Save zip temporarily
        with open(TEMP_ZIP, "wb") as f:
            f.write(data)

        with zipfile.ZipFile(TEMP_ZIP, "r") as zf:
            zf.extractall(assets_dir)
        for item in os.listdir(assets_dir):
            full = os.path.join(assets_dir, item)
            if os.path.isdir(full) and item.startswith("vosk-model-") and item != "vosk-model":
                extracted = full
                break

        if extracted:
            if os.path.isdir(MODEL_DIR):
                shutil.rmtree(MODEL_DIR)
            shutil.move(extracted, MODEL_DIR)

        os.remove(TEMP_ZIP)
        print(f"  Model installed at: {MODEL_DIR}")
        return True
    except Exception as e:
        print(f"  Extraction failed: {e}")
        return False


if __name__ == "__main__":
    success = download_model()
    if success:
        # Quick test
        from vosk import Model
        model = Model(MODEL_DIR)
        print("  Vosk model loaded successfully!")
    else:
        sys.exit(1)
