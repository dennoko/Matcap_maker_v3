from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np
from src.layers.interface import LayerInterface

class SpotLightLayer(LayerInterface):
    def __init__(self):
        super().__init__()
        self.name = "Spot Light"
        self.blend_mode = "Add"
        self.shader_program = None
        self.VAO = None
        self.index_count = 0
        
        # Params
        self.direction = [0.0, 0.0, 1.0] 
        self.color = [1.0, 1.0, 1.0]
        self.intensity = 1.0
        self.range = 0.2    # Size of spot (0.0 to 1.0 approx) -> maps to cutoff
        self.blur = 0.1     # Softness
        
        # New Params for shape
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.rotation = 0.0

    def initialize(self):
        from src.core.resource_manager import ResourceManager
        self.shader_program = ResourceManager().get_shader("src/shaders/layer_base.vert", "src/shaders/layer_spot.frag")


        # Generate Geometry
        self._setup_geometry()
        
    def render(self):
        if not self.shader_program or not self.enabled:
            return

        self.setup_blend_func() 
        glDepthFunc(GL_LEQUAL)
        glDepthMask(GL_FALSE)
        
        # Determine uniforms based on blend mode
        u_color = self.color
        u_intensity = self.intensity

        if self.blend_mode == "Multiply":
            # Special handling for Multiply
            u_intensity = 1.0 
            if self.intensity <= 1.0:
                u_color = [(1.0 - self.intensity) + c * self.intensity for c in self.color]
            else:
                if self.intensity > 0:
                    u_color = [c / self.intensity for c in self.color]
        
        glUseProgram(self.shader_program)
        glUniform3f(glGetUniformLocation(self.shader_program, "lightDir"), *self.direction)
        glUniform3f(glGetUniformLocation(self.shader_program, "lightColor"), *u_color)
        glUniform1f(glGetUniformLocation(self.shader_program, "intensity"), u_intensity)
        glUniform1f(glGetUniformLocation(self.shader_program, "range"), self.range)
        glUniform1f(glGetUniformLocation(self.shader_program, "blur"), self.blur)
        
        # New Params
        glUniform1f(glGetUniformLocation(self.shader_program, "scaleX"), self.scale_x)
        glUniform1f(glGetUniformLocation(self.shader_program, "scaleY"), self.scale_y)
        glUniform1f(glGetUniformLocation(self.shader_program, "rotation"), self.rotation)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthFunc(GL_LESS)
        glDepthMask(GL_TRUE)




