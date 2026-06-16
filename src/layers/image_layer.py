from OpenGL.GL import *
from PIL import Image
from src.layers.interface import LayerInterface

class ImageLayer(LayerInterface):
    def __init__(self):
        super().__init__()
        self.name = "Image Layer"
        self.blend_mode = "Add" # Default Add per user request
        self.texture_id = None

        # Params
        self.image_path = ""
        self.mapping_mode = "UV" # "UV", "Planar" ("Spherical" omitted)
        self.scale = 1.0
        self.scale_x = 1.0 # Per-axis multiplier on top of scale
        self.scale_y = 1.0
        self.rotation = 0.0 # Degrees
        self.offset = [0.0, 0.0] # [x, y]
        self.aspect_ratio = 1.0 # width / height
        self.blur = 0.0 # Blur amount 0.0 - 1.0

        # Internal state
        self._texture_loaded_path = None # To track reloading necessity

    def initialize(self):
        # Shared base vertex shader with TBN support
        from src.core.resource_manager import ResourceManager
        self.shader_program = ResourceManager().get_shader("src/shaders/layer_base.vert", "src/shaders/layer_image.frag")
        self._setup_geometry()

        # Load Texture if needed
        if self.image_path:
            self.load_texture(self.image_path)

    def load_texture(self, path):
        """Load the image texture. Requires a current GL context."""
        if not path:
            return

        try:
            # Get Aspect Ratio (Read only header)
            with Image.open(path) as img:
                w, h = img.size
                self.aspect_ratio = float(w) / float(h)

            # Get Texture ID from Manager
            from src.core.resource_manager import ResourceManager
            self.texture_id = ResourceManager().get_texture(path)

            self.image_path = path
            self._texture_loaded_path = path
            print(f"Texture loaded: {path}")

        except Exception as e:
            print(f"Failed to load texture {path}: {e}")

    def render(self):
        if not self.shader_program or not self.enabled:
            return

        # Lazy (re)load: image_path may have been changed from the UI where
        # no GL context is current.
        if self.image_path and self.image_path != self._texture_loaded_path:
            self.load_texture(self.image_path)

        if not self.texture_id:
            return

        glUseProgram(self.shader_program)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glUniform1i(self._uloc("imageTexture"), 0)

        mode_int = 0 if self.mapping_mode == "UV" else 1  # 1 = Planar
        glUniform1i(self._uloc("mappingMode"), mode_int)

        # The shader divides UV by scale; avoid 0 (NaN UVs)
        safe_scale = self.scale if abs(self.scale) > 1e-4 else 1e-4
        safe_sx = self.scale_x if abs(self.scale_x) > 1e-4 else 1e-4
        safe_sy = self.scale_y if abs(self.scale_y) > 1e-4 else 1e-4
        glUniform1f(self._uloc("scale"), safe_scale)
        glUniform2f(self._uloc("scaleXY"), safe_sx, safe_sy)
        glUniform1f(self._uloc("rotation"), self.rotation)
        glUniform2f(self._uloc("offset"), *self.offset)
        glUniform1f(self._uloc("blur"), self.blur)
        glUniform1f(self._uloc("aspectRatio"), self.aspect_ratio)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
