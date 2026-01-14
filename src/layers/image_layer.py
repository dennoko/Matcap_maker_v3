from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np
from PIL import Image
from src.layers.interface import LayerInterface

class ImageLayer(LayerInterface):
    def __init__(self):
        super().__init__()
        self.name = "Image Layer"
        self.blend_mode = "Normal" # Default to Normal for decals/textures
        self.opacity = 1.0 # Add explicit opacity (handled by base/blend func usually, but good to have)
        
        self.shader_program = None
        self.VAO = None
        self.index_count = 0
        self.texture_id = None
        
        # Params
        self.image_path = ""
        self.mapping_mode = "Spherical" # "Spherical", "Planar"
        self.scale = 1.0
        self.rotation = 0.0 # Degrees
        self.offset = [0.0, 0.0] # [x, y]
        
        # Internal state
        self._texture_loaded_path = None # To track reloading necessity
        
    def initialize(self):
        # Vertex Shader
        vertex_src = """#version 330 core
        layout (location = 0) in vec3 aPos;
        layout (location = 1) in vec3 aNormal;
        layout (location = 2) in vec2 aTexCoords;

        out vec3 Normal;
        out vec3 FragPos;
        out vec2 TexCoords;

        void main()
        {
            FragPos = aPos;
            Normal = aNormal;
            TexCoords = aTexCoords;
            gl_Position = vec4(aPos, 1.0);
        }
        """
        
        # Fragment Shader
        fragment_src = """#version 330 core
        out vec4 FragColor;
        in vec3 Normal;
        in vec3 FragPos; 
        in vec2 TexCoords;
        
        uniform sampler2D imageTexture;
        uniform int mappingMode; // 0=Spherical, 1=Planar
        uniform float scale;
        uniform float rotation;
        uniform vec2 offset;
        uniform float opacity;
        
        #define PI 3.14159265359
        
        vec2 rotateUV(vec2 uv, float angle)
        {
            uv -= 0.5;
            float s = sin(angle);
            float c = cos(angle);
            mat2 rot = mat2(c, -s, s, c);
            uv = rot * uv;
            uv += 0.5;
            return uv;
        }

        void main()
        {
            vec2 uv;
            
            if (mappingMode == 0) {
                // Spherical Mapping
                uv = TexCoords;
            } else {
                // Planar Mapping
                vec2 clipPos = FragPos.xy; 
                uv = clipPos * 0.5 + 0.5;
            }
            
            // Apply Offset (Inverse translation to move image)
            // Move image by offset => Coordinate system by -offset
            uv -= offset;
            
            // Apply Rotation
            uv = rotateUV(uv, radians(rotation));
            
            // Apply Scale
            uv = (uv - 0.5) / scale + 0.5;
            
            vec4 texColor = texture(imageTexture, uv);
            
            FragColor = vec4(texColor.rgb, texColor.a * opacity);
        }
        """
        
        try:
            vertex_shader = shaders.compileShader(vertex_src, GL_VERTEX_SHADER)
            fragment_shader = shaders.compileShader(fragment_src, GL_FRAGMENT_SHADER)
            self.shader_program = shaders.compileProgram(vertex_shader, fragment_shader)
        except Exception as e:
            print(f"ImageLayer Shader Error: {e}")
            return

        # Geometry
        self._setup_geometry()
        
        # Load Texture if needed
        if self.image_path:
            self.load_texture(self.image_path)
            
    def load_texture(self, path):
        if not path:
            return
            
        try:
            img = Image.open(path)
            img = img.transpose(Image.FLIP_TOP_BOTTOM) # OpenGL origin is bottom-left
            img_data = img.convert("RGBA").tobytes()
            w, h = img.size
            
            if self.texture_id:
                glDeleteTextures([self.texture_id])
                
            self.texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            
            # Set params
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
            glGenerateMipmap(GL_TEXTURE_2D)
            
            glBindTexture(GL_TEXTURE_2D, 0)
            
            self.image_path = path
            self._texture_loaded_path = path
            print(f"Texture loaded: {path}")
            
        except Exception as e:
            print(f"Failed to load texture {path}: {e}")

    def render(self):
        if not self.shader_program or not self.enabled or not self.texture_id:
            return

        if self.image_path and self.image_path != self._texture_loaded_path:
            self.load_texture(self.image_path)

        self.setup_blend_func() 
        glDepthFunc(GL_LEQUAL)
        glDepthMask(GL_FALSE)
        
        glUseProgram(self.shader_program)
        
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glUniform1i(glGetUniformLocation(self.shader_program, "imageTexture"), 0)
        
        mode_int = 0 if self.mapping_mode == "Spherical" else 1
        glUniform1i(glGetUniformLocation(self.shader_program, "mappingMode"), mode_int)
        
        glUniform1f(glGetUniformLocation(self.shader_program, "scale"), self.scale)
        glUniform1f(glGetUniformLocation(self.shader_program, "rotation"), self.rotation)
        glUniform2f(glGetUniformLocation(self.shader_program, "offset"), *self.offset)
        glUniform1f(glGetUniformLocation(self.shader_program, "opacity"), self.opacity)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthFunc(GL_LESS)
        glDepthMask(GL_TRUE)

    def _setup_geometry(self):
        # Shared sphere generation (copied for now)
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
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(6 * 4))
        glBindVertexArray(0)

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
