import datetime
import os
import json


class AIChatHistory:
    def __init__(self, log_file_path, va_name, username):
        self.history = []
        self.log_file_path = log_file_path
        self.va_name = va_name
        self.username = username
        self.load_history()

    def add_entry(self, entry_type, content):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "type": entry_type,
            "content": content,
            "va_name": self.va_name,
            "username": self.username,
        }
        self.history.append(entry)
        self.save_history()

    def get_history(self):
        return "\n".join(
            [
                f"[{entry['timestamp']}] {entry['username']} to {entry['va_name']} - {entry['type']}: {entry['content']}"
                for entry in self.history
            ]
        )

    def load_history(self):
        if os.path.exists(self.log_file_path):
            with open(self.log_file_path, "r") as f:
                self.history = json.load(f)

    def save_history(self):
        with open(self.log_file_path, "w") as f:
            json.dump(self.history, f, indent=2)
