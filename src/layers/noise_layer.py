from OpenGL.GL import *
import numpy as np
from src.layers.interface import LayerInterface

class NoiseLayer(LayerInterface):
    def __init__(self):
        super().__init__()
        self.name = "Noise"
        self.blend_mode = "Multiply" # Default to Multiply (supported)
        self.texture_id = None

        # Params
        self.scale = 1.0
        self.intensity = 1.0
        self.seed = 0
        self.color = [0.0, 0.0, 0.0] # Default Black for Multiply

        # Internal
        self._needs_regen = False

    def initialize(self):
        from src.core.resource_manager import ResourceManager
        self.shader_program = ResourceManager().get_shader("src/shaders/layer_base.vert", "src/shaders/layer_noise.frag")
        self._setup_geometry()
        self._generate_noise_texture()

    def render(self):
        if not self.shader_program or not self.enabled:
            return

        # Texture (re)generation needs a current GL context, so it is
        # deferred from UI callbacks (regenerate) to the render pass.
        if self._needs_regen or not self.texture_id:
            self._generate_noise_texture()
            self._needs_regen = False

        glUseProgram(self.shader_program)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glUniform1i(self._uloc("noiseTexture"), 0)

        glUniform1f(self._uloc("scale"), self.scale)
        glUniform1f(self._uloc("intensity"), self.intensity)
        glUniform3f(self._uloc("color"), *self.color)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    def regenerate(self):
        """Request regeneration of the noise texture on the next render."""
        self._needs_regen = True

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
