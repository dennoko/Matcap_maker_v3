
import sys
import os
import json
import unittest
from PySide6.QtWidgets import QApplication

# Mock OpenGL Context for Headless
from src.core.project_io import ProjectIO
from src.layers.base_layer import BaseLayer
from src.layers.spot_light_layer import SpotLightLayer

class TestProjectIO(unittest.TestCase):
    def test_serialization(self):
        # Create Dummy Layers
        l1 = BaseLayer()
        l1.base_color = [0.1, 0.2, 0.3]
        
        l2 = SpotLightLayer()
        l2.intensity = 0.5
        l2.position = [1.0, 2.0, 3.0]
        l2.cone_angle = 60.0 # Standard
        
        # Test to_dict
        d1 = l1.to_dict()
        self.assertEqual(d1["type"], "BaseLayer")
        self.assertEqual(d1["params"]["base_color"], [0.1, 0.2, 0.3])
        
        d2 = l2.to_dict()
        self.assertEqual(d2["type"], "SpotLightLayer")
        self.assertEqual(d2["params"]["intensity"], 0.5)
        self.assertEqual(d2["params"]["position"], [1.0, 2.0, 3.0])
        
    def test_save_load_cycle(self):
        filename = "test_project.json"
        
        # Stack
        layers = []
        l1 = BaseLayer()
        l1.name = "Custom Base"
        layers.append(l1)
        
        l2 = SpotLightLayer()
        l2.name = "My Spot"
        layers.append(l2)
        
        # Save
        ProjectIO.save_project(filename, layers)
        
        # Load
        loaded_layers = ProjectIO.load_project(filename, None)
        
        self.assertEqual(len(loaded_layers), 2)
        self.assertEqual(loaded_layers[0].name, "Custom Base")
        self.assertEqual(loaded_layers[0].__class__.__name__, "BaseLayer")
        
        self.assertEqual(loaded_layers[1].name, "My Spot")
        self.assertEqual(loaded_layers[1].__class__.__name__, "SpotLightLayer")
        
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)
            
    def test_robustness_unknown_param(self):
        # Create a fake JSON with unknown params
        data = {
            "app_version": "3.0",
            "layers": [
                {
                    "type": "BaseLayer",
                    "params": {
                        "base_color": [1,1,1],
                        "future_param_xyz": 999
                    }
                }
            ]
        }
        
        filename = "test_robust.json"
        with open(filename, 'w') as f:
            json.dump(data, f)
            
        # Load should succeed and just print warning
        loaded = ProjectIO.load_project(filename, None)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].base_color, [1,1,1])
        # Should not have the new attr (or maybe introspection ignores it?)
        self.assertFalse(hasattr(loaded[0], "future_param_xyz"))
        
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == '__main__':
    # Need app for some potential signal stuff (though we are testing core logic mostly)
    # app = QApplication(sys.argv) 
    unittest.main()
