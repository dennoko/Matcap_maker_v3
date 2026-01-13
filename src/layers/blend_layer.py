from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np
from src.layers.interface import LayerInterface

class BlendLayer(LayerInterface):
    def __init__(self):
        super().__init__()
        self.name = "Blend Test Layer"
        self.shader_program = None
        self.VAO = None
        self.index_count = 0
        self.color = [0.0, 1.0, 0.0, 0.5] # Green, 50% opacity

    def initialize(self):
        # We can reuse the same geometry as BaseLayer or generate new.
        # For simplicity, let's copy generator for now or use a shared Geometry Manager later.
        # Minimal duplicate for isolation.
        
        vertex_src = """
        #version 330 core
        layout (location = 0) in vec3 aPos;
        uniform float scale;
        void main() {
            gl_Position = vec4(aPos * scale, 1.0);
        }
        """
        fragment_src = """
        #version 330 core
        out vec4 FragColor;
        uniform vec4 color;
        void main() {
            FragColor = color;
        }
        """
        
        try:
            vs = shaders.compileShader(vertex_src, GL_VERTEX_SHADER)
            fs = shaders.compileShader(fragment_src, GL_FRAGMENT_SHADER)
            self.shader_program = shaders.compileProgram(vs, fs)
        except Exception as e:
            print(f"BlendLayer Shader Error: {e}")
            return

        # Simple Sphere or just a smaller quad? Let's do a sphere to see valid overlap.
        # Reusing generation logic is better but for now just a small internal function or import?
        # Let's import BaseLayer's generator if possible or just use a Quad.
        # A Quad in front of the sphere is enough to test blending.
        
        quad_verts = np.array([
            -0.5, -0.5, 0.0,
             0.5, -0.5, 0.0,
             0.0,  0.5, 0.0
        ], dtype=np.float32)
        
        self.VAO = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        glBindVertexArray(self.VAO)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, quad_verts.nbytes, quad_verts, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3*4, ctypes.c_void_p(0))
        glBindVertexArray(0)
        
    def render(self):
        if not self.shader_program:
            return
            
        glUseProgram(self.shader_program)
        glUniform4f(glGetUniformLocation(self.shader_program, "color"), *self.color)
        glUniform1f(glGetUniformLocation(self.shader_program, "scale"), 1.0)
        
        glBindVertexArray(self.VAO)
        glDrawArrays(GL_TRIANGLES, 0, 3)
        glBindVertexArray(0)
