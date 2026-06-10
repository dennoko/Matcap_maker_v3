from OpenGL.GL import *
from src.layers.interface import LayerInterface

class SpotLightLayer(LayerInterface):
    def __init__(self):
        super().__init__()
        self.name = "Spot Light"
        self.blend_mode = "Add"

        # Params
        self.direction = [0.0, 0.0, 1.0]
        self.color = [1.0, 1.0, 1.0]
        self.intensity = 1.0
        self.range = 0.2    # Size of spot (0.0 to 1.0 approx) -> maps to cutoff
        self.blur = 0.1     # Softness

        # Shape params
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.rotation = 0.0

    def initialize(self):
        from src.core.resource_manager import ResourceManager
        self.shader_program = ResourceManager().get_shader("src/shaders/layer_base.vert", "src/shaders/layer_spot.frag")
        self._setup_geometry()

    def render(self):
        if not self.shader_program or not self.enabled:
            return

        # Multiply mode expects a "tint" color: fold intensity into the color
        # so 0 intensity = white (no darkening) and 1 = full color.
        u_color = self.color
        u_intensity = self.intensity
        if self.blend_mode == "Multiply":
            u_intensity = 1.0
            if self.intensity <= 1.0:
                u_color = [(1.0 - self.intensity) + c * self.intensity for c in self.color]
            elif self.intensity > 0:
                u_color = [c / self.intensity for c in self.color]

        glUseProgram(self.shader_program)
        glUniform3f(self._uloc("lightDir"), *self.direction)
        glUniform3f(self._uloc("lightColor"), *u_color)
        glUniform1f(self._uloc("intensity"), u_intensity)
        glUniform1f(self._uloc("range"), self.range)
        glUniform1f(self._uloc("blur"), self.blur)
        glUniform1f(self._uloc("scaleX"), self.scale_x)
        glUniform1f(self._uloc("scaleY"), self.scale_y)
        glUniform1f(self._uloc("rotation"), self.rotation)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
