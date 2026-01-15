import json
import logging
from src.layers.base_layer import BaseLayer
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
        "SpotLightLayer": SpotLightLayer,
        "FresnelLayer": FresnelLayer,
        "FresnelLayer": FresnelLayer,
        "NoiseLayer": NoiseLayer,
        "ImageLayer": ImageLayer
    }

    @staticmethod
    def save_project(file_path, layer_stack):
        """
        Save project as a directory bundle.
        file_path: The user selected path (e.g. .../MyProject.json or .../MyProject)
        We will create a directory at that path (stripping enum extension if needed)
        and save 'project.json' inside it, along with 'assets/'.
        """
        import os
        import shutil
        import json
        from pathlib import Path
        
        # Determine Project Directory
        # If user picked "foo.json", project dir is "foo".
        path_obj = Path(file_path)
        if path_obj.suffix == '.json':
            project_dir = path_obj.parent / path_obj.stem
        else:
            project_dir = path_obj
            
        assets_dir = project_dir / "assets"
        
        # Create Dirs
        try:
            project_dir.mkdir(parents=True, exist_ok=True)
            assets_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"Failed to create project directory: {e}")
            return False, [str(e)]
            
        errors = []
        data = []
        for layer in layer_stack:
            layer_data = layer.to_dict()
            
            
            # Asset Management for ImageLayer
            if "params" in layer_data and "image_path" in layer_data["params"]:
                src_path = layer_data["params"]["image_path"]
                # print(f"Processing Image Asset: {src_path}") # Debug
                if src_path and os.path.exists(src_path):
                    try:
                        filename = os.path.basename(src_path)
                        dst_path = assets_dir / filename
                        shutil.copy2(src_path, dst_path)
                        layer_data["params"]["image_path"] = f"./assets/{filename}"
                        # print(f"Copied to {dst_path}") # Debug
                    except Exception as e:
                        errors.append(f"Failed to copy {filename}: {e}")
                        print(f"Copy Error: {e}")
            
            data.append(layer_data)
            
        # Wrap in project dictionary
        project_data = {
            "app_version": ProjectIO.APP_VERSION,
            "layers": data
        }
            
        # Write JSON
        target_json = project_dir / "project.json"
        try:
            with open(target_json, 'w') as f:
                json.dump(project_data, f, indent=4)
        except Exception as e:
            return False, [f"Failed to write JSON: {e}"]
            
        print(f"Project saved to {target_json}")
        return True, errors

    @staticmethod
    def load_project(file_path, layer_stack):
        import json
        import os
        from pathlib import Path
        
        try:
            path_obj = Path(file_path)
            project_dir = path_obj.parent
            
            with open(file_path, 'r') as f:
                project_data = json.load(f)
                
            new_layers = []
            
            layout_data_list = project_data.get("layers", [])
            for layer_data in layout_data_list:
                type_name = layer_data.get("type", "")
                
                if type_name in ProjectIO.LAYER_REGISTRY:
                    # Instantiate
                    layer_class = ProjectIO.LAYER_REGISTRY[type_name]
                    layer = layer_class()
                    
                    # Resolve relative paths BEFORE from_dict
                    if "params" in layer_data and "image_path" in layer_data["params"]:
                        p = layer_data["params"]["image_path"]
                        if p and p.startswith("./"):
                            # Resolve relative to project_dir
                            # ./assets/foo.png -> project_dir/assets/foo.png
                            # Use forward slashes or Path
                            abs_p = (project_dir / p).resolve()
                            layer_data["params"]["image_path"] = str(abs_p)

                    # Restore parameters
                    layer.from_dict(layer_data)
                    new_layers.append(layer)
                else:
                    print(f"Warning: Unknown layer type '{type_name}'. Skipped.")
            
            return new_layers # Return list, caller handles stack update
            
        except Exception as e:
            print(f"Failed to load project: {e}")
            return None
