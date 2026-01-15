from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np
from src.layers.interface import LayerInterface

class FresnelLayer(LayerInterface):
    def __init__(self):
        super().__init__()
        self.name = "Fresnel / Rim"
        self.blend_mode = "Add"
        self.shader_program = None
        self.VAO = None
        self.index_count = 0
        
        # Params
        self.color = [0.0, 1.0, 1.0] # Default Cyan to see effect clearly
        self.intensity = 1.0
        self.power = 5.0   # Higher exponent for sharper rim
        self.bias = 0.0    # Offset
        
        # For Fresnel, direction usually means View direction which is fixed [0,0,1] for matcaps
        # But we could allow shifting the "center" if needed. For now fixed.

    def initialize(self):
        # Reuse base geometry logic (Sphere)
        from src.core.resource_manager import ResourceManager
        self.shader_program = ResourceManager().get_shader("src/shaders/layer_base.vert", "src/shaders/layer_fresnel.frag")


        # Generate Geometry
        self._setup_geometry()

    def render(self):
        if not self.shader_program or not self.enabled:
            return

        self.setup_blend_func()
        glDepthFunc(GL_LEQUAL)
        glDepthMask(GL_FALSE)
        
        # Enable Culling for Fresnel to avoid backface rim artifacts
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        
        # Calculate uniforms for Multiply mode if needed
        u_color = self.color
        u_intensity = self.intensity
        if self.blend_mode == "Multiply":
             u_intensity = 1.0
             if self.intensity <= 1.0:
                 u_color = [(1.0 - self.intensity) + c * self.intensity for c in self.color]
             else:
                 if self.intensity > 0:
                     u_color = [c / self.intensity for c in self.color]

        glUseProgram(self.shader_program)
        glUniform3f(glGetUniformLocation(self.shader_program, "color"), *u_color)
        glUniform1f(glGetUniformLocation(self.shader_program, "intensity"), u_intensity)
        glUniform1f(glGetUniformLocation(self.shader_program, "power"), self.power)
        glUniform1f(glGetUniformLocation(self.shader_program, "bias"), self.bias)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthFunc(GL_LESS)
        glDepthMask(GL_TRUE)



