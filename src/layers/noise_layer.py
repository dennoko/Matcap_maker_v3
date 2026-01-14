from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np
from src.layers.interface import LayerInterface

class NoiseLayer(LayerInterface):
    def __init__(self):
        super().__init__()
        self.name = "Noise"
        self.blend_mode = "Multiply" # Default to Multiply (supported)
        self.shader_program = None
        self.VAO = None
        self.index_count = 0
        self.texture_id = None
        
        # Params
        self.scale = 1.0
        self.intensity = 1.0
        self.seed = 0
        self.color = [0.0, 0.0, 0.0] # Default Black for Multiply

    def initialize(self):
        # Vertex Shader
        vertex_src = self._load_shader("src/shaders/layer_base.vert")
        
        fragment_src = """#version 330 core
        out vec4 FragColor;
        in vec3 Normal;
        in vec2 TexCoords; 
        
        uniform sampler2D noiseTexture;
        uniform float scale;
        uniform float intensity;
        uniform vec3 color;
        
        void main()
        {
            vec2 uv = TexCoords * scale;
            
            vec4 texColor = texture(noiseTexture, uv);
            float noiseVal = texColor.r; 
            
            // For Multiply mode:
            // We want base color to be white (1,1,1) where noise is 0? No wait.
            // Noise 0..1. 
            // If noise is black (0), result is 0?
            
            // Let's implement modulation:
            // Final = mix(White, Color, NoiseVal * Intensity) ?
            // Usually noise is used as a mask or direct overlay.
            
            // If Blend Mode is Multiply:
            // Output = 1.0 (No change) where we want no noise.
            // Output = Color where we want noise.
            
            // Assume NoiseVal 0..1 (Random).
            // We want to interpolate between White (1,1,1) and TargetColor based on NoiseVal * Intensity.
            
            vec3 target = color;
            vec3 white = vec3(1.0);
            
            vec3 finalColor = mix(white, target, noiseVal * intensity);
            
            // Alpha should be 1.0 because we output "the color to be multiplied".
            // If we use Alpha blending, we need to match glBlendFunc logic.
            // Multiply func: Dst * (Src + 1 - A).
            // If we output A=1, result is Dst * Src.
            
            FragColor = vec4(finalColor, 1.0); 
        }
        """
        
        try:
            vertex_shader = shaders.compileShader(vertex_src, GL_VERTEX_SHADER)
            fragment_shader = shaders.compileShader(fragment_src, GL_FRAGMENT_SHADER)
            self.shader_program = shaders.compileProgram(vertex_shader, fragment_shader)
        except Exception as e:
            print(f"NoiseLayer Shader Error: {e}")
            return

        self._setup_geometry()
        self._generate_noise_texture()

    def render(self):
        if not self.shader_program or not self.enabled:
            return

        self.setup_blend_func()
        glDepthFunc(GL_LEQUAL)
        glDepthMask(GL_FALSE)
        
        glUseProgram(self.shader_program)
        
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glUniform1i(glGetUniformLocation(self.shader_program, "noiseTexture"), 0)
        
        glUniform1f(glGetUniformLocation(self.shader_program, "scale"), self.scale)
        glUniform1f(glGetUniformLocation(self.shader_program, "intensity"), self.intensity)
        glUniform3f(glGetUniformLocation(self.shader_program, "color"), *self.color)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthFunc(GL_LESS)
        glDepthMask(GL_TRUE)
        
    def _generate_noise_texture(self):
        # Generate simple white noise for now
        width, height = 256, 256
        rng = np.random.default_rng(self.seed)
        noise_data = rng.random((height, width), dtype=np.float32)
        noise_data = (noise_data * 255).astype(np.uint8)
        
        if self.texture_id:
            glDeleteTextures([self.texture_id])
            
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        # GL_LUMINANCE is deprecated in core, use GL_RED
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, width, height, 0, GL_RED, GL_UNSIGNED_BYTE, noise_data)
        glGenerateMipmap(GL_TEXTURE_2D)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    def _load_shader(self, path):
        with open(path, 'r', encoding="utf-8") as f: return f.read()


