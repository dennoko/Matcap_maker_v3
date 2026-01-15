from OpenGL.GL import *
from OpenGL.GL import shaders
from PySide6.QtOpenGL import QOpenGLFramebufferObject, QOpenGLFramebufferObjectFormat
import numpy as np

class Engine:
    # Blend Modes Mapping (Must match shader defines)
    BLEND_MODES = {
        "Normal": 0,
        "Add": 1,
        "Multiply": 2,
        "Screen": 3,
        "Subtract": 4,
        "Lighten": 5,
        "Darken": 6,
        "Overlay": 7,
        "Soft Light": 8,
        "Hard Light": 9,
        "Color Dodge": 10,
        "Difference": 11
    }

    def __init__(self, width=512, height=512):
        self.width = width
        self.height = height
        
        # FBOs for Ping-Pong Compositing
        self.fbo_layer = None # Temps for current layer render
        self.fbo_ping = None  # Accumulator A
        self.fbo_pong = None  # Accumulator B
        
        # Shader
        self.blend_program = None
        self.quad_vao = None
        
        self.global_normal_id = None
        self.use_global_normal = False
        self.preview_rotation = 0.0
        
        self.normal_strength = 1.0
        self.normal_scale = 1.0
        self.normal_offset = [0.0, 0.0]
        
    def initialize(self):
        # Initial creation
        self._create_fbos()
        self._init_blend_shader()
        self._init_quad_geometry()
        
    def resize(self, width, height):
        self.width = width
        self.height = height
        self._create_fbos()
            
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
        if not self.fbo_ping:
            return
            
        # Flush previous errors
        while glGetError() != GL_NO_ERROR: pass

        # -------------------------------------------------------------
        # Ping-Pong Compositing Logic
        # -------------------------------------------------------------
        
        # Ensure Viewport matches current FBO size
        glViewport(0, 0, self.width, self.height)
        
        # 1. Clear accumulators
        self.fbo_ping.bind()
        glClearColor(0.0, 0.0, 0.0, 0.0) # Transparent Black background
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.fbo_ping.release()
        
        self.fbo_pong.bind()
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.fbo_pong.release()
        
        # Current accumulator is ping initially
        current_fbo = self.fbo_ping
        next_fbo = self.fbo_pong
        
        # Enable Blending for internal layer logic (opacity etc within layer draw)
        
        for layer in layer_stack:
            if not layer.enabled or not layer.shader_program:
                continue
            
            # --- Step A: Render Layer to fbo_layer (Intermediate) ---
            self.fbo_layer.bind()
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # Standard GL Settings for Layer Rendering
            # We must DISABLE blending here to ensure we capture the RAW (Straight) RGB and Alpha from the layer shader.
            # If we enable blend, we get Pre-multiplied Alpha on the black background, but our composite shader
            # expects Straight RGB for its math (mix(Dst, Src, Alpha)).
            glDisable(GL_BLEND)
            # glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            # Setup Uniforms & Render
            glUseProgram(layer.shader_program)
            
            # Global Uniforms
            glUniform1i(glGetUniformLocation(layer.shader_program, "normalMap"), 5)
            glActiveTexture(GL_TEXTURE5)
            if self.use_global_normal and self.global_normal_id:
                glBindTexture(GL_TEXTURE_2D, self.global_normal_id)
            else:
                glBindTexture(GL_TEXTURE_2D, 0)
                
            glUniform1i(glGetUniformLocation(layer.shader_program, "useNormalMap"), 1 if self.use_global_normal else 0)
            glUniform1f(glGetUniformLocation(layer.shader_program, "normalStrength"), self.normal_strength)
            glUniform1f(glGetUniformLocation(layer.shader_program, "normalScale"), self.normal_scale)
            glUniform2f(glGetUniformLocation(layer.shader_program, "normalOffset"), *self.normal_offset)
            
            glUniform2f(glGetUniformLocation(layer.shader_program, "normalOffset"), *self.normal_offset)
            
            pm = getattr(self, "preview_mode_int", 0) 
            glUniform1i(glGetUniformLocation(layer.shader_program, "previewMode"), pm)
            
            # --- Aspect Ratio & Scaling Logic ---
            # Standard Mode (0): Content is Square (1.0 x 1.0 half-extent) -> Bounds [-1, 1] x [-1, 1]
            # Comparison Mode (1): Content is Wide (~0.95 x 0.45 half-extent) -> Bounds [-0.95, 0.95] x [-0.45, 0.45]
            
            # Note: We want to Maximize the content in the viewport without stretching.
            
            # 1. Define Content Half-Extents (Approximation)
            content_hw = 1.0
            content_hh = 1.0
            
            if pm == 1: # Comparison Mode
                 content_hw = 0.95
                 content_hh = 0.45
            
            content_aspect = content_hw / content_hh
            
            # 2. Viewport Aspect Ratio
            # self.width / self.height
            # Avoid division by zero
            vp_w = max(1.0, float(self.width))
            vp_h = max(1.0, float(self.height))
            screen_aspect = vp_w / vp_h
            
            # 3. Calculate Zoom factor to Fit
            # if screen_aspect > content_aspect: Screen is Wider -> Fit Height
            # else: Screen is Narrower -> Fit Width
            
            raw_zoom = 1.0
            if screen_aspect > content_aspect:
                # Fit Height
                # raw_zoom * content_hh = 1.0 (NDC Top)
                raw_zoom = 1.0 / content_hh
            else:
                # Fit Width
                # We need x_ndc range to cover [-1, 1]
                # x_ndc = x_local * raw_zoom / screen_aspect (due to x shrinking below)
                # actually let's just stick to "Dimension Mapping"
                # raw_zoom * content_hw = screen_aspect * 1.0??
                # No. 
                # If Fit Width: raw_zoom = screen_aspect / content_hw.
                raw_zoom = screen_aspect / content_hw

            # 4. Apply Aspect Correction to X axis
            # NDC X range [-1, 1] maps to Width pixels. 
            # NDC Y range [-1, 1] maps to Height pixels.
            # To preserve squareness, X units must be smaller if Width is larger.
            # scale.x = scale.y / screen_aspect.
            
            scale_y = raw_zoom
            scale_x = raw_zoom / screen_aspect
            
            glUniform3f(glGetUniformLocation(layer.shader_program, "uScale"), scale_x, scale_y, 1.0)
            
            layer.render()
            
            self.fbo_layer.release()
            
            # --- Step B: Composite (Blend) fbo_layer over current_fbo into next_fbo ---
            next_fbo.bind()
            glClearColor(0.0, 0.0, 0.0, 0.0) # Clear dest
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) # Actually usually we just overwrite full screen quad
            
            # Disable blend for the composite operation itself, as the shader handles the mixing logic
            # and outputs the final color/alpha which should overwrite the destination buffer
            glDisable(GL_BLEND)

            glUseProgram(self.blend_program)
            
            # Bind Textures
            # Unit 0: Foreground (Layer Result)
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.fbo_layer.texture())
            glUniform1i(glGetUniformLocation(self.blend_program, "uSrc"), 0)
            
            # Unit 1: Background (Accumulated Result)
            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_2D, current_fbo.texture())
            glUniform1i(glGetUniformLocation(self.blend_program, "uDst"), 1)
            
            # Uniforms
            mode_id = self.BLEND_MODES.get(layer.blend_mode, 0)
            glUniform1i(glGetUniformLocation(self.blend_program, "uMode"), mode_id)
            glUniform1f(glGetUniformLocation(self.blend_program, "uOpacity"), 1.0) # Opacity is handled in Layer Shader? Yes.
            # Wait, verify image_layer opacity.
            # Image Layer: FragColor = tex * opacity. So fbo_layer result IS premultiplied by opacity (in alpha sense? no straight alpha usually)
            # Standard GL BlendFunc(SrcAlpha, OneMinus) -> SrcRGB * SrcA + DstRGB * (1-SrcA).
            # If layer shader outputs: A = TexA * Opacity.
            # Then fbo_layer contains correct alpha-weighted color?
            # NO. fbo_layer contains (RGB, A).
            # If we blend it using Shader, we need to apply Opacity there?
            # Or is Opacity already applied to A in fbo_layer?
            # Yes, ImageLayer L254: FragColor.a = tex.a * opacity.
            # So `uOpacity` in Blend Shader should be 1.0 if it's already baked into fbo_layer.alpha.
            # BUT if we want "Group B" blends (Overlay etc), they often ignore Alpha for color math, then mix using alpha.
            # My Blend Shader uses `srcAlpha` from texture input. So it works.
            
            # Draw Quad
            glBindVertexArray(self.quad_vao)
            glDrawArrays(GL_TRIANGLES, 0, 6)
            glBindVertexArray(0)
            
            next_fbo.release()
            
            # Swap Ping-Pong
            current_fbo, next_fbo = next_fbo, current_fbo
            
        # End of Loop
        # Valid result is in `current_fbo`
        
        # We want the result to remain in a stable FBO for "get_texture_id"
        # If `current_fbo` is `fbo_ping`, calling get_texture_id handles it?
        # `fbo` property is gone. We need to track which one has the result.
        self.final_fbo = current_fbo
        
    def get_texture_id(self):
        return self.final_fbo.texture() if hasattr(self, 'final_fbo') and self.final_fbo else 0

    def _create_fbos(self):
        # Helper
        def make_fbo(w, h):
            fmt = QOpenGLFramebufferObjectFormat()
            fmt.setAttachment(QOpenGLFramebufferObject.CombinedDepthStencil)
            fbo = QOpenGLFramebufferObject(w, h, fmt)
            if not fbo.isValid():
                print("ERROR: FBO invalid")
            return fbo

        # Cleanup
        if self.fbo_layer: del self.fbo_layer
        if self.fbo_ping: del self.fbo_ping
        if self.fbo_pong: del self.fbo_pong
        
        self.fbo_layer = make_fbo(self.width, self.height)
        self.fbo_ping = make_fbo(self.width, self.height)
        self.fbo_pong = make_fbo(self.width, self.height)
        self.final_fbo = self.fbo_ping # Default
        
    def _init_blend_shader(self):
        from src.core.resource_manager import ResourceManager
        self.blend_program = ResourceManager().get_shader("src/shaders/quad.vert", "src/shaders/blend.frag")
            
    def _init_quad_geometry(self):
        # Simple Quad -1..1
        quad_vertices = np.array([
            # Pos(2), UV(2)
            -1.0,  1.0,  0.0, 1.0,
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,
             
            -1.0,  1.0,  0.0, 1.0,
             1.0, -1.0,  1.0, 0.0,
             1.0,  1.0,  1.0, 1.0
        ], dtype=np.float32)
        
        self.quad_vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        
        glBindVertexArray(self.quad_vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, GL_STATIC_DRAW)
        
        # Pos
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
        # UV
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(2 * 4))
        
        glBindVertexArray(0)

    def render_offscreen(self, width, height, layer_stack, preview_mode_override=None, force_no_normal=False):
        """Render to image using temp engine instance to handle resolution change"""
        # Create a temp engine with desired res
        temp_engine = Engine(width, height)
        temp_engine.initialize()
        
        # Copy global state
        use_normal = self.use_global_normal
        if force_no_normal:
            use_normal = False
            
        temp_engine.set_global_normal_map(self.global_normal_id, use_normal, 
                                          self.normal_strength, self.normal_scale, self.normal_offset)
        
        mode = preview_mode_override if preview_mode_override is not None else getattr(self, 'preview_mode_int', 0)
        temp_engine.set_preview_mode(mode)
        
        # Render
        temp_engine.render(layer_stack)
        
        # Get Image
        img = temp_engine.final_fbo.toImage()
        
        # Cleanup (explicitly delete FBOs to free GPU mem immediately if possible)
        del temp_engine.fbo_layer
        del temp_engine.fbo_ping
        del temp_engine.fbo_pong
        
        return img
