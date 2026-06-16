import math
import numpy as np
from OpenGL.GL import *
from src.layers.interface import LayerInterface

MAX_STOPS = 8

class GradientLayer(LayerInterface):
    def __init__(self):
        super().__init__()
        self.name = "Gradient"

        self.gradient_stops = [
            {"position": 0.0, "color": [0.0, 0.0, 0.0]},
            {"position": 1.0, "color": [1.0, 1.0, 1.0]},
        ]
        self.angle = 90.0          # degrees; 90 = bottom→top (Y+), 270 = top→bottom
        self.gradient_type = "Linear"  # "Linear" or "Radial"

    def initialize(self):
        from src.core.resource_manager import ResourceManager
        self.shader_program = ResourceManager().get_shader(
            "src/shaders/layer_base.vert",
            "src/shaders/layer_gradient.frag"
        )
        self._setup_geometry()

    def render(self):
        if not self.shader_program or not self.enabled:
            return

        glUseProgram(self.shader_program)

        # Sort stops by position and clamp to MAX_STOPS
        stops = sorted(self.gradient_stops, key=lambda s: s["position"])
        num_stops = min(len(stops), MAX_STOPS)

        positions = np.zeros(MAX_STOPS, dtype=np.float32)
        colors = np.zeros((MAX_STOPS, 3), dtype=np.float32)
        for i in range(num_stops):
            positions[i] = stops[i]["position"]
            colors[i] = stops[i]["color"]

        glUniform1i(self._uloc("uNumStops"), num_stops)
        glUniform1fv(self._uloc("uStopPositions"), MAX_STOPS, positions)
        glUniform3fv(self._uloc("uStopColors"), MAX_STOPS, colors)
        glUniform1f(self._uloc("uAngle"), math.radians(self.angle))
        glUniform1i(self._uloc("uGradientType"),
                    0 if self.gradient_type == "Linear" else 1)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    # Serialization is handled reflectively by LayerSerializer:
    # gradient_stops / angle / gradient_type are plain public attributes.
