import json
import logging
from src.layers.base_layer import BaseLayer
from src.layers.light_layer import LightLayer
from src.layers.spot_light_layer import SpotLightLayer
from src.layers.fresnel_layer import FresnelLayer
from src.layers.fresnel_layer import FresnelLayer
from src.layers.noise_layer import NoiseLayer
from src.layers.image_layer import ImageLayer

class ProjectIO:
    APP_VERSION = "3.0"
    
    # Registry of available layer classes
    # Key: Class Name string, Value: Class Type
    LAYER_REGISTRY = {
        "BaseLayer": BaseLayer,
        "LightLayer": LightLayer,
        "SpotLightLayer": SpotLightLayer,
        "FresnelLayer": FresnelLayer,
        "FresnelLayer": FresnelLayer,
        "NoiseLayer": NoiseLayer,
        "ImageLayer": ImageLayer
    }

    @staticmethod
    def save_project(file_path, layer_stack):
        """Save layer stack to JSON file"""
        try:
            layers_data = []
            for layer in layer_stack:
                layers_data.append(layer.to_dict())
                
            project_data = {
                "app_version": ProjectIO.APP_VERSION,
                "layers": layers_data
            }
            
            with open(file_path, 'w') as f:
                json.dump(project_data, f, indent=4)
                
            print(f"Project saved to {file_path}")
            return True
        except Exception as e:
            print(f"Failed to save project: {e}")
            return False

    @staticmethod
    def load_project(file_path, layer_stack):
        """Load layer stack from JSON file"""
        try:
            with open(file_path, 'r') as f:
                project_data = json.load(f)
                
            # Clear existing layers (except maybe Base Layer? No, full replace)
            # Actually Main Window needs to handle the clear + rebuild logic to refresh UI properly
            # But the stack modification can happen here.
            
            new_layers = []
            
            layout_data_list = project_data.get("layers", [])
            for layer_data in layout_data_list:
                type_name = layer_data.get("type", "")
                
                if type_name in ProjectIO.LAYER_REGISTRY:
                    # Instantiate
                    layer_class = ProjectIO.LAYER_REGISTRY[type_name]
                    layer = layer_class()
                    
                    # Restore parameters
                    layer.from_dict(layer_data)
                    new_layers.append(layer)
                else:
                    print(f"Warning: Unknown layer type '{type_name}'. Skipped.")
            
            # If successful, replace stack contents
            # We clear the list first (but keeping the instance ref if meaningful, though LayerStack just uses a list)
            # To be safe, we should probably add a clear() method to LayerStack
            
            return new_layers # Return list, caller handles stack update
            
        except Exception as e:
            print(f"Failed to load project: {e}")
            return None
