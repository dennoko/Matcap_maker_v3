import json
import os
from src.core.settings import Settings
from src.core.utils import get_resource_path

class Translator:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Translator, cls).__new__(cls)
            cls._instance._init()
        return cls._instance
        
    def _init(self):
        self._translations = {}
        self.load_language()
        
    def load_language(self):
        lang = Settings().language
        # Path to locales
        # res/locales/{lang}.json
        
        path = get_resource_path(f"res/locales/{lang}.json")
        
        # Fallback to en if requested lang missing (and not en)
        if not os.path.exists(path) and lang != "en":
             print(f"Language file not found: {path}. Falling back to 'en'.")
             path = get_resource_path("res/locales/en.json")
             
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self._translations = json.load(f)
                print(f"Loaded language: {lang}")
            except Exception as e:
                print(f"Failed to load language {lang}: {e}")
                self._translations = {}
        else:
             print(f"Language file not found: {path}")
             # If even EN missing, we just return keys
             self._translations = {}

    def tr(self, key, **kwargs):
        """
        Get translated string.
        Optional kwargs for formatting, e.g. tr("prop.header", name="Layer 1")
        """
        text = self._translations.get(key, key) # Return key if not found
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception:
                # Return unformatted if error (e.g. format string mismatch)
                pass 
        return text

# Global helper for easy access
def tr(key, **kwargs):
    return Translator().tr(key, **kwargs)
