import copy
import logging

class LayerSerializer:
    @staticmethod
    def to_dict(layer):
        """Serialize layer state to dictionary"""
        params = {}
        # Attributes to exclude from 'params' because they are handled in top-level fields
        # or are runtime/internal properties.
        excluded = [
            "shader_program", "VAO", "VBO", "EBO", 
            "index_count", "name", "enabled", "blend_mode", 
            "texture_id", "_texture_loaded_path", "preview_mode",
            "opacity"
        ]
        
        # Also exclude properties starting with _
        
        for key, value in layer.__dict__.items():
            if key.startswith('_'): continue
            if key in excluded:
                continue
            
            try:
                params[key] = copy.deepcopy(value)
            except Exception:
                params[key] = value
            
        return {
            "type": layer.__class__.__name__,
            "name": layer.name,
            "enabled": layer.enabled,
            "blend_mode": layer.blend_mode,
            "opacity": getattr(layer, "opacity", 1.0),
            "params": params
        }

    @staticmethod
    def from_dict(layer, data):
        """Restore layer state from dictionary"""
        layer.name = data.get("name", layer.name)
        layer.enabled = data.get("enabled", layer.enabled)
        layer.blend_mode = data.get("blend_mode", layer.blend_mode)
        layer.opacity = data.get("opacity", getattr(layer, "opacity", 1.0))
        
        if "params" in data:
            for key, value in data["params"].items():
                if key == "preview_mode": continue # Legacy skip
                
                if hasattr(layer, key):
                     setattr(layer, key, value)
                else:
                    # logging.warning(f"Unknown parameter '{key}' for layer '{layer.name}'")
                    pass
