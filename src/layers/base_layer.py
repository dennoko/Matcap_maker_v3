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

        # 2. Generate Sphere Geometry
        vertices, indices = self._generate_sphere(radius=0.9, stacks=30, sectors=30)
        self.index_count = len(indices)
        
        vertices = np.array(vertices, dtype=np.float32)
        indices = np.array(indices, dtype=np.uint32)

        # 3. Setup VAO/VBO
        self.VAO = glGenVertexArrays(1)
        self.VBO = glGenBuffers(1)
        self.EBO = glGenBuffers(1)

        glBindVertexArray(self.VAO)

        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        # Position (3 floats), Normal (3), TexCoord (2) -> Stride 8 * 4 bytes
        stride = 8 * 4
        
        # Pos (Loc 0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        
        # Normal (Loc 1)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * 4))
        
        # TexCoord (Loc 2)
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(6 * 4))

        glBindVertexArray(0)
        
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
        with open(path, 'r') as f:
            return f.read()

    def _generate_sphere(self, radius, stacks, sectors):
        vertices = []
        indices = []

        for i in range(stacks + 1):
            lat = math.pi * i / stacks
            y = math.cos(lat)
            r_plane = math.sin(lat)
            
            for j in range(sectors + 1):
                lon = 2 * math.pi * j / sectors
                x = r_plane * math.cos(lon)
                z = r_plane * math.sin(lon)
                
                # Pos (x, y, z)
                vx, vy, vz = x * radius, y * radius, z * radius
                
                # Normal (normalized pos for sphere at origin)
                nx, ny, nz = x, y, z
                
                # TexCoord
                u = j / sectors
                v = i / stacks
                
                vertices.extend([vx, vy, vz, nx, ny, nz, u, v])

        for i in range(stacks):
            for j in range(sectors):
                first = (i * (sectors + 1)) + j
                second = first + sectors + 1
                
                indices.extend([first, second, first + 1])
                indices.extend([second, second + 1, first + 1])
                
        return vertices, indices
