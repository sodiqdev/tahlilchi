# app/settings_manager.py
import json
import os


class SettingsManager:
    def __init__(self, path="settings.json"):
        self.path = path
        self.defaults = {
            "tuman": "",
            "maktab": "",
            "oibdo": "",
            "metod_rahbari": "",
            "fan_oqituvchisi": "",
            "output_dir": ""
        }

    def load(self) -> dict:
        if not os.path.exists(self.path):
            return self.defaults.copy()

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {**self.defaults, **data}
        except Exception:
            return self.defaults.copy()

    def save(self, data: dict):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
