import sys
import os
import json
import shutil
import unittest

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.project_io import ProjectIO
from src.core.layer_serializer import LayerSerializer
from src.layers.base_layer import BaseLayer
from src.layers.spot_light_layer import SpotLightLayer
from src.layers.gradient_layer import GradientLayer
import src.layers  # Register layers


class TestProjectIO(unittest.TestCase):
    def test_serialization(self):
        # Create Dummy Layers
        l1 = BaseLayer()
        l1.base_color = [0.1, 0.2, 0.3]

        l2 = SpotLightLayer()
        l2.intensity = 0.5
        l2.direction = [1.0, 2.0, 3.0]
        l2.opacity = 0.75

        d1 = LayerSerializer.to_dict(l1)
        self.assertEqual(d1["type"], "BaseLayer")
        self.assertEqual(d1["params"]["base_color"], [0.1, 0.2, 0.3])
        # Internal attributes must not leak into params
        for hidden in ("shader_program", "VAO", "index_count"):
            self.assertNotIn(hidden, d1["params"])

        d2 = LayerSerializer.to_dict(l2)
        self.assertEqual(d2["type"], "SpotLightLayer")
        self.assertEqual(d2["params"]["intensity"], 0.5)
        self.assertEqual(d2["params"]["direction"], [1.0, 2.0, 3.0])
        self.assertEqual(d2["opacity"], 0.75)

        # Round trip restores opacity (top-level field)
        l3 = SpotLightLayer()
        LayerSerializer.from_dict(l3, d2)
        self.assertEqual(l3.opacity, 0.75)
        self.assertEqual(l3.intensity, 0.5)

    def test_gradient_layer_roundtrip(self):
        g = GradientLayer()
        g.gradient_stops = [
            {"position": 0.0, "color": [0.5, 0.0, 0.0]},
            {"position": 0.4, "color": [0.0, 0.5, 0.0]},
            {"position": 1.0, "color": [0.0, 0.0, 0.5]},
        ]
        g.angle = 135.0
        g.gradient_type = "Radial"

        data = LayerSerializer.to_dict(g)
        self.assertEqual(data["type"], "GradientLayer")

        g2 = GradientLayer()
        LayerSerializer.from_dict(g2, data)
        self.assertEqual(g2.gradient_stops, g.gradient_stops)
        self.assertEqual(g2.angle, 135.0)
        self.assertEqual(g2.gradient_type, "Radial")

    def test_save_load_cycle(self):
        filename = "test_project.json"

        layers = []
        l1 = BaseLayer()
        l1.name = "Custom Base"
        layers.append(l1)

        l2 = SpotLightLayer()
        l2.name = "My Spot"
        layers.append(l2)

        # Save (creates a "test_project" directory bundle)
        ok, errors = ProjectIO.save_project(filename, layers)
        self.assertTrue(ok)

        project_json = os.path.join("test_project", "project.json")
        self.assertTrue(os.path.exists(project_json))

        # Load
        loaded_layers = ProjectIO.load_project(project_json, None)

        self.assertEqual(len(loaded_layers), 2)
        self.assertEqual(loaded_layers[0].name, "Custom Base")
        self.assertEqual(loaded_layers[0].__class__.__name__, "BaseLayer")

        self.assertEqual(loaded_layers[1].name, "My Spot")
        self.assertEqual(loaded_layers[1].__class__.__name__, "SpotLightLayer")

        # Clean up
        shutil.rmtree("test_project", ignore_errors=True)

    def test_robustness_unknown_param(self):
        # Create a fake JSON with unknown params
        data = {
            "app_version": "3.0",
            "layers": [
                {
                    "type": "BaseLayer",
                    "params": {
                        "base_color": [1, 1, 1],
                        "future_param_xyz": 999
                    }
                },
                {
                    "type": "FutureUnknownLayer",
                    "params": {}
                }
            ]
        }

        filename = "test_robust.json"
        with open(filename, 'w') as f:
            json.dump(data, f)

        # Load should succeed: unknown params ignored, unknown layers skipped
        loaded = ProjectIO.load_project(filename, None)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].base_color, [1, 1, 1])
        self.assertFalse(hasattr(loaded[0], "future_param_xyz"))

        if os.path.exists(filename):
            os.remove(filename)


if __name__ == '__main__':
    unittest.main()
