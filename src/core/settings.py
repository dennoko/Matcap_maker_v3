import os
from pathlib import Path

class Settings:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.export_resolution = 2048
        
        # Paths
        # User requested: Documents/MatcapMakerV2/output/ and projects/
        docs = Path(os.path.expanduser("~")) / "Documents"
        self.base_dir = docs / "MatcapMakerV2"
        self.output_dir = self.base_dir / "output"
        self.projects_dir = self.base_dir / "projects"
        
        self._ensure_dirs()
        
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
