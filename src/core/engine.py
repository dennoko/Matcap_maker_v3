from src.core.compositor import Compositor

class Engine:
    # Expose Blend Modes (Facade)
    BLEND_MODES = Compositor.BLEND_MODES

    def __init__(self, width=512, height=512):
        self.width = width
        self.height = height
        self.compositor = Compositor(width, height)
        
        # Global State
        self.global_normal_id = None
        self.use_global_normal = False
        self.preview_rotation = 0.0
        
        self.normal_strength = 1.0
        self.normal_scale = 1.0
        self.normal_offset = [0.0, 0.0]
        self.preview_mode_int = 0
        
    def initialize(self):
        self.compositor.initialize()
        
    def resize(self, width, height):
        self.width = width
        self.height = height
        self.compositor.resize(width, height)
            
    def set_global_normal_map(self, texture_id, use_map, strength=1.0, scale=1.0, offset=(0.0,0.0)):
        self.global_normal_id = texture_id
        self.use_global_normal = use_map
        self.normal_strength = strength
        self.normal_scale = scale
        self.normal_offset = offset

    def set_preview_mode(self, mode_int):
        # 0 = Standard, 1 = Comparison (With Normal Map)
        self.preview_mode_int = mode_int

    def set_preview_rotation(self, angle):
        self.preview_rotation = angle

    def render(self, layer_stack):
        context = {
            'global_normal_id': self.global_normal_id,
            'use_global_normal': self.use_global_normal,
            'normal_strength': self.normal_strength,
            'normal_scale': self.normal_scale,
            'normal_offset': self.normal_offset,
            'preview_mode_int': self.preview_mode_int
        }
        self.compositor.render(layer_stack, context)
        
    def get_texture_id(self):
        return self.compositor.get_texture_id()

    def render_offscreen(self, width, height, layer_stack, preview_mode_override=None, force_no_normal=False):
        """Render to image using temp engine instance to handle resolution change"""
        # Create a temp Compositor with desired res
        temp_comp = Compositor(width, height)
        temp_comp.initialize()
        
        # Copy global state
        use_normal = self.use_global_normal
        if force_no_normal:
            use_normal = False
        
        mode = preview_mode_override if preview_mode_override is not None else self.preview_mode_int
        
        ctx = {
            'global_normal_id': self.global_normal_id,
            'use_global_normal': use_normal,
            'normal_strength': self.normal_strength,
            'normal_scale': self.normal_scale,
            'normal_offset': self.normal_offset,
            'preview_mode_int': mode
        }
            
        # Render
        temp_comp.render(layer_stack, ctx)
        
        # Get Image
        if temp_comp.final_fbo:
            img = temp_comp.final_fbo.toImage()
        else:
            img = None # Should not happen
        
        # Cleanup
        # Explicit deletion might help with FBO release
        del temp_comp
        
        return img
