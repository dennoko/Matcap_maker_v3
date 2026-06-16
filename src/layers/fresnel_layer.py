from OpenGL.GL import *
from src.layers.interface import LayerInterface

class FresnelLayer(LayerInterface):
    def __init__(self):
        super().__init__()
        self.name = "Fresnel / Rim"
        self.blend_mode = "Add"

        # Params
        self.color = [0.0, 1.0, 1.0] # Default Cyan to see effect clearly
        self.intensity = 1.0
        self.power = 5.0   # Higher exponent for sharper rim
        self.bias = 0.0    # Offset

        # For Fresnel, direction usually means View direction which is fixed [0,0,1] for matcaps

    def initialize(self):
        from src.core.resource_manager import ResourceManager
        self.shader_program = ResourceManager().get_shader("src/shaders/layer_base.vert", "src/shaders/layer_fresnel.frag")
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
        glUniform3f(self._uloc("color"), *u_color)
        glUniform1f(self._uloc("intensity"), u_intensity)
        glUniform1f(self._uloc("power"), self.power)
        glUniform1f(self._uloc("bias"), self.bias)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
