"""Voice alert service for sim racing pit wall notifications."""

import logging

from ..config import AppConfig
from ..telemetry.models import TelemetryData
from .alert_engine import AlertEngine
from .tts_service import TTSService

log = logging.getLogger(__name__)


class VoiceService:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        voice_name = config.voice_en if config.voice_language == "en" else config.voice_pt
        self._tts = TTSService(voice_name=voice_name, volume=config.voice_volume)
        self._alert_engine = AlertEngine(config)

    def start(self) -> None:
        self._tts.start()

    def stop(self) -> None:
        self._tts.stop()

    def on_frame(self, data: TelemetryData, fuel_per_lap: float) -> None:
        for text in self._alert_engine.process(data, fuel_per_lap):
            self._tts.speak(text)

    _TEST_PHRASES = {
        "en": "This is an engineer voice test.",
        "pt": "Este é um teste de voz de engenheiro.",
    }

    def speak_test(self, language: str | None = None) -> None:
        lang = language or self._config.voice_language
        self._tts.speak(self._TEST_PHRASES.get(lang, self._TEST_PHRASES["en"]))

    def reset(self) -> None:
        self._alert_engine.reset()
