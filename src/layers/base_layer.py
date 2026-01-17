from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np
import math
from src.layers.interface import LayerInterface

class BaseLayer(LayerInterface):
    def __init__(self):
        super().__init__()
        self.name = "Base Layer"
        self.base_color = [1.0, 0.0, 0.0] # Red default
        self.shader_program = None
        self.VAO = None
        self.VBO = None
        self.EBO = None
        self.index_count = 0
        
        # Properties
        self.preview_mode = "Standard" # "Standard", "With Normal Map"
        # Default Normal Map
        from src.core.utils import get_resource_path
        self.normal_map_path = get_resource_path("res/texture/test_leather.jpg")
        
        # Normal Map Options
        self.normal_strength = 1.0 
        self.normal_scale = 1.0
        self.normal_offset = [0.0, 0.0]
        
        # Internal
        self._normal_map_id = None
        self._loaded_normal_path = None

    def initialize(self):
        # 1. Compile Shaders via ResourceManager
        from src.core.resource_manager import ResourceManager
        self.shader_program = ResourceManager().get_shader("src/shaders/layer_base.vert", "src/shaders/layer_base.frag")
        
        if not self.shader_program:
            print("Failed to load BaseLayer shaders")
            return



        # 2. Setup Geometry
        self._setup_geometry()
        
    def render(self):
        if not self.shader_program or not self.enabled:
            return

        glUseProgram(self.shader_program)

        # Update Uniforms
        loc = glGetUniformLocation(self.shader_program, "baseColor")
        glUniform3f(loc, *self.base_color)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    def set_color(self, r, g, b):
        self.base_color = [r, g, b]




