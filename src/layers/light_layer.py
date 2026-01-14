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
        in vec2 TexCoords;
        in mat3 TBN;
        
        uniform vec3 lightDir;
        uniform vec3 lightColor;
        uniform float intensity;
        
        uniform bool useNormalMap;
        uniform sampler2D normalMap;
        
        vec3 getNormal() {
            // Only apply Normal Map to Preview Object (Right Side, > 0.0)
            if (useNormalMap && FragPos.x > 0.0) {
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

        except Exception as e:
            print(f"LightLayer Shader Error: {e}")
            return

        # Generate Geometry
        self._setup_geometry()
        
    def render(self):
        if not self.shader_program or not self.enabled:
            return

        # Set Blend Mode
        self.setup_blend_func()
        
        # Determine uniforms based on blend mode
        u_color = self.color
        u_intensity = self.intensity

        if self.blend_mode == "Multiply":
            # Special handling for Multiply to make Intensity intuitive (0=No effect, High=Darker)
            u_intensity = 1.0 # Bake intensity into color
            if self.intensity <= 1.0:
                # Interpolate White -> Color
                # White * (1-I) + Color * I  => 1 - I + Color*I
                u_color = [(1.0 - self.intensity) + c * self.intensity for c in self.color]
            else:
                # Interpolate Color -> Black
                # Color / Intensity
                if self.intensity > 0:
                    u_color = [c / self.intensity for c in self.color]
                else:
                    u_color = self.color # Should not happen via logic branch
        
        # Mulit-pass rendering rules for same geometry:
        # 1. Depth Func needs to be LEQUAL so valid fragments at same depth pass
        # 2. Don't write depth (already written by base)
        glDepthFunc(GL_LEQUAL)
        glDepthMask(GL_FALSE)
        
        glUseProgram(self.shader_program)
        glUniform3f(glGetUniformLocation(self.shader_program, "lightDir"), *self.direction)
        glUniform3f(glGetUniformLocation(self.shader_program, "lightColor"), *u_color)
        glUniform1f(glGetUniformLocation(self.shader_program, "intensity"), u_intensity)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        
        # Reset States
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthFunc(GL_LESS)
        glDepthMask(GL_TRUE)

    def _load_shader(self, path):
        with open(path, 'r', encoding="utf-8") as f: return f.read()


