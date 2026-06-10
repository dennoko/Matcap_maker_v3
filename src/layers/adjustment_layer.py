from OpenGL.GL import glUniform1f, glUniform1i
from src.layers.interface import LayerInterface
from src.core.resource_manager import ResourceManager

class AdjustmentLayer(LayerInterface):
    # Post-process layer: the Compositor feeds the accumulated result into
    # this layer's shader on a full-screen quad instead of drawing geometry.
    is_post_process = True

    def __init__(self):
        super().__init__()
        self.name = "Color Adjustment"

        # Shader Properties
        self.hue = 0.0        # -0.5 to 0.5
        self.saturation = 1.0 # 0.0 to 2.0
        self.brightness = 0.0 # -1.0 to 1.0
        self.contrast = 1.0   # 0.0 to 2.0

    def initialize(self):
        # Fragment-only effect; the Compositor supplies the quad geometry.
        self.shader_program = ResourceManager().get_shader(
            "src/shaders/quad.vert",
            "src/shaders/layer_adjustment.frag"
        )

    def render(self):
        # Called by the Compositor with the shader bound and the source
        # texture on unit 0. Only sets this layer's own uniforms.
        if not self.shader_program:
            return

        glUniform1f(self._uloc("uHue"), self.hue)
        glUniform1f(self._uloc("uSaturation"), self.saturation)
        glUniform1f(self._uloc("uBrightness"), self.brightness)
        glUniform1f(self._uloc("uContrast"), self.contrast)
        glUniform1i(self._uloc("uTexture"), 0)
