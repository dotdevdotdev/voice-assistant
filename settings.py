import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any


class Settings:
    _instance = None

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.app_settings = {}
        self.va_configs = {}

    @staticmethod
    def get_instance():
        if Settings._instance is None:
            Settings._instance = Settings()
        return Settings._instance

    def load_app_settings(self, file_path: str = "app-settings.yaml") -> Dict[str, Any]:
        """Load application settings"""
        try:
            with open(file_path, "r") as f:
                self.app_settings = yaml.safe_load(f)
            return self.app_settings
        except Exception as e:
            self.logger.error(f"Error loading app settings: {e}")
            return {}

    def load_va_configs(self, directory: str = ".") -> Dict[str, Dict]:
        """Load all VA configurations"""
        try:
            path = Path(directory)
            for config_file in path.glob("va-*.yaml"):
                va_name = config_file.stem.replace("va-", "")
                with open(config_file, "r") as f:
                    self.va_configs[va_name] = yaml.safe_load(f)
            return self.va_configs
        except Exception as e:
            self.logger.error(f"Error loading VA configs: {e}")
            return {}

    def save_app_settings(
        self, settings: Dict[str, Any], file_path: str = "app-settings.yaml"
    ):
        """Save application settings"""
        try:
            with open(file_path, "w") as f:
                yaml.dump(settings, f)
            self.app_settings = settings
        except Exception as e:
            self.logger.error(f"Error saving app settings: {e}")

    def save_va_config(self, va_name: str, config: Dict[str, Any]):
        """Save individual VA configuration"""
        try:
            file_path = f"va-{va_name}.yaml"
            with open(file_path, "w") as f:
                yaml.dump(config, f)
            self.va_configs[va_name] = config
        except Exception as e:
            self.logger.error(f"Error saving VA config: {e}")


# Add this if not already present
OPENAI_API_KEY = "your-openai-api-key-here"  # Replace with your actual OpenAI API key

# Add this with the other settings
DEEPGRAM_API_KEY = ""  # User should set this via settings UI


def get_openai_key():
    """Get OpenAI API key from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return api_key
