class LayerInterface:
    def __init__(self):
        self.name = "Layer"
        self.enabled = True
        self.opacity = 1.0
        self.blend_mode = "Normal" # "Normal", "Add", "Multiply", "Screen"

    def initialize(self):
        """Called once when GL context is ready"""
        pass
        
    def render(self):
        """Called every frame"""
        pass
        
    def set_parameter(self, name, value):
        """Update a parameter"""
        pass

    def setup_blend_func(self):
        from OpenGL.GL import glBlendFunc, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_DST_COLOR, GL_ZERO, GL_ONE_MINUS_SRC_COLOR, GL_ONE_MINUS_SRC_ALPHA
        
        # Assumption: Shaders output Pre-multiplied Alpha
        # RGB = Color * Alpha * Intensity
        # A = Alpha (Coverage)
        
        if self.blend_mode == "Normal":
            # Normal: Src + Dst*(1-A)
            glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
            
        elif self.blend_mode == "Add":
            # Add: Src + Dst
            glBlendFunc(GL_ONE, GL_ONE)
            
        elif self.blend_mode == "Multiply":
            # Multiply: Dst * (SrcRGB + 1 - A)
            # Derivation: Dst * SrcRGB + Dst * (1 - A)
            # = (Dst * SrcRGB) + (Dst * (1 - SrcAlpha))
            # Requires SrcRGB to be effectively the "tint" factor weighted by alpha
            glBlendFunc(GL_DST_COLOR, GL_ONE_MINUS_SRC_ALPHA) 
            
        elif self.blend_mode == "Screen":
            # Screen: Src + Dst * (1 - Src)
            glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_COLOR)
            
        else:
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
