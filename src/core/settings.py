import os
import json
from pathlib import Path

class Settings:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        # Paths
        docs = Path(os.path.expanduser("~")) / "Documents"
        self.base_dir = docs / "MatcapMaker"
        self.output_dir = self.base_dir / "output"
        self.projects_dir = self.base_dir / "projects"
        self.config_file = self.base_dir / "config.json"
        
        self._ensure_dirs()
        
        # Default Settings
        self.export_resolution = 2048
        self.export_padding = 4
        self.language = "ja" # Default Japanese
        
        # Load from file
        self.load()
        
    def _ensure_dirs(self):
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.projects_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Failed to create directories: {e}")
            
    def get_output_dir(self):
        return str(self.output_dir)
        
    def get_projects_dir(self):
        return str(self.projects_dir)

    def load(self):
        if not self.config_file.exists():
            return
            
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                self.export_resolution = data.get("export_resolution", 2048)
                self.export_padding = data.get("export_padding", 4)
                self.language = data.get("language", "ja")
                # print(f"Settings loaded: {data}")
        except Exception as e:
            print(f"Failed to load settings: {e}")

    def save(self):
        data = {
            "export_resolution": self.export_resolution,
            "export_padding": self.export_padding,
            "language": self.language
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=4)
            # print("Settings saved.")
        except Exception as e:
            print(f"Failed to save settings: {e}")

