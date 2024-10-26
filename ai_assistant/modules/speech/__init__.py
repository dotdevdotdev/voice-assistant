from enum import Enum
from core.interfaces.speech import SpeechToTextProvider, TextToSpeechProvider
from .whisper_provider import WhisperProvider
from .deepgram_provider import DeepgramProvider


class SpeechProviderType(Enum):
    WHISPER = "whisper"
    DEEPGRAM = "deepgram"


def create_speech_provider(provider_type: str) -> SpeechToTextProvider:
    providers = {
        "whisper": WhisperProvider,
        "deepgram": DeepgramProvider,
    }

    if provider_type not in providers:
        raise ValueError(f"Unknown speech provider type: {provider_type}")

    return providers[provider_type]()
