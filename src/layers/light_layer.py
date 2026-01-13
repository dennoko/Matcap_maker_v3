from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np
from src.layers.interface import LayerInterface

class LightLayer(LayerInterface):
    def __init__(self):
        super().__init__()
        self.name = "Directional Light"
        self.blend_mode = "Add"
        self.shader_program = None
        self.VAO = None
        self.index_count = 0
        
        # Params
        self.direction = [0.0, 0.0, 1.0] # Looking from camera (-Z ray direction)
        self.color = [1.0, 1.0, 1.0]
        self.intensity = 1.0

    def initialize(self):
        # Vertex Shader (Reuse Base Layer logic or simple pass-through)
        # We need to draw the sphere again to apply lighting on it.
        # Ideally, we share geometry. For now, regenerating to be self-contained.
        vertex_src = self._load_shader("src/shaders/layer_base.vert") # Reuse
        
        fragment_src = """
        #version 330 core
        out vec4 FragColor;
        in vec3 Normal;
        in vec3 FragPos;
        
        uniform vec3 lightDir;
        uniform vec3 lightColor;
        uniform float intensity;
        
        void main()
        {
            vec3 norm = normalize(Normal);
            // Invert lightDir for calculation (direction TO light)
            vec3 lDir = normalize(-lightDir); 
            
            float diff = max(dot(norm, lDir), 0.0);
            vec3 diffuse = diff * lightColor * intensity;
            
            // Output with Alpha = diff (geometric coverage)
            // RGB is already premultiplied by diff (diffuse = diff * color * intensity)
            FragColor = vec4(diffuse, diff); 
        }
        """
        
        try:
            vertex_shader = shaders.compileShader(vertex_src, GL_VERTEX_SHADER)
            fragment_shader = shaders.compileShader(fragment_src, GL_FRAGMENT_SHADER)
            self.shader_program = shaders.compileProgram(vertex_shader, fragment_shader)
        except Exception as e:
            print(f"LightLayer Shader Error: {e}")
            return

        # Generate Geometry (Should be shared in Engine, but locally gen for now)
        vertices, indices = self._generate_sphere(0.9, 30, 30)
        self.index_count = len(indices)
        
        vertices = np.array(vertices, dtype=np.float32)
        indices = np.array(indices, dtype=np.uint32)

        self.VAO = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        ebo = glGenBuffers(1)

        glBindVertexArray(self.VAO)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        stride = 8 * 4
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * 4))
        # No texcoord needed for basic light but data is there
        
        glBindVertexArray(0)
        
    def render(self):
        if not self.shader_program or not self.enabled:
            return

        # Set Blend Mode
        self.setup_blend_func()
        
        # Mulit-pass rendering rules for same geometry:
        # 1. Depth Func needs to be LEQUAL so valid fragments at same depth pass
        # 2. Don't write depth (already written by base)
        glDepthFunc(GL_LEQUAL)
        glDepthMask(GL_FALSE)
        
        glUseProgram(self.shader_program)
        glUniform3f(glGetUniformLocation(self.shader_program, "lightDir"), *self.direction)
        glUniform3f(glGetUniformLocation(self.shader_program, "lightColor"), *self.color)
        glUniform1f(glGetUniformLocation(self.shader_program, "intensity"), self.intensity)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        
        # Reset States
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthFunc(GL_LESS)
        glDepthMask(GL_TRUE)

    def _load_shader(self, path):
        with open(path, 'r') as f: return f.read()

    def _generate_sphere(self, radius, stacks, sectors):
        import math
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
                vertices.extend([x*radius, y*radius, z*radius, x, y, z, j/sectors, i/stacks])
        for i in range(stacks):
            for j in range(sectors):
                first = (i * (sectors + 1)) + j
                second = first + sectors + 1
                indices.extend([first, second, first + 1, second, second + 1, first + 1])
        return vertices, indices
