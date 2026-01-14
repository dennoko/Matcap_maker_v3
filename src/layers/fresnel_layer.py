from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np
from src.layers.interface import LayerInterface

class FresnelLayer(LayerInterface):
    def __init__(self):
        super().__init__()
        self.name = "Fresnel / Rim"
        self.blend_mode = "Add"
        self.shader_program = None
        self.VAO = None
        self.index_count = 0
        
        # Params
        self.color = [0.0, 1.0, 1.0] # Default Cyan to see effect clearly
        self.intensity = 1.0
        self.power = 5.0   # Higher exponent for sharper rim
        self.bias = 0.0    # Offset
        
        # For Fresnel, direction usually means View direction which is fixed [0,0,1] for matcaps
        # But we could allow shifting the "center" if needed. For now fixed.

    def initialize(self):
        # Reuse base geometry logic (Sphere)
        vertex_src = self._load_shader("src/shaders/layer_base.vert")
        
        fragment_src = """#version 330 core
        out vec4 FragColor;
        in vec3 Normal;
        in vec3 FragPos; 
        in vec2 TexCoords;
        in mat3 TBN;
        
        uniform vec3 color;
        uniform float intensity;
        uniform float power;
        uniform float bias;
        
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
            // View direction: from surface toward camera
            // Camera looks down -Z, so view direction is -Z
            vec3 viewDir = vec3(0.0, 0.0, -1.0); 
            
            // dot(N, V): high at center (normals point toward camera), low at edge
            float ndotv = max(dot(norm, viewDir), 0.0);
            
            // Fresnel/Rim: bright at edge (ndotv~0), dark at center (ndotv~1)
            float rim = pow(1.0 - ndotv, max(power, 0.001));
            
            rim = clamp(rim + bias, 0.0, 1.0);
            
            vec3 finalColor = rim * color * intensity;
            
            FragColor = vec4(finalColor, rim); 
        }
        """
        
        try:
            vertex_shader = shaders.compileShader(vertex_src, GL_VERTEX_SHADER)
            fragment_shader = shaders.compileShader(fragment_src, GL_FRAGMENT_SHADER)
            self.shader_program = shaders.compileProgram(vertex_shader, fragment_shader)
        except Exception as e:
            print(f"FresnelLayer Shader Error: {e}")
            return

        # Generate Geometry
        self._setup_geometry()

    def render(self):
        if not self.shader_program or not self.enabled:
            return

        self.setup_blend_func()
        glDepthFunc(GL_LEQUAL)
        glDepthMask(GL_FALSE)
        
        # Enable Culling for Fresnel to avoid backface rim artifacts
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        
        # Calculate uniforms for Multiply mode if needed
        u_color = self.color
        u_intensity = self.intensity
        if self.blend_mode == "Multiply":
             u_intensity = 1.0
             if self.intensity <= 1.0:
                 u_color = [(1.0 - self.intensity) + c * self.intensity for c in self.color]
             else:
                 if self.intensity > 0:
                     u_color = [c / self.intensity for c in self.color]

        glUseProgram(self.shader_program)
        glUniform3f(glGetUniformLocation(self.shader_program, "color"), *u_color)
        glUniform1f(glGetUniformLocation(self.shader_program, "intensity"), u_intensity)
        glUniform1f(glGetUniformLocation(self.shader_program, "power"), self.power)
        glUniform1f(glGetUniformLocation(self.shader_program, "bias"), self.bias)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthFunc(GL_LESS)
        glDepthMask(GL_TRUE)
    def _load_shader(self, path):
        with open(path, 'r', encoding="utf-8") as f: return f.read()


