from src.layers.interface import LayerInterface
from src.core.resource_manager import ResourceManager
from OpenGL.GL import glUniform1f, glUniform1i, glGetUniformLocation
import os

class AdjustmentLayer(LayerInterface):
    def __init__(self):
        super().__init__()
        self.name = "Color Adjustment"
        self.type_id = "adjustment" # Used for saving/loading
        
        # Shader Properties
        self.hue = 0.0        # -0.5 to 0.5
        self.saturation = 1.0 # 0.0 to 2.0
        self.brightness = 0.0 # -1.0 to 1.0
        self.contrast = 1.0   # 0.0 to 2.0
        
        # Override geometry logic? 
        # Actually Engine handles the quad drawing for this layer type.
        # But we need to load the shader.

    def initialize(self):
        # We use a custom shader but don't strictly use standard vertex processing
        # Engine will use correct Vertex Shader (quad.vert) with this fragment shader
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # vs = os.path.join(base_dir, "shaders", "quad.vert") # Shared quad vert
        # fs = os.path.join(base_dir, "shaders", "layer_adjustment.frag")
        
        self.shader_program = ResourceManager().get_shader(
            "src/shaders/quad.vert", 
            "src/shaders/layer_adjustment.frag"
        )

    def render(self):
        # Called by Engine.
        # Engine binds the shader. We set uniforms.
        if not self.shader_program:
            return
            
        glUniform1f(glGetUniformLocation(self.shader_program, "uHue"), self.hue)
        glUniform1f(glGetUniformLocation(self.shader_program, "uSaturation"), self.saturation)
        glUniform1f(glGetUniformLocation(self.shader_program, "uBrightness"), self.brightness)
        glUniform1f(glGetUniformLocation(self.shader_program, "uContrast"), self.contrast)
        
        # Engine handles texture binding (uTexture)
        glUniform1i(glGetUniformLocation(self.shader_program, "uTexture"), 0)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "hue": self.hue,
            "saturation": self.saturation,
            "brightness": self.brightness,
            "contrast": self.contrast
        })
        return data

    def from_dict(self, data):
        super().from_dict(data)
        self.hue = data.get("hue", 0.0)
        self.saturation = data.get("saturation", 1.0)
        self.brightness = data.get("brightness", 0.0)
        self.contrast = data.get("contrast", 1.0)
