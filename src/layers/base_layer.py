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
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.normal_map_path = os.path.join(base_dir, "res", "texture", "Leather034D_4K_NormalDX.jpg")
        
        # Normal Map Options
        self.normal_strength = 1.0 
        self.normal_scale = 1.0
        self.normal_offset = [0.0, 0.0]
        
        # Internal
        self._normal_map_id = None
        self._loaded_normal_path = None

    def initialize(self):
        # 1. Compile Shaders
        vertex_src = self._load_shader("src/shaders/layer_base.vert")
        fragment_src = self._load_shader("src/shaders/layer_base.frag")
        
        try:
            vertex_shader = shaders.compileShader(vertex_src, GL_VERTEX_SHADER)
            fragment_shader = shaders.compileShader(fragment_src, GL_FRAGMENT_SHADER)
            self.shader_program = shaders.compileProgram(vertex_shader, fragment_shader)
        except Exception as e:
            print(f"Shader compilation error: {e}")
            return

        except Exception as e:
            print(f"Shader compilation error: {e}")
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

    def _load_shader(self, path):
        with open(path, 'r', encoding="utf-8") as f:
            return f.read()


