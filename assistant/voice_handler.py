"""
Voice Handler Module - Speech-to-Text and Text-to-Speech with wake word detection.
Uses speech_recognition for STT and pyttsx3 for TTS.
Runs on background threads to keep the UI responsive.
"""

import logging
import queue
import struct
import math

from PyQt6.QtCore import QObject, QThread, pyqtSignal

logger = logging.getLogger("jarvis.voice")


class AudioLevelMonitor(QThread):
    """Monitors microphone audio levels for waveform visualization."""
    level_updated = pyqtSignal(float)  # 0.0 - 1.0 normalized level
    stopped = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._running = False

    def run(self):
        try:
            import pyaudio
        except ImportError:
            logger.warning("pyaudio not available for audio level monitoring")
            return

        self._running = True
        pa = pyaudio.PyAudio()
        chunk = 1024
        try:
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=chunk,
            )
        except Exception as e:
            logger.error(f"Cannot open audio stream: {e}")
            pa.terminate()
            return

        while self._running:
            try:
                data = stream.read(chunk, exception_on_overflow=False)
                samples = struct.unpack(f"<{chunk}h", data)
                rms = math.sqrt(sum(s * s for s in samples) / len(samples))
                # Normalize to 0-1 range (16-bit audio max ~32768)
                level = min(rms / 8000.0, 1.0)
                self.level_updated.emit(level)
            except Exception:
                break

        stream.stop_stream()
        stream.close()
        pa.terminate()
        self.stopped.emit()

    def stop(self):
        self._running = False


class STTWorker(QThread):
    """Speech-to-Text worker thread using SpeechRecognition library."""
    text_recognized = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    listening_started = pyqtSignal()
    listening_stopped = pyqtSignal()

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self._engine = settings.get("stt_engine", "windows_sapi")
        self._timeout = settings.get("listen_timeout", 10)
        self._phrase_limit = settings.get("phrase_time_limit", 15)
        self._pause = settings.get("pause_threshold", 1.5)

    def run(self):
        try:
            import speech_recognition as sr
        except ImportError:
            self.error_occurred.emit("speech_recognition not installed. Run: pip install SpeechRecognition")
            return

        recognizer = sr.Recognizer()
        recognizer.pause_threshold = self._pause
        recognizer.dynamic_energy_threshold = False  # We set it manually after calibration

        try:
            mic = sr.Microphone()
        except Exception as e:
            self.error_occurred.emit(f"No microphone found: {e}")
            return

        with mic as source:
            logger.info("Calibrating microphone for ambient noise (2 sec)...")
            recognizer.adjust_for_ambient_noise(source, duration=2.0)

            # Enforce a minimum threshold so background hum doesn't trigger
            # immediately. In a quiet room calibration may produce ~45 which
            # causes instant false triggers.
            MIN_ENERGY = 150
            if recognizer.energy_threshold < MIN_ENERGY:
                logger.info(f"Calibrated energy {recognizer.energy_threshold:.0f} too low, raising to {MIN_ENERGY}")
                recognizer.energy_threshold = MIN_ENERGY
            logger.info(f"Energy threshold: {recognizer.energy_threshold:.0f}")

            self.listening_started.emit()
            logger.info("Listening... speak now!")
            try:
                audio = recognizer.listen(
                    source,
                    timeout=self._timeout,
                    phrase_time_limit=self._phrase_limit,
                )
            except sr.WaitTimeoutError:
                self.listening_stopped.emit()
                self.error_occurred.emit("No speech detected (timeout). Try speaking louder.")
                return
            except Exception as e:
                self.listening_stopped.emit()
                self.error_occurred.emit(f"Listening error: {e}")
                return

        self.listening_stopped.emit()
        logger.info("Audio captured, transcribing...")

        text = None
        engines = self._get_engine_chain()
        for engine_name, recognizer_fn in engines:
            try:
                text = recognizer_fn(recognizer, audio)
                if text:
                    logger.info(f"Transcribed via {engine_name}: {text}")
                    break
            except Exception as e:
                logger.warning(f"{engine_name} failed: {e}")
                continue

        if text:
            self.text_recognized.emit(text)
        else:
            self.error_occurred.emit("Could not understand the audio. Please try again.")

    def _get_engine_chain(self):
        """Return ordered list of (name, fn) for speech recognition engines."""
        import speech_recognition as sr

        engines = []
        if self._engine == "windows_sapi":
            engines.append(("Sphinx", lambda r, a: r.recognize_sphinx(a)))
        elif self._engine == "google":
            engines.append(("Google", lambda r, a: r.recognize_google(a)))
            engines.append(("Sphinx", lambda r, a: r.recognize_sphinx(a)))
        elif self._engine == "sphinx":
            engines.append(("Sphinx", lambda r, a: r.recognize_sphinx(a)))
        else:
            engines.append(("Sphinx", lambda r, a: r.recognize_sphinx(a)))

        # Always have at least Sphinx as offline fallback
        seen = set()
        unique = []
        for name, fn in engines:
            if name not in seen:
                seen.add(name)
                unique.append((name, fn))
        if "Sphinx" not in seen:
            unique.append(("Sphinx", lambda r, a: r.recognize_sphinx(a)))
        return unique


class VoskSTTWorker(QThread):
    """Speech-to-Text using Vosk (offline, high accuracy).
    
    Vosk listens directly via PyAudio and provides real-time streaming
    recognition — much better than Sphinx for accuracy.
    """
    text_recognized = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    listening_started = pyqtSignal()
    listening_stopped = pyqtSignal()
    audio_level = pyqtSignal(float)

    def __init__(self, model_path: str, timeout: int = 10, phrase_timeout: float = 2.0):
        super().__init__()
        self.model_path = model_path
        self.timeout = timeout
        self.phrase_timeout = phrase_timeout  # silence after speech to stop

    def run(self):
        try:
            import pyaudio
            from vosk import Model, KaldiRecognizer
            import json as _json
        except ImportError as e:
            self.error_occurred.emit(f"Missing dependency: {e}. Run: pip install vosk pyaudio")
            return

        # Load model
        try:
            model = Model(self.model_path)
        except Exception as e:
            self.error_occurred.emit(f"Failed to load Vosk model: {e}")
            return

        recognizer = KaldiRecognizer(model, 16000)
        recognizer.SetWords(True)

        pa = pyaudio.PyAudio()
        try:
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=4096,
            )
        except Exception as e:
            pa.terminate()
            self.error_occurred.emit(f"Cannot open microphone: {e}")
            return

        self.listening_started.emit()
        logger.info("Vosk: Listening... speak now!")

        import time
        start_time = time.time()
        last_speech_time = 0.0
        has_speech = False
        full_text = ""

        try:
            while True:
                elapsed = time.time() - start_time

                # Hard timeout
                if elapsed > self.timeout and not has_speech:
                    break

                # If we heard speech, stop after silence
                if has_speech and (time.time() - last_speech_time) > self.phrase_timeout:
                    break

                # Max total time cap
                if elapsed > self.timeout + 10:
                    break

                data = stream.read(4096, exception_on_overflow=False)

                # Emit audio level for waveform
                samples = struct.unpack(f"<{len(data)//2}h", data)
                rms = math.sqrt(sum(s * s for s in samples) / len(samples))
                level = min(rms / 8000.0, 1.0)
                self.audio_level.emit(level)

                if recognizer.AcceptWaveform(data):
                    result = _json.loads(recognizer.Result())
                    text = result.get("text", "").strip()
                    if text:
                        full_text += (" " + text) if full_text else text
                        has_speech = True
                        last_speech_time = time.time()
                        logger.debug(f"Vosk partial final: {text}")
                else:
                    partial = _json.loads(recognizer.PartialResult())
                    partial_text = partial.get("partial", "").strip()
                    if partial_text:
                        has_speech = True
                        last_speech_time = time.time()
                        logger.debug(f"Vosk partial: {partial_text}")

        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()

        # Get final result
        final = _json.loads(recognizer.FinalResult())
        final_text = final.get("text", "").strip()
        if final_text:
            full_text += (" " + final_text) if full_text else final_text

        self.listening_stopped.emit()
        full_text = full_text.strip()

        if full_text:
            logger.info(f"Vosk recognized: \"{full_text}\"")
            self.text_recognized.emit(full_text)
        else:
            logger.info("Vosk: No speech recognized")
            self.error_occurred.emit("No speech detected")


class WhisperSTTWorker(QThread):
    """Speech-to-Text using Faster-Whisper (offline, high accuracy).
    
    Records audio via PyAudio, then transcribes with Faster-Whisper model.
    More accurate than Vosk, especially for unclear speech.
    """
    text_recognized = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    listening_started = pyqtSignal()
    listening_stopped = pyqtSignal()
    audio_level = pyqtSignal(float)

    # Class-level model cache to avoid reloading on each recognition
    _model = None
    _model_size = None

    def __init__(self, model_size: str = "medium", timeout: int = 10, phrase_timeout: float = 2.0):
        super().__init__()
        self.model_size = model_size
        self.timeout = timeout
        self.phrase_timeout = phrase_timeout

    @classmethod
    def get_model(cls, model_size: str):
        """Get or create cached Whisper model."""
        if cls._model is None or cls._model_size != model_size:
            from faster_whisper import WhisperModel
            from pathlib import Path
            
            # Check for local model first (avoids proxy issues)
            local_model_path = Path(__file__).parent.parent / "assets" / f"whisper-{model_size}"
            if local_model_path.exists() and (local_model_path / "model.bin").exists():
                model_path = str(local_model_path)
                logger.info(f"Loading Whisper model from local path: {model_path}")
            else:
                model_path = model_size  # Download from HuggingFace
                logger.info(f"Loading Whisper model: {model_size} (downloading if needed)")
            
            # Use CPU with int8 for good speed/accuracy balance
            cls._model = WhisperModel(model_path, device="cpu", compute_type="int8")
            cls._model_size = model_size
            logger.info("Whisper model loaded successfully")
        return cls._model

    @classmethod
    def is_model_available(cls, model_size: str) -> tuple[bool, str]:
        """Check if Whisper model can be loaded. Returns (success, error_msg)."""
        try:
            cls.get_model(model_size)
            return True, ""
        except Exception as e:
            error_msg = str(e)
            if "407" in error_msg or "Proxy" in error_msg:
                return False, "Proxy authentication required. Download model manually or use Vosk."
            if "Invalid port" in error_msg:
                return False, "Proxy configuration issue (NO_PROXY). Use Vosk or fix proxy settings."
            return False, f"Model load failed: {error_msg[:100]}"

    def run(self):
        try:
            import pyaudio
            import tempfile
            import wave
            import os
        except ImportError as e:
            self.error_occurred.emit(f"Missing dependency: {e}")
            return

        # Pre-load model before listening to reduce delay
        try:
            model = self.get_model(self.model_size)
        except Exception as e:
            self.error_occurred.emit(f"Failed to load Whisper model: {e}")
            return

        # Setup audio recording
        pa = pyaudio.PyAudio()
        try:
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=4096,
            )
        except Exception as e:
            pa.terminate()
            self.error_occurred.emit(f"Cannot open microphone: {e}")
            return

        self.listening_started.emit()
        logger.info("Whisper: Listening... speak now!")

        import time
        start_time = time.time()
        last_sound_time = 0.0
        has_speech = False
        audio_frames = []
        silence_threshold = 500  # RMS threshold for speech detection

        try:
            while True:
                elapsed = time.time() - start_time

                # Hard timeout if no speech yet
                if elapsed > self.timeout and not has_speech:
                    break

                # If we heard speech, stop after silence
                if has_speech and (time.time() - last_sound_time) > self.phrase_timeout:
                    break

                # Max total time cap
                if elapsed > self.timeout + 10:
                    break

                data = stream.read(4096, exception_on_overflow=False)
                audio_frames.append(data)

                # Calculate and emit audio level
                samples = struct.unpack(f"<{len(data)//2}h", data)
                rms = math.sqrt(sum(s * s for s in samples) / len(samples))
                level = min(rms / 8000.0, 1.0)
                self.audio_level.emit(level)

                # Detect speech
                if rms > silence_threshold:
                    has_speech = True
                    last_sound_time = time.time()

        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()

        self.listening_stopped.emit()

        if not audio_frames or not has_speech:
            logger.info("Whisper: No speech detected")
            self.error_occurred.emit("No speech detected")
            return

        # Save audio to temp file for Whisper
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
                wf = wave.open(f, 'wb')
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(16000)
                wf.writeframes(b''.join(audio_frames))
                wf.close()

            # Transcribe with Whisper
            logger.info("Transcribing with Whisper...")
            segments, info = model.transcribe(
                temp_path,
                language="en",
                beam_size=5,
                vad_filter=True,  # Filter out non-speech
            )

            full_text = " ".join(seg.text for seg in segments).strip()

            # Clean up temp file
            os.unlink(temp_path)

        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            self.error_occurred.emit(f"Transcription error: {e}")
            return

        if full_text:
            logger.info(f"Whisper recognized: \"{full_text}\"")
            self.text_recognized.emit(full_text)
        else:
            logger.info("Whisper: No speech recognized")
            self.error_occurred.emit("No speech detected")


class WindowsSTTWorker(QThread):
    """Uses Windows SAPI via PowerShell as fallback (no pip packages needed)."""
    text_recognized = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    listening_started = pyqtSignal()
    listening_stopped = pyqtSignal()

    def __init__(self, timeout: int = 10):
        super().__init__()
        self.timeout = timeout

    def run(self):
        import subprocess
        self.listening_started.emit()

        ps_script = f'''
Add-Type -AssemblyName System.Speech
$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$recognizer.SetInputToDefaultAudioDevice()
$grammar = New-Object System.Speech.Recognition.DictationGrammar
$recognizer.LoadGrammar($grammar)
$recognizer.InitialSilenceTimeout = [TimeSpan]::FromSeconds({self.timeout})
$recognizer.EndSilenceTimeout = [TimeSpan]::FromSeconds(2)
try {{
    $result = $recognizer.Recognize()
    if ($result) {{ Write-Output $result.Text }}
}} catch {{}}
finally {{ $recognizer.Dispose() }}
'''
        try:
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True, text=True,
                timeout=self.timeout + 5,
            )
            self.listening_stopped.emit()
            text = result.stdout.strip()
            if text:
                self.text_recognized.emit(text)
            else:
                self.error_occurred.emit("No speech detected.")
        except subprocess.TimeoutExpired:
            self.listening_stopped.emit()
            self.error_occurred.emit("Speech recognition timed out.")
        except Exception as e:
            self.listening_stopped.emit()
            self.error_occurred.emit(str(e))


class TTSWorker(QThread):
    """Text-to-Speech worker thread."""
    speech_started = pyqtSignal()
    speech_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, text: str, rate: int = 175, volume: float = 0.9):
        super().__init__()
        self.text = text
        self.rate = rate
        self.volume = volume

    def run(self):
        self.speech_started.emit()
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)

            # Try to pick a good voice
            voices = engine.getProperty("voices")
            for voice in voices:
                if "zira" in voice.name.lower() or "david" in voice.name.lower():
                    engine.setProperty("voice", voice.id)
                    break

            engine.say(self.text)
            engine.runAndWait()
            engine.stop()
        except ImportError:
            # Fallback to Windows SAPI via PowerShell
            try:
                import subprocess
                safe_text = self.text.replace("'", "''").replace('"', '`"')
                subprocess.run(
                    ["powershell", "-Command",
                     f"Add-Type -AssemblyName System.Speech; "
                     f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                     f"$s.Rate = {max(-5, min(5, (self.rate - 175) // 25))}; "
                     f"$s.Speak('{safe_text}'); $s.Dispose()"],
                    timeout=60,
                    capture_output=True,
                )
            except Exception as e:
                self.error_occurred.emit(f"TTS failed: {e}")
        except Exception as e:
            self.error_occurred.emit(f"TTS error: {e}")
        finally:
            self.speech_finished.emit()


class ContinuousListener(QThread):
    """Continuously listens for the wake word, then captures a full command."""
    wake_word_detected = pyqtSignal()
    command_recognized = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    level_updated = pyqtSignal(float)

    def __init__(self, wake_word: str = "hey assistant", settings: dict | None = None):
        super().__init__()
        self.wake_word = wake_word.lower()
        self.settings = settings or {}
        self._running = False

    def run(self):
        try:
            import speech_recognition as sr
        except ImportError:
            self.error_occurred.emit("speech_recognition not installed")
            return

        self._running = True
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 1.0
        recognizer.dynamic_energy_threshold = True
        # Let adjust_for_ambient_noise auto-set the energy threshold

        try:
            mic = sr.Microphone()
        except Exception as e:
            self.error_occurred.emit(f"No microphone: {e}")
            return

        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)

        def callback(recognizer, audio):
            if not self._running:
                return
            try:
                text = recognizer.recognize_google(audio).lower()
                if self.wake_word in text:
                    self.wake_word_detected.emit()
                    # Extract command after wake word
                    idx = text.find(self.wake_word) + len(self.wake_word)
                    command = text[idx:].strip()
                    if command:
                        self.command_recognized.emit(command)
            except Exception:
                pass

        stop_listening = recognizer.listen_in_background(mic, callback, phrase_time_limit=10)

        while self._running:
            self.msleep(100)

        stop_listening(wait_for_stop=False)

    def stop(self):
        self._running = False


class VoiceHandler(QObject):
    """High-level voice handler that coordinates STT, TTS, and audio monitoring."""

    # Signals
    listening_started = pyqtSignal()
    listening_stopped = pyqtSignal()
    text_recognized = pyqtSignal(str)
    speech_started = pyqtSignal()
    speech_finished = pyqtSignal()
    audio_level = pyqtSignal(float)
    error_occurred = pyqtSignal(str)
    wake_word_detected = pyqtSignal()

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self._stt_worker = None
        self._tts_worker = None
        self._audio_monitor = None
        self._continuous_listener = None
        self._is_listening = False
        self._is_speaking = False

    @property
    def is_listening(self) -> bool:
        return self._is_listening

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

    def start_listening(self):
        """Start a single speech recognition session."""
        if self._is_listening or self._is_speaking:
            return

        self._is_listening = True

        # Choose STT engine
        stt_engine = self.settings.get("stt_engine", "vosk")

        if stt_engine == "whisper":
            # Faster-Whisper — highest accuracy, transcribes after recording
            model_size = self.settings.get("whisper_model", "medium")
            # Pre-check if model is available (may fail due to proxy)
            available, err = WhisperSTTWorker.is_model_available(model_size)
            if not available:
                logger.warning(f"Whisper unavailable: {err}. Falling back to Vosk.")
                self.error_occurred.emit(f"Whisper unavailable, using Vosk: {err}")
                stt_engine = "vosk"  # fall through to vosk
            else:
                self._stt_worker = WhisperSTTWorker(
                    model_size=model_size,
                    timeout=self.settings.get("listen_timeout", 10),
                    phrase_timeout=self.settings.get("pause_threshold", 2.0),
                )
                # Whisper worker provides its own audio levels
                self._stt_worker.audio_level.connect(self.audio_level.emit)

        if stt_engine == "vosk":
            # Vosk — good offline accuracy, streams audio in real-time
            from pathlib import Path
            model_path = str(Path(__file__).parent.parent / "assets" / "vosk-model")
            if not Path(model_path).exists():
                logger.warning("Vosk model not found, falling back to Sphinx")
                stt_engine = "sphinx"  # fall through below
            else:
                self._stt_worker = VoskSTTWorker(
                    model_path=model_path,
                    timeout=self.settings.get("listen_timeout", 10),
                    phrase_timeout=self.settings.get("pause_threshold", 2.0),
                )
                # Vosk provides its own audio levels, no separate monitor needed
                self._stt_worker.audio_level.connect(self.audio_level.emit)

        if stt_engine == "powershell_sapi":
            # Windows SAPI via PowerShell
            self._stt_worker = WindowsSTTWorker(self.settings.get("listen_timeout", 10))
        elif stt_engine in ("sphinx", "google"):
            # SpeechRecognition library (Sphinx offline or Google online)
            try:
                import speech_recognition  # noqa: F401
                self._stt_worker = STTWorker(self.settings)
            except ImportError:
                logger.warning("SpeechRecognition not installed, falling back to Windows SAPI")
                self._stt_worker = WindowsSTTWorker(self.settings.get("listen_timeout", 10))

        # Start audio level monitor (for engines that don't provide their own)
        if stt_engine not in ("vosk", "whisper"):
            self._audio_monitor = AudioLevelMonitor()
            self._audio_monitor.level_updated.connect(self.audio_level.emit)
            self._audio_monitor.start()

        self._stt_worker.text_recognized.connect(self._on_text_recognized)
        self._stt_worker.error_occurred.connect(self._on_stt_error)
        self._stt_worker.listening_started.connect(self.listening_started.emit)
        self._stt_worker.listening_stopped.connect(self._on_listening_stopped)
        self._stt_worker.start()

    def stop_listening(self):
        """Stop current listening session."""
        if self._audio_monitor:
            self._audio_monitor.stop()
            self._audio_monitor = None
        self._is_listening = False
        self.listening_stopped.emit()

    def speak(self, text: str):
        """Speak the given text."""
        if self._is_speaking:
            return

        self._is_speaking = True
        rate = self.settings.get("tts_rate", 175)
        volume = self.settings.get("tts_volume", 0.9)
        self._tts_worker = TTSWorker(text, rate, volume)
        self._tts_worker.speech_started.connect(self._on_speech_started)
        self._tts_worker.speech_finished.connect(self._on_speech_finished)
        self._tts_worker.error_occurred.connect(self._on_tts_error)
        self._tts_worker.start()

    def start_continuous_listening(self, wake_word: str = "hey assistant"):
        """Start background listening for wake word."""
        if self._continuous_listener:
            return
        self._continuous_listener = ContinuousListener(wake_word, self.settings)
        self._continuous_listener.wake_word_detected.connect(self.wake_word_detected.emit)
        self._continuous_listener.command_recognized.connect(self.text_recognized.emit)
        self._continuous_listener.error_occurred.connect(self.error_occurred.emit)
        self._continuous_listener.start()

    def stop_continuous_listening(self):
        """Stop background wake word listening."""
        if self._continuous_listener:
            self._continuous_listener.stop()
            self._continuous_listener.wait(2000)
            self._continuous_listener = None

    def _on_text_recognized(self, text: str):
        self._is_listening = False
        if self._audio_monitor:
            self._audio_monitor.stop()
        self.text_recognized.emit(text)

    def _on_stt_error(self, error: str):
        self._is_listening = False
        if self._audio_monitor:
            self._audio_monitor.stop()
        self.error_occurred.emit(error)

    def _on_listening_stopped(self):
        if self._audio_monitor:
            self._audio_monitor.stop()
        self._is_listening = False

    def _on_speech_started(self):
        self.speech_started.emit()

    def _on_speech_finished(self):
        self._is_speaking = False
        self.speech_finished.emit()

    def _on_tts_error(self, error: str):
        self._is_speaking = False
        self.error_occurred.emit(error)

    def cleanup(self):
        """Clean up all threads."""
        self.stop_listening()
        self.stop_continuous_listening()
        if self._tts_worker and self._tts_worker.isRunning():
            self._tts_worker.wait(2000)
