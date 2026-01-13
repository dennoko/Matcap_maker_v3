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

    def initialize(self):
        vertex_src = self._load_shader("src/shaders/layer_base.vert")
        
        fragment_src = """
        #version 330 core
        out vec4 FragColor;
        in vec3 Normal;
        in vec3 FragPos;
        
        uniform vec3 lightDir;
        uniform vec3 lightColor;
        uniform float intensity;
        uniform float range;
        uniform float blur;
        
        void main()
        {
            vec3 norm = normalize(Normal);
            // Invert lightDir for calculation (direction TO light)
            vec3 lDir = normalize(-lightDir); 
            
            float ndotl = dot(norm, lDir);
            
            // Map range to cutoff (larger range = smaller cutoff req)
            // range 0.0 -> cutoff 1.0 (strict)
            // range 1.0 -> cutoff 0.0 (wide)
            float cutoff = 1.0 - range; 
            
            // Improved Blur Logic
            // We want the fade to happen OUTSIDE the cutoff or INSIDE?
            // Usually blur softens the edge effectively making the spot slightly larger/smaller.
            // Let's define: inner_cutoff = cutoff, outer_cutoff = cutoff - blur
            // But to avoid artifacts when blur is large, we clamp.
            
            float epsilon = blur + 0.0001;
            float spot = smoothstep(cutoff - epsilon, cutoff + epsilon, ndotl);
            
            vec3 finalColor = spot * lightColor * intensity;
            
            // Output Alpha = spot (geometric coverage)
            FragColor = vec4(finalColor, spot); 
        }
        """
        
        try:
            vertex_shader = shaders.compileShader(vertex_src, GL_VERTEX_SHADER)
            fragment_shader = shaders.compileShader(fragment_src, GL_FRAGMENT_SHADER)
            self.shader_program = shaders.compileProgram(vertex_shader, fragment_shader)
        except Exception as e:
            print(f"SpotLightLayer Shader Error: {e}")
            return

        # Generate Geometry (Shared sphere)
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
        
        glBindVertexArray(0)
        
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
            # Special handling for Multiply to make Intensity intuitive (0=No effect, High=Darker)
            u_intensity = 1.0 # Bake intensity into color
            if self.intensity <= 1.0:
                # Interpolate White -> Color
                u_color = [(1.0 - self.intensity) + c * self.intensity for c in self.color]
            else:
                # Interpolate Color -> Black
                if self.intensity > 0:
                    u_color = [c / self.intensity for c in self.color]
        
        glUseProgram(self.shader_program)
        glUniform3f(glGetUniformLocation(self.shader_program, "lightDir"), *self.direction)
        glUniform3f(glGetUniformLocation(self.shader_program, "lightColor"), *u_color)
        glUniform1f(glGetUniformLocation(self.shader_program, "intensity"), u_intensity)
        glUniform1f(glGetUniformLocation(self.shader_program, "range"), self.range)
        glUniform1f(glGetUniformLocation(self.shader_program, "blur"), self.blur)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        
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
