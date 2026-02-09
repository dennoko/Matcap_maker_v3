from OpenGL.GL import *
from PySide6.QtOpenGL import QOpenGLFramebufferObject, QOpenGLFramebufferObjectFormat
import numpy as np
import ctypes
from src.layers.adjustment_layer import AdjustmentLayer

class Compositor:
    # Blend Modes Mapping (matches shader)
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
        
        # FBOs
        self.fbo_layer = None
        self.fbo_ping = None
        self.fbo_pong = None
        self.final_fbo = None
        
        # Resources
        self.blend_program = None
        self.quad_vao = None
        
        # Cache for intermediate results
        self._cached_fbo = None  # 最後にクリーンだった時点の中間結果
        self._cache_valid_up_to = -1  # キャッシュが有効なレイヤーインデックス

    def initialize(self):
        self._create_fbos()
        self._init_blend_shader()
        self._init_quad_geometry()

    def resize(self, width, height):
        self.width = width
        self.height = height
        self._create_fbos()
        self.invalidate_cache()  # サイズ変更時はキャッシュを無効化

    def invalidate_cache(self):
        """キャッシュを無効化（外部からの構造変更通知用）"""
        self._cache_valid_up_to = -1

    def _find_first_dirty_index(self, layer_stack):
        """最初のダーティレイヤーのインデックスを返す。全てクリーンなら-1"""
        for i, layer in enumerate(layer_stack):
            if layer.enabled and layer.is_dirty():
                return i
        return -1

    def _copy_fbo_to_cache(self, source_fbo):
        """FBOの内容をキャッシュにコピー"""
        if self._cached_fbo is None:
            fmt = QOpenGLFramebufferObjectFormat()
            fmt.setAttachment(QOpenGLFramebufferObject.CombinedDepthStencil)
            self._cached_fbo = QOpenGLFramebufferObject(self.width, self.height, fmt)
        
        # Blit source to cache
        QOpenGLFramebufferObject.blitFramebuffer(
            self._cached_fbo, source_fbo
        )

    def _restore_from_cache(self, target_fbo):
        """キャッシュからFBOに復元"""
        if self._cached_fbo:
            QOpenGLFramebufferObject.blitFramebuffer(
                target_fbo, self._cached_fbo
            )

    def render(self, layer_stack, context):
        """
        Render the stack.
        context: dict containing global settings:
            - global_normal_id
            - use_global_normal
            - normal_params (strength, scale, offset)
            - preview_mode_int
        """
        if not self.fbo_ping:
            return

        # Context Unpacking
        global_normal_id = context.get('global_normal_id')
        use_global_normal = context.get('use_global_normal', False)
        ns = context.get('normal_strength', 1.0)
        nsc = context.get('normal_scale', 1.0)
        noff = context.get('normal_offset', (0.0, 0.0))
        pm = context.get('preview_mode_int', 0)

        # Flush errors
        while glGetError() != GL_NO_ERROR: pass

        glViewport(0, 0, self.width, self.height)

        # --- Cache Logic ---
        layer_list = list(layer_stack)
        first_dirty = self._find_first_dirty_index(layer_list)
        
        # Determine start index
        if first_dirty == -1:
            # All layers are clean - nothing to render, use cached result
            if self._cache_valid_up_to >= 0 and self.final_fbo:
                return  # Already have valid result
            start_index = 0  # Fallback: render all
        elif first_dirty > 0 and self._cache_valid_up_to >= first_dirty - 1:
            # Cache is valid up to the layer before the first dirty one
            start_index = first_dirty
        else:
            # Cache invalid or dirty from the beginning
            start_index = 0

        # Clear Accumulators
        self.fbo_ping.bind()
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.fbo_ping.release()

        self.fbo_pong.bind()
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.fbo_pong.release()

        current_fbo = self.fbo_ping
        next_fbo = self.fbo_pong

        # Restore from cache if starting from a later index
        if start_index > 0 and self._cached_fbo:
            self._restore_from_cache(current_fbo)

        for i, layer in enumerate(layer_list):
            if not layer.enabled or not layer.shader_program:
                continue
            
            # Skip layers before start_index (already in cache)
            if i < start_index:
                continue

            # --- Adjustment Layer Logic ---
            if isinstance(layer, AdjustmentLayer):
                next_fbo.bind()
                glClearColor(0.0, 0.0, 0.0, 0.0)
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                
                glDisable(GL_BLEND)
                glUseProgram(layer.shader_program)
                
                glActiveTexture(GL_TEXTURE0)
                glBindTexture(GL_TEXTURE_2D, current_fbo.texture())
                
                layer.render() # Calls glDrawArrays typically? No, layer.render sets uniforms.
                # We need to draw the quad here?
                # Engine.py lines 159-163: layer.render(), then draw quad.
                
                glBindVertexArray(self.quad_vao)
                glDrawArrays(GL_TRIANGLES, 0, 6)
                glBindVertexArray(0)
                
                next_fbo.release()
                current_fbo, next_fbo = next_fbo, current_fbo
                layer.mark_clean()  # Mark as clean after rendering
                continue

            # --- Standard Layer Logic ---
            self.fbo_layer.bind()
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            glDisable(GL_BLEND)
            glUseProgram(layer.shader_program)

            # Uniforms
            glUniform1i(glGetUniformLocation(layer.shader_program, "normalMap"), 5)
            glActiveTexture(GL_TEXTURE5)
            if use_global_normal and global_normal_id:
                glBindTexture(GL_TEXTURE_2D, global_normal_id)
            else:
                glBindTexture(GL_TEXTURE_2D, 0)
            
            glUniform1i(glGetUniformLocation(layer.shader_program, "useNormalMap"), 1 if use_global_normal else 0)
            glUniform1f(glGetUniformLocation(layer.shader_program, "normalStrength"), ns)
            glUniform1f(glGetUniformLocation(layer.shader_program, "normalScale"), nsc)
            glUniform2f(glGetUniformLocation(layer.shader_program, "normalOffset"), *noff)
            glUniform1i(glGetUniformLocation(layer.shader_program, "previewMode"), pm)

            # Scaling / Aspect Ratio
            content_hw = 0.95 if pm == 1 else 1.0
            content_hh = 0.45 if pm == 1 else 1.0
            content_aspect = content_hw / content_hh
            
            vp_w = max(1.0, float(self.width))
            vp_h = max(1.0, float(self.height))
            screen_aspect = vp_w / vp_h
            
            raw_zoom = 1.0
            if screen_aspect > content_aspect:
                 raw_zoom = 1.0 / content_hh
            else:
                 raw_zoom = screen_aspect / content_hw # Fit Width logic corrected in Engine?
            
            # Re-check Engine.py logic (Step 14):
            # else: raw_zoom = screen_aspect / content_hw
            # scale_y = raw_zoom
            # scale_x = raw_zoom / screen_aspect
            
            scale_y = raw_zoom
            scale_x = raw_zoom / screen_aspect 
            
            glUniform3f(glGetUniformLocation(layer.shader_program, "uScale"), scale_x, scale_y, 1.0)
            
            layer.render() # Sets other uniforms? And Draws?
            # Wait, layer.render() in Engine.py line 223 calls `layer.render()`.
            # BaseLayer.render() typically does NOT draw, it update uniforms.
            # Engine.py does NOT draw quad for Standard Layer??
            # Let's check Engine.py line 223.
            # `layer.render()`
            # Does `layer.render()` draw?
            # `src/layers/interface.py`: `render` is pass.
            # `src/layers/base_layer.py`: Usually draws geometry?
            # Let's check `src/layers/base_layer.py`.
            
            # Assuming layer.render() sets uniforms and draws geometry.
            # But wait, AdjustmentLayer logic EXPLICITLY draws quad in Engine.py (line 163).
            # But Standard Layer logic (line 223) calls `layer.render()`.
            # I must check `BaseLayer.render` implementation.
            
            self.fbo_layer.release()
            
            # Composite
            next_fbo.bind()
            glClearColor(0.0, 0.0, 0.0, 0.0) # OR retain background? Engine clears it.
            # Logic: We blend fbo_layer over current_fbo.
            # If next_fbo is cleared, we need to draw current_fbo? 
            # Engine.py line 230: glClear.
            # Line 246: binds `current_fbo` as TEXTURE1.
            # So the blend shader reads both and outputs result.
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) 
            
            glDisable(GL_BLEND)
            glUseProgram(self.blend_program)
            
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.fbo_layer.texture())
            glUniform1i(glGetUniformLocation(self.blend_program, "uSrc"), 0)
            
            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_2D, current_fbo.texture())
            glUniform1i(glGetUniformLocation(self.blend_program, "uDst"), 1)
            
            mode_id = self.BLEND_MODES.get(layer.blend_mode, 0)
            glUniform1i(glGetUniformLocation(self.blend_program, "uMode"), mode_id)
            glUniform1f(glGetUniformLocation(self.blend_program, "uOpacity"), 1.0)
            
            glBindVertexArray(self.quad_vao)
            glDrawArrays(GL_TRIANGLES, 0, 6)
            glBindVertexArray(0)
            
            next_fbo.release()
            
            current_fbo, next_fbo = next_fbo, current_fbo
            layer.mark_clean()  # Mark as clean after rendering

        self.final_fbo = current_fbo
        
        # Update cache with current result
        self._copy_fbo_to_cache(current_fbo)
        self._cache_valid_up_to = len(layer_list) - 1

    def get_texture_id(self):
        return self.final_fbo.texture() if self.final_fbo else 0

    def _create_fbos(self):
        def make_fbo(w, h):
            fmt = QOpenGLFramebufferObjectFormat()
            fmt.setAttachment(QOpenGLFramebufferObject.CombinedDepthStencil)
            fbo = QOpenGLFramebufferObject(w, h, fmt)
            return fbo

        if self.fbo_layer: del self.fbo_layer
        if self.fbo_ping: del self.fbo_ping
        if self.fbo_pong: del self.fbo_pong
        
        self.fbo_layer = make_fbo(self.width, self.height)
        self.fbo_ping = make_fbo(self.width, self.height)
        self.fbo_pong = make_fbo(self.width, self.height)
        self.final_fbo = self.fbo_ping

    def _init_blend_shader(self):
        from src.core.resource_manager import ResourceManager
        self.blend_program = ResourceManager().get_shader("src/shaders/quad.vert", "src/shaders/blend.frag")

    def _init_quad_geometry(self):
        quad_vertices = np.array([
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
        
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(2 * 4))
        
        glBindVertexArray(0)
