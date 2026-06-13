"""Piper TTS wrapper running in a dedicated daemon thread."""

import io
import logging
import os
import queue
import subprocess
import tempfile
import threading
import urllib.request
import wave
from pathlib import Path

log = logging.getLogger(__name__)

_VOICES_DIR = Path.home() / "simracing" / "piper"

_MODEL_URLS: dict[str, tuple[str, str]] = {
    "en_US-lessac-medium": (
        "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
        "/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
        "/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
    ),
    "pt_BR-faber-medium": (
        "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
        "/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx",
        "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
        "/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json",
    ),
}


def _ensure_model(voice_name: str) -> tuple[Path, Path]:
    _VOICES_DIR.mkdir(parents=True, exist_ok=True)
    onnx_path = _VOICES_DIR / f"{voice_name}.onnx"
    json_path = _VOICES_DIR / f"{voice_name}.onnx.json"

    urls = _MODEL_URLS.get(voice_name)
    if not urls:
        raise ValueError(f"Unknown voice model: {voice_name!r}")

    missing = [p for p in [onnx_path, json_path] if not p.exists()]
    if missing:
        print(
            f"\n[voice] First run — downloading Piper TTS model '{voice_name}' (~200 MB)."
            " This happens once; subsequent starts are instant.\n"
        )

    for path, url in zip([onnx_path, json_path], urls):
        if not path.exists():
            log.info("Downloading %s …", path.name)
            urllib.request.urlretrieve(url, path)  # noqa: S310
            log.info("Downloaded %s (%.1f MB)", path.name, path.stat().st_size / 1e6)

    return onnx_path, json_path


class TTSService:
    def __init__(self, voice_name: str, volume: float = 0.8) -> None:
        self._voice_name = voice_name
        self._volume = volume
        self._q: queue.SimpleQueue[str | None] = queue.SimpleQueue()
        self._voice = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Download model if needed, load it, and start playback thread."""
        try:
            from piper.voice import PiperVoice  # type: ignore[import]
        except ImportError:
            log.warning("piper-tts not installed — voice alerts disabled. "
                        "Install with: pip install 'simracing-engineer[voice]'")
            return

        try:
            onnx_path, json_path = _ensure_model(self._voice_name)
            self._voice = PiperVoice.load(
                str(onnx_path), config_path=str(json_path), use_cuda=False
            )
            log.info("Piper TTS ready: %s", self._voice_name)
        except Exception as exc:
            log.error("Failed to load TTS model %r: %s", self._voice_name, exc)
            return

        self._thread = threading.Thread(target=self._run, daemon=True, name="piper-tts")
        self._thread.start()

    def stop(self) -> None:
        self._q.put(None)

    def speak(self, text: str) -> None:
        if self._voice is None:
            return
        if self._q.empty():
            self._q.put(text)

    def _run(self) -> None:
        while True:
            item = self._q.get()
            if item is None:
                break
            try:
                self._synthesize_and_play(item)
            except Exception:
                log.exception("TTS playback error")

    def _synthesize_and_play(self, text: str) -> None:
        if self._voice is None:
            return

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav:
            self._voice.synthesize_wav(text, wav)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(buf.getvalue())
            tmp_path = f.name
        try:
            subprocess.run(
                ["afplay", "-v", str(self._volume), tmp_path],
                check=False, timeout=30,
            )
        finally:
            os.unlink(tmp_path)
