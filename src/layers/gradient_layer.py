import math
import numpy as np
from OpenGL.GL import *
from src.layers.interface import LayerInterface

class GradientLayer(LayerInterface):
    def __init__(self):
        super().__init__()
        self.name = "Gradient"
        self.blend_mode = "Normal"
        self.shader_program = None
        self.VAO = None
        self.index_count = 0

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

        self.setup_blend_func()
        glDepthFunc(GL_LEQUAL)
        glDepthMask(GL_FALSE)

        glUseProgram(self.shader_program)

        # Sort stops by position and clamp to MAX_STOPS
        stops = sorted(self.gradient_stops, key=lambda s: s["position"])
        num_stops = min(len(stops), 8)

        positions = np.zeros(8, dtype=np.float32)
        colors = np.zeros((8, 3), dtype=np.float32)
        for i in range(num_stops):
            positions[i] = stops[i]["position"]
            colors[i] = stops[i]["color"]

        glUniform1i(glGetUniformLocation(self.shader_program, "uNumStops"), num_stops)
        glUniform1fv(glGetUniformLocation(self.shader_program, "uStopPositions"), 8, positions)
        glUniform3fv(glGetUniformLocation(self.shader_program, "uStopColors"), 8, colors)
        glUniform1f(glGetUniformLocation(self.shader_program, "uAngle"), math.radians(self.angle))
        glUniform1i(glGetUniformLocation(self.shader_program, "uGradientType"),
                    0 if self.gradient_type == "Linear" else 1)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthFunc(GL_LESS)
        glDepthMask(GL_TRUE)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "gradient_stops": [
                {"position": s["position"], "color": list(s["color"])}
                for s in self.gradient_stops
            ],
            "angle": self.angle,
            "gradient_type": self.gradient_type,
        })
        return data

    def from_dict(self, data):
        super().from_dict(data)
        self.gradient_stops = data.get("gradient_stops", [
            {"position": 0.0, "color": [0.0, 0.0, 0.0]},
            {"position": 1.0, "color": [1.0, 1.0, 1.0]},
        ])
        self.angle = data.get("angle", 90.0)
        self.gradient_type = data.get("gradient_type", "Linear")
