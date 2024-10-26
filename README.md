# AI Assistant

A modular, extensible desktop application for interacting with AI language models through text and speech.

## Features

- 🤖 Multiple AI model support (OpenAI GPT-4, Anthropic Claude)
- 🎙️ Speech-to-text capabilities (Whisper, Deepgram)
- 🔊 Audio input/output support (PyAudio, SoundDevice)
- 📋 Cross-platform clipboard integration
- 🌙 Dark/Light theme support
- ⚡ Asynchronous processing
- 🔌 Modular provider system
- 🎨 Modern Qt-based UI

## Architecture

The application follows a modular architecture with clear separation of concerns:

```
ai_assistant/
├── core/               # Core interfaces and events
├── modules/            # Provider implementations
├── ui/                 # User interface components
├── config/            # Configuration management
└── utils/             # Utility functions
```

### Provider System

The application uses a provider-based architecture that allows easy swapping of implementations:

- **Assistant Providers**: OpenAI GPT-4, Anthropic Claude
- **Speech Providers**: Whisper (local), Deepgram (cloud)
- **Audio Providers**: PyAudio, SoundDevice
- **Clipboard Providers**: Qt, Pyperclip

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/ai-assistant.git
cd ai-assistant
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `config/settings.yaml` file:

```yaml
audio:
  provider: pyaudio
  config:
    sample_rate: 16000
    channels: 1
    chunk_size: 1024

speech:
  provider: whisper
  config: {}

assistant:
  provider: anthropic
  config: {}

clipboard:
  provider: qt
  config: {}

ui:
  theme: dark
  window_size: [800, 600]
```

## Environment Variables

The following environment variables need to be set:

- `OPENAI_API_KEY` - For OpenAI provider
- `ANTHROPIC_API_KEY` - For Anthropic provider
- `DEEPGRAM_API_KEY` - For Deepgram provider

## Usage

1. Start the application:

```bash
python -m ai_assistant.main
```

2. Select your preferred AI model and configure its parameters using the settings dialog.

3. Use either text input or voice recording to communicate with the AI.

4. The AI's responses will be displayed in the chat window and can be copied to clipboard.

## Development

### Adding New Providers

1. Create a new provider class implementing the appropriate interface from `core/interfaces/`
2. Add the provider to the relevant factory in `modules/`
3. Update the configuration system to support the new provider

### Running Tests

```bash
python -m pytest tests/
```

## Current State

The application is in active development. Current focus areas:

- [ ] Implementing comprehensive error handling
- [ ] Adding unit and integration tests
- [ ] Improving audio level visualization
- [ ] Adding support for more AI models
- [ ] Implementing message history persistence
- [ ] Adding support for custom prompts/personas

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PyQt6 for the UI framework
- OpenAI and Anthropic for their AI APIs
- The open-source community for various audio and speech processing libraries

## Support

For support, please open an issue in the GitHub repository.

## Assistant Configuration

You can create custom assistant configurations by adding YAML files with the prefix `va-` in the root directory. For example, `va-programmer.yaml`:

```yaml
name: "Programming Assistant"
description: "Specialized assistant for programming help"
system_prompt: |
  You are an expert programmer with deep knowledge of multiple programming languages.
  Always provide code examples and explain your reasoning.
model: "claude-3-opus-20240229"
settings:
  temperature: 0.7
  top_p: 0.9
```

The application will automatically load all `va-*.yaml` files and make these assistants available in the UI.
