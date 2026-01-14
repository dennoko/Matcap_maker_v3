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
        # Vertex Shader (Load shared base shader with TBN support)
        vertex_src = self._load_shader("src/shaders/layer_base.vert")
        
        # Fragment Shader
        fragment_src = """#version 330 core
        out vec4 FragColor;
        in vec3 Normal;
        in vec3 FragPos; 
        in vec2 TexCoords;
        in mat3 TBN;
        
        uniform sampler2D imageTexture;
        uniform int mappingMode; // 0=Spherical, 1=Planar
        uniform float scale;
        uniform float rotation;
        uniform vec2 offset;
        uniform float opacity;
        
        uniform bool useNormalMap;
        uniform sampler2D normalMap;
        
        #define PI 3.14159265359
        
        vec3 getNormal() {
            if (useNormalMap && FragPos.x > 0.0) {
                vec3 normal = texture(normalMap, TexCoords).rgb;
                normal = normal * 2.0 - 1.0;
                return normalize(TBN * normal);
            }
            return normalize(Normal);
        }
        
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
                // Spherical Mapping (Matcap)
                // Use perturbed normal!
                vec3 n = getNormal();
                
                // Matcap Mapping:
                // View Space Normal?
                // We assume View Dir is fixed -Z (0,0,-1) in local space?
                // Camera looks down -Z.
                // Standard Matcap: UV = N.xy * 0.5 + 0.5
                // This assumes N is in View Space.
                // Our Normal is in... World Space (Object Space since static camera).
                // If Camera is fixed, World Space == View Space (roughly).
                
                uv = n.xy * 0.5 + 0.5;
                
            } else {
                // Planar Mapping
                vec2 clipPos = FragPos.xy; 
                uv = clipPos * 0.5 + 0.5;
            }
            
            // Apply Offset (Inverse translation to move image)
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
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthFunc(GL_LESS)
        glDepthMask(GL_TRUE)

    def _load_shader(self, path):
        with open(path, 'r', encoding="utf-8") as f: return f.read()


