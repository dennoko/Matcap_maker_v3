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
        self.mapping_mode = "UV" # "UV", "Planar" ("Spherical" omitted)
        self.blend_mode = "Add" # Default changed from Normal to Add per user request
        self.scale = 1.0
        self.rotation = 0.0 # Degrees
        self.offset = [0.0, 0.0] # [x, y]
        self.aspect_ratio = 1.0 # width / height
        
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
        uniform int mappingMode; // 0=UV, 1=Planar
        uniform float scale;
        uniform float rotation;
        uniform vec2 offset;
        uniform float opacity;
        uniform float aspectRatio; // Image Aspect Ratio (w/h)
        
        uniform int previewMode; // 0=Standard, 1=Comparison
        
        uniform bool useNormalMap;
        uniform sampler2D normalMap;
        uniform float normalStrength;
        uniform float normalScale;
        uniform vec2 normalOffset;
        
        #define PI 3.14159265359
        
        vec3 getNormal() {
            if (useNormalMap && FragPos.x > 0.0) {
                vec2 uv = TexCoords * normalScale + normalOffset;
                vec3 normal = texture(normalMap, uv).rgb;
                normal = normal * 2.0 - 1.0;
                normal.xy *= normalStrength;
                return normalize(TBN * normalize(normal));
            }
            return normalize(Normal);
        }
        
        vec2 rotateUV(vec2 uv, float angle)
        {
            float s = sin(angle);
            float c = cos(angle);
            mat2 rot = mat2(c, -s, s, c);
            return rot * uv;
        }

        void main()
        {
            vec2 uv;
            
            // ---------------------------------------------------------
            // 1. Determine which Mapping Logic to use
            // ---------------------------------------------------------
            
            bool isRightSidePreview = (previewMode == 1) && (FragPos.x > 0.0);
            
            if (isRightSidePreview) {
                // [RIGHT SIDE PREVIEW]
                // Driven by Surface Normal (Matcap Simulation)
                vec3 n = getNormal(); // Includes Normal Map distortion
                uv = n.xy * 0.5 + 0.5;
                
            } else {
                // [LEFT SIDE GENERATOR] or [STANDARD MODE]
                
                if (mappingMode == 0) {
                    // --- UV (Wrapped) ---
                    // Maps texture using Mesh UV coordinates.
                    uv = TexCoords;
                    uv.y = 1.0 - uv.y; // Fix inverted UVs from Geometry
                } else {
                    // --- Planar (Screen Space) ---
                    float centerX = (previewMode == 1) ? -0.5 : 0.0;
                    vec2 centerInfo = vec2(centerX, 0.0);
                    vec2 pos = FragPos.xy - centerInfo;
                    uv = pos + 0.5;
                }
            }
            
            // ---------------------------------------------------------
            // 2. Aspect Ratio Correction (Before Rotation/Scale)
            // ---------------------------------------------------------
            // Correct for image Aspect Ratio to prevent stretching usage logic:
            // Center is 0.5
            uv -= 0.5;
            
            // If AR > 1 (Wide), we want to squash Y (uv.y * AR) to make pixels square
            // If AR < 1 (Tall), we want to squash X (uv.x / AR) -> (uv.x * (1/AR))
            
            if (aspectRatio > 1.0) {
                uv.y *= aspectRatio;
            } else {
                uv.x *= (1.0 / aspectRatio);
            }
            
            // ---------------------------------------------------------
            // 3. Apply Transforms (Offset, Rotation, Scale)
            // ---------------------------------------------------------
            
            // Rotation
            uv = rotateUV(uv, radians(rotation));
            
            // Scale
            uv = uv / scale;
            
            // Offset (Applied after scale/rot? Or before? User usually expects "Move image")
            // If we move AFTER scaling/aspect, "Offset" unit depends on scale/aspect.
            // Let's apply Offset LAST (so it translates the final image window)
            // Wait, standard UV math:
            // Pos -> Scale -> Rot -> Trans -> UV
            // Here we are doing Inverse: UV -> Inverse Trans -> Inverse Rot -> Inverse Scale -> Image
            // So:
            // uv -= offset; // Move the window
            // uv = rot(uv);
            // uv = uv / scale;
            
            // Re-center for transform calc was already done at "uv -= 0.5"
            // Let's add offset here.
            uv -= offset;
            
            // Shift back to 0..1 range
            uv += 0.5;

            // ---------------------------------------------------------
            // 4. Sample & Output
            // ---------------------------------------------------------
            
            vec4 texColor = texture(imageTexture, uv);
            
            // Check Bounds for Planar? (Clamp to border?)
            // GL_REPEAT is set in load_texture, so it repeats.
            
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
            self.aspect_ratio = float(w) / float(h)
            
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
        if not self.shader_program or not self.enabled:
            return

        # Check if we need to load/reload texture BEFORE checking texture_id
        if self.image_path and self.image_path != self._texture_loaded_path:
            self.load_texture(self.image_path)
        
        # Now check if texture exists
        if not self.texture_id:
            return

        self.setup_blend_func() 
        glDepthFunc(GL_LEQUAL)
        glDepthMask(GL_FALSE)
        
        glUseProgram(self.shader_program)
        
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glUniform1i(glGetUniformLocation(self.shader_program, "imageTexture"), 0)
        
        if self.mapping_mode == "UV":
            mode_int = 0
        else:  # Planar
            mode_int = 1
            
        glUniform1i(glGetUniformLocation(self.shader_program, "mappingMode"), mode_int)
        
        glUniform1f(glGetUniformLocation(self.shader_program, "scale"), self.scale)
        glUniform1f(glGetUniformLocation(self.shader_program, "rotation"), self.rotation)
        glUniform2f(glGetUniformLocation(self.shader_program, "offset"), *self.offset)
        glUniform1f(glGetUniformLocation(self.shader_program, "opacity"), self.opacity)
        
        # Pass Aspect Ratio
        glUniform1f(glGetUniformLocation(self.shader_program, "aspectRatio"), self.aspect_ratio)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthFunc(GL_LESS)
        glDepthMask(GL_TRUE)

    def _load_shader(self, path):
        with open(path, 'r', encoding="utf-8") as f: return f.read()


