from OpenGL.GL import *
from PySide6.QtOpenGL import QOpenGLFramebufferObject, QOpenGLFramebufferObjectFormat
import numpy as np
import ctypes


class Compositor:
    """GPU compositing pipeline.

    Owns the ping-pong FBOs, the programmable blend pass (blend.frag) and the
    GL state shared by all layer passes. Layers only set their own uniforms
    and issue their draw call; all framebuffer/blend/cull state lives here.
    """

    # Blend Modes Mapping (matches blend.frag)
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
        self._quad_vbo = None

        # Uniform location cache: (program, name) -> location
        self._uniform_cache = {}

        # Simple cache: only skip if ALL layers are clean
        self._all_clean = False

    def initialize(self):
        self._create_fbos()
        self._init_blend_shader()
        self._init_quad_geometry()

    def resize(self, width, height):
        self.width = width
        self.height = height
        self._create_fbos()
        self._all_clean = False  # Invalidate cache on resize

    def cleanup(self):
        """Release GL resources owned by this compositor.

        Shader programs are shared via ResourceManager and not deleted here.
        Requires a current GL context.
        """
        if self.quad_vao:
            glDeleteVertexArrays(1, [self.quad_vao])
            self.quad_vao = None
        if self._quad_vbo:
            glDeleteBuffers(1, [self._quad_vbo])
            self._quad_vbo = None
        # QOpenGLFramebufferObject releases its GL resources on destruction
        self.fbo_layer = None
        self.fbo_ping = None
        self.fbo_pong = None
        self.final_fbo = None
        self._uniform_cache.clear()

    def invalidate_cache(self):
        """キャッシュを無効化（外部からの構造変更通知用）"""
        self._all_clean = False

    def _any_layer_dirty(self, layers):
        """いずれかのレイヤーがダーティかどうかを確認（無効レイヤーの変化も検出）"""
        for layer in layers:
            if layer.is_dirty():
                return True
        return False

    def render(self, layer_stack, context):
        """
        Render the stack.
        context: dict containing global settings:
            - global_normal_id / use_global_normal
            - normal_strength / normal_scale / normal_offset
            - preview_mode_int
        """
        if not self.fbo_ping:
            return

        # Simple cache: skip rendering if all layers are clean
        layer_list = list(layer_stack)
        if self._all_clean and not self._any_layer_dirty(layer_list):
            return  # Nothing changed, keep existing result

        # Flush stale errors
        while glGetError() != GL_NO_ERROR:
            pass

        glViewport(0, 0, self.width, self.height)
        self._clear_fbo(self.fbo_ping)
        self._clear_fbo(self.fbo_pong)

        # Shared state for every pass: compositing happens entirely in
        # blend.frag (programmable blending), and all layer geometry is a
        # convex sphere, so back-face culling replaces depth testing.
        glDisable(GL_BLEND)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)

        current_fbo = self.fbo_ping
        next_fbo = self.fbo_pong
        scale = self._content_scale(context.get('preview_mode_int', 0))

        for layer in layer_list:
            if not layer.enabled or not layer.shader_program:
                continue

            if layer.is_post_process:
                self._render_post_process(layer, current_fbo, next_fbo)
            else:
                self._render_layer(layer, context, scale)
                self._composite(layer, current_fbo, next_fbo)

            current_fbo, next_fbo = next_fbo, current_fbo

        glDisable(GL_CULL_FACE)
        glEnable(GL_DEPTH_TEST)

        self.final_fbo = current_fbo

        # Mark all layers as clean and set cache valid
        for layer in layer_list:
            layer.mark_clean()
        self._all_clean = True

    def get_texture_id(self):
        return self.final_fbo.texture() if self.final_fbo else 0

    # ------------------------------------------------------------------
    # Render passes
    # ------------------------------------------------------------------

    def _render_layer(self, layer, context, scale):
        """Draw a single layer's own geometry into fbo_layer."""
        self.fbo_layer.bind()
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        prog = layer.shader_program
        glUseProgram(prog)

        # Global normal-map / preview uniforms shared by all layer shaders
        use_normal = context.get('use_global_normal', False)
        normal_id = context.get('global_normal_id')
        glActiveTexture(GL_TEXTURE5)
        glBindTexture(GL_TEXTURE_2D, normal_id if (use_normal and normal_id) else 0)

        glUniform1i(self._uloc(prog, "normalMap"), 5)
        glUniform1i(self._uloc(prog, "useNormalMap"), 1 if (use_normal and normal_id) else 0)
        glUniform1f(self._uloc(prog, "normalStrength"), context.get('normal_strength', 1.0))
        glUniform1f(self._uloc(prog, "normalScale"), context.get('normal_scale', 1.0))
        glUniform2f(self._uloc(prog, "normalOffset"), *context.get('normal_offset', (0.0, 0.0)))
        glUniform1i(self._uloc(prog, "previewMode"), context.get('preview_mode_int', 0))
        glUniform3f(self._uloc(prog, "uScale"), scale[0], scale[1], 1.0)

        layer.render()
        self.fbo_layer.release()

    def _composite(self, layer, current_fbo, next_fbo):
        """Blend fbo_layer (Src) over current_fbo (Dst) into next_fbo."""
        next_fbo.bind()
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        prog = self.blend_program
        glUseProgram(prog)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.fbo_layer.texture())
        glUniform1i(self._uloc(prog, "uSrc"), 0)

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, current_fbo.texture())
        glUniform1i(self._uloc(prog, "uDst"), 1)

        glUniform1i(self._uloc(prog, "uMode"), self.BLEND_MODES.get(layer.blend_mode, 0))
        glUniform1f(self._uloc(prog, "uOpacity"), layer.opacity)

        self._draw_quad()
        next_fbo.release()

    def _render_post_process(self, layer, current_fbo, next_fbo):
        """Run a full-screen post-process layer over the accumulated result."""
        next_fbo.bind()
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        prog = layer.shader_program
        glUseProgram(prog)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, current_fbo.texture())
        glUniform1f(self._uloc(prog, "uOpacity"), layer.opacity)

        layer.render()  # sets the layer's own uniforms (incl. uTexture = 0)
        self._draw_quad()
        next_fbo.release()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _uloc(self, program, name):
        """Cached glGetUniformLocation (string lookups are per-frame hot path)."""
        key = (program, name)
        loc = self._uniform_cache.get(key)
        if loc is None:
            loc = glGetUniformLocation(program, name)
            self._uniform_cache[key] = loc
        return loc

    def _clear_fbo(self, fbo):
        fbo.bind()
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        fbo.release()

    def _content_scale(self, preview_mode_int):
        """Fit the content (single sphere or comparison pair) into the viewport."""
        content_hw = 0.95 if preview_mode_int == 1 else 1.0
        content_hh = 0.45 if preview_mode_int == 1 else 1.0

        vp_w = max(1.0, float(self.width))
        vp_h = max(1.0, float(self.height))
        screen_aspect = vp_w / vp_h

        if screen_aspect > (content_hw / content_hh):
            raw_zoom = 1.0 / content_hh   # Fit height
        else:
            raw_zoom = screen_aspect / content_hw  # Fit width

        return (raw_zoom / screen_aspect, raw_zoom)

    def _draw_quad(self):
        glBindVertexArray(self.quad_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)

    def _create_fbos(self):
        def make_fbo(w, h):
            fmt = QOpenGLFramebufferObjectFormat()
            fmt.setAttachment(QOpenGLFramebufferObject.CombinedDepthStencil)
            return QOpenGLFramebufferObject(w, h, fmt)

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
        self._quad_vbo = glGenBuffers(1)

        glBindVertexArray(self.quad_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self._quad_vbo)
        glBufferData(GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, GL_STATIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(2 * 4))

        glBindVertexArray(0)
