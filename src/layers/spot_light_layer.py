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
        vertex_src = self._load_shader("src/shaders/layer_base.vert")
        
        fragment_src = """
        #version 330 core
        out vec4 FragColor;
        in vec3 Normal;
        in vec3 FragPos;
        in vec2 TexCoords;
        in mat3 TBN;
        
        uniform vec3 lightDir;
        uniform vec3 lightColor;
        uniform float intensity;
        uniform float range;
        uniform float blur;
        
        // New Shape Uniforms
        uniform float scaleX;
        uniform float scaleY;
        uniform float rotation;
        
        uniform bool useNormalMap;
        uniform sampler2D normalMap;
        uniform float normalStrength;
        uniform float normalScale;
        uniform vec2 normalOffset;
        
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
        
        void main()
        {
            vec3 norm = getNormal();
            
            // 1. Light Basis Construction
            // We want a coordinate system where Z is pointing TO the light (L).
            vec3 L = normalize(-lightDir); 
            
            // Standard backface check
            float raw_ndotl = dot(norm, L);
            if (raw_ndotl <= 0.0) {
                FragColor = vec4(0.0);
                return;
            }
            
            // Construct orthogonal basis (Gram-Schmidt-like)
            vec3 UpGuess = abs(L.y) < 0.99 ? vec3(0, 1, 0) : vec3(1, 0, 0);
            vec3 Right = normalize(cross(UpGuess, L));
            vec3 Up = cross(L, Right);
            
            // 2. Project Normal onto this basis (Local Light Coordinates)
            // x, y represents the 'deviation' from the light center
            float x = dot(norm, Right);
            float y = dot(norm, Up);
            
            // 3. Apply 2D Rotation
            float rad = radians(rotation);
            float c = cos(rad);
            float s = sin(rad);
            float rx = x * c - y * s;
            float ry = x * s + y * c;
            
            // 4. Apply Scale (Inverse scaling of the coordinate stretches the feature)
            // Scale > 1.0 -> Coordinate smaller -> Deviation smaller -> Spot WIDER
            float sx = rx / max(0.001, scaleX);
            float sy = ry / max(0.001, scaleY);
            
            // 5. Reconstruct "Modified Z" (Pseudo NdotL)
            // dist_sq is sin^2(theta) in the distorted space
            float dist_sq = sx*sx + sy*sy;
            
            // If dist_sq > 1, it means the normal is 'behind' the plane in distorted space (clamped)
            float modified_ndotl = sqrt(max(0.0, 1.0 - dist_sq));
            
            // 6. Apply Standard Spot Logic with modified_ndotl
            // Map range to cutoff (larger range = smaller cutoff req = wider spot)
            float cutoff = 1.0 - range; 
            
            float epsilon = blur + 0.0001;
            float spot = smoothstep(cutoff - epsilon, cutoff + epsilon, modified_ndotl);
            
            vec3 finalColor = spot * lightColor * intensity;
            
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

    def _load_shader(self, path):
        with open(path, 'r', encoding="utf-8") as f: return f.read()


