from OpenGL.GL import glUniform1f, glUniform1i
from src.layers.interface import LayerInterface
from src.core.resource_manager import ResourceManager


class BlurSharpenLayer(LayerInterface):
    # Post-process layer rendered on a full-screen quad over the accumulated
    # result. Uses a separable Gaussian (horizontal + vertical), so the
    # Compositor runs it in two passes (see Compositor._render_post_process).
    is_post_process = True
    num_passes = 2

    def __init__(self):
        super().__init__()
        self.name = "Blur / Sharpen"

        # Params
        self.mode = "Blur"    # "Blur" or "Sharpen"
        self.radius = 0.5     # 0.0 - 1.0 : Gaussian radius (both modes)
        self.amount = 1.0     # 0.0 - 2.0 : Sharpen strength (Blur uses opacity)

    def initialize(self):
        # Fragment-only effect; the Compositor supplies the quad geometry.
        self.shader_program = ResourceManager().get_shader(
            "src/shaders/quad.vert",
            "src/shaders/layer_blur_sharpen.frag"
        )

    def render(self):
        # Called by the Compositor once per pass with the shader bound, the
        # source on unit 0 and (pass 1) the original on unit 1. uPass/uOpacity/
        # uOriginal are set by the Compositor; here we set our own params.
        if not self.shader_program:
            return

        glUniform1i(self._uloc("uMode"), 0 if self.mode == "Blur" else 1)
        glUniform1f(self._uloc("uRadius"), self.radius)
        glUniform1f(self._uloc("uAmount"), self.amount)
        glUniform1i(self._uloc("uTexture"), 0)
