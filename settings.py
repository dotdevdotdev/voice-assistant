import os
from pathlib import Path
import json


class Settings:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "voice-assistant"
        self.config_file = self.config_dir / "config.json"
        self.load_settings()

    def load_settings(self):
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True)

        if not self.config_file.exists():
            default_settings = {"openai_api_key": "", "assistants": {}}
            self.save_settings(default_settings)
            self.settings = default_settings
        else:
            with open(self.config_file, "r") as f:
                self.settings = json.load(f)

    def save_settings(self, settings):
        with open(self.config_file, "w") as f:
            json.dump(settings, f, indent=4)

    def get_openai_key(self):
        return self.settings.get("openai_api_key", "")

    def set_openai_key(self, key):
        self.settings["openai_api_key"] = key
        self.save_settings(self.settings)
