# Modular Architecture Restructuring Proposal

## Directory Structure

First, let's reorganize the project structure to better support modularity:

```
ai_assistant/
├── core/
│   ├── __init__.py
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── audio.py
│   │   ├── speech.py
│   │   ├── assistant.py
│   │   └── clipboard.py
│   └── events.py
├── modules/
│   ├── __init__.py
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── pyaudio_provider.py
│   │   └── sounddevice_provider.py
│   ├── speech/
│   │   ├── __init__.py
│   │   ├── deepgram_provider.py
│   │   └── whisper_provider.py
│   ├── assistant/
│   │   ├── __init__.py
│   │   ├── openai_provider.py
│   │   └── anthropic_provider.py
│   └── clipboard/
│       ├── __init__.py
│       ├── qt_provider.py
│       └── pyperclip_provider.py
├── ui/
│   ├── __init__.py
│   ├── chat_window.py
│   └── components/
├── config/
│   ├── __init__.py
│   └── settings.py
└── utils/
    ├── __init__.py
    └── registry.py
```

## Core Interfaces

Let's define clear interfaces for each major component:

```python
# core/interfaces/audio.py
from abc import ABC, abstractmethod
from typing import Optional, BinaryIO, Protocol
from dataclasses import dataclass

@dataclass
class AudioConfig:
    sample_rate: int
    channels: int
    chunk_size: int
    device_id: Optional[int] = None

class AudioInputProvider(Protocol):
    @abstractmethod
    def start_stream(self, config: AudioConfig) -> None:
        """Start audio input stream"""
        pass

    @abstractmethod
    def read_chunk(self) -> bytes:
        """Read a chunk of audio data"""
        pass

    @abstractmethod
    def stop_stream(self) -> None:
        """Stop audio input stream"""
        pass

class AudioOutputProvider(Protocol):
    @abstractmethod
    def play_audio(self, audio_data: BinaryIO) -> None:
        """Play audio from data"""
        pass
```

```python
# core/interfaces/speech.py
from typing import Protocol, AsyncIterator

class SpeechToTextProvider(Protocol):
    async def transcribe_stream(self, audio_stream: AsyncIterator[bytes]) -> AsyncIterator[str]:
        """Convert streaming audio to text"""
        pass

class TextToSpeechProvider(Protocol):
    async def synthesize(self, text: str) -> bytes:
        """Convert text to speech"""
        pass
```

## Implementation Examples

```python
# modules/audio/pyaudio_provider.py
import pyaudio
from core.interfaces.audio import AudioInputProvider, AudioOutputProvider, AudioConfig

class PyAudioProvider(AudioInputProvider, AudioOutputProvider):
    def __init__(self):
        self._audio = pyaudio.PyAudio()
        self._stream = None

    def start_stream(self, config: AudioConfig) -> None:
        self._stream = self._audio.open(
            format=pyaudio.paFloat32,
            channels=config.channels,
            rate=config.sample_rate,
            input=True,
            input_device_index=config.device_id,
            frames_per_buffer=config.chunk_size
        )

    def read_chunk(self) -> bytes:
        return self._stream.read(self._chunk_size)

    def stop_stream(self) -> None:
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
```

```python
# modules/speech/deepgram_provider.py
from core.interfaces.speech import SpeechToTextProvider
from typing import AsyncIterator
import os
from deepgram import DeepgramClient

class DeepgramProvider(SpeechToTextProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        self.client = DeepgramClient(self.api_key)

    async def transcribe_stream(self, audio_stream: AsyncIterator[bytes]) -> AsyncIterator[str]:
        async for chunk in audio_stream:
            response = await self.client.transcribe(chunk)
            if transcript := response.results.channels[0].alternatives[0].transcript:
                yield transcript
```

## Factory Pattern for Provider Selection

```python
# modules/audio/__init__.py
from enum import Enum
from core.interfaces.audio import AudioInputProvider, AudioOutputProvider
from .pyaudio_provider import PyAudioProvider
from .sounddevice_provider import SoundDeviceProvider

class AudioProviderType(Enum):
    PYAUDIO = "pyaudio"
    SOUNDDEVICE = "sounddevice"

def create_audio_provider(provider_type: AudioProviderType) -> AudioInputProvider:
    providers = {
        AudioProviderType.PYAUDIO: PyAudioProvider,
        AudioProviderType.SOUNDDEVICE: SoundDeviceProvider,
    }
    return providers[provider_type]()
```

## Registry for Provider Management

```python
# utils/registry.py
from typing import Dict, Type, TypeVar
from core.interfaces import audio, speech, assistant, clipboard

T = TypeVar('T')

class ProviderRegistry:
    _instance = None

    def __init__(self):
        self._providers: Dict[Type, object] = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_provider(self, interface_type: Type[T], provider: T):
        self._providers[interface_type] = provider

    def get_provider(self, interface_type: Type[T]) -> T:
        return self._providers.get(interface_type)
```

## Configuration System

```python
# config/settings.py
from dataclasses import dataclass
from typing import Dict, Any
from modules.audio import AudioProviderType

@dataclass
class ModuleConfig:
    provider_type: str
    config: Dict[str, Any]

@dataclass
class AppConfig:
    audio: ModuleConfig
    speech: ModuleConfig
    assistant: ModuleConfig
    clipboard: ModuleConfig

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AppConfig':
        return cls(
            audio=ModuleConfig(
                provider_type=config_dict['audio']['provider'],
                config=config_dict['audio'].get('config', {})
            ),
            # ... similar for other modules
        )
```

## Usage Example

```python
# Example application initialization
from utils.registry import ProviderRegistry
from core.interfaces import audio, speech
from modules.audio import create_audio_provider, AudioProviderType
from modules.speech import create_speech_provider, SpeechProviderType
from config.settings import AppConfig

def initialize_app(config: AppConfig):
    registry = ProviderRegistry.get_instance()

    # Initialize audio provider
    audio_provider = create_audio_provider(
        AudioProviderType(config.audio.provider_type)
    )
    registry.register_provider(audio.AudioInputProvider, audio_provider)

    # Initialize speech provider
    speech_provider = create_speech_provider(
        SpeechProviderType(config.speech.provider_type)
    )
    registry.register_provider(speech.SpeechToTextProvider, speech_provider)
```

## Benefits of This Restructure:

1. **True Modularity**: Each provider implements a well-defined interface, making them truly interchangeable.

2. **Clear Dependencies**: The interface definitions make it explicit what each provider must implement.

3. **Easy Testing**: Mock providers can be easily created for testing by implementing the interfaces.

4. **Simple Extension**: New providers can be added by implementing the relevant interface and adding to the factory.

5. **Configuration Driven**: Provider selection and configuration is handled through configuration, not hard-coded.

6. **Type Safety**: Using Protocol classes provides type checking while maintaining loose coupling.

## Migration Strategy:

1. Start by creating the interface definitions
2. Create new providers implementing these interfaces
3. Gradually migrate existing code to use the new providers
4. Update the configuration system to support provider selection
5. Refactor the main application to use the registry

Would you like me to elaborate on any part of this restructuring proposal or provide more specific examples for certain components?
