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
        in vec2 TexCoords;
        in mat3 TBN;
        
        uniform vec3 lightDir;
        uniform vec3 lightColor;
        uniform float intensity;
        uniform float range;
        uniform float blur;
        
        uniform bool useNormalMap;
        uniform sampler2D normalMap;
        
        vec3 getNormal() {
            if (useNormalMap && FragPos.x > -0.05) {
                vec3 normal = texture(normalMap, TexCoords).rgb;
                normal = normal * 2.0 - 1.0;
                return normalize(TBN * normal);
            }
            return normalize(Normal);
        }
        
        void main()
        {
            vec3 norm = getNormal();
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
        with open(path, 'r', encoding="utf-8") as f: return f.read()


