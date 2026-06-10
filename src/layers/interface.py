from OpenGL.GL import glGetUniformLocation


class LayerInterface:
    # True for layers that post-process the accumulated result on a
    # full-screen quad instead of drawing their own geometry.
    # (Class attribute: not serialized, override per subclass.)
    is_post_process = False

    def __init__(self):
        self.name = "Layer"
        self.enabled = True
        self.opacity = 1.0
        self.blend_mode = "Normal"  # See Compositor.BLEND_MODES
        self.shader_program = None
        self.VAO = None
        self.index_count = 0
        self._vbo = None
        self._ebo = None
        self._dirty = True  # 初期状態はダーティ（初回描画が必要）
        self._uniform_cache = {}

    def mark_dirty(self):
        """パラメータ変更時に呼び出し、再描画が必要であることを示す"""
        self._dirty = True

    def mark_clean(self):
        """レンダリング完了後に呼び出す"""
        self._dirty = False

    def is_dirty(self) -> bool:
        """このレイヤーが再描画を必要とするかどうか"""
        return self._dirty

    def initialize(self):
        """Called once when GL context is ready"""
        pass

    def render(self):
        """Called every frame. Set uniforms and issue the draw call only;
        framebuffer/blend/cull state is managed by the Compositor."""
        pass

    def set_parameter(self, name, value):
        """Update a parameter"""
        pass

    def _uloc(self, name):
        """Cached uniform location lookup for this layer's shader program."""
        key = (self.shader_program, name)
        loc = self._uniform_cache.get(key)
        if loc is None:
            loc = glGetUniformLocation(self.shader_program, name)
            self._uniform_cache[key] = loc
        return loc

    def _setup_geometry(self):
        """Default geometry setup (Sphere)"""
        from src.core.geometry import GeometryEngine
        verts, inds = GeometryEngine.generate_sphere()
        self.update_geometry(verts, inds)

    def update_geometry(self, vertices, indices):
        """Update the VAO/VBO with new geometry data (requires current GL context)"""
        from OpenGL.GL import (
            glGenVertexArrays, glGenBuffers, glBindVertexArray, glBindBuffer,
            glBufferData, glEnableVertexAttribArray, glVertexAttribPointer,
            glDeleteVertexArrays, glDeleteBuffers,
            GL_ARRAY_BUFFER, GL_ELEMENT_ARRAY_BUFFER, GL_STATIC_DRAW,
            GL_FLOAT, GL_FALSE
        )
        import ctypes

        self.index_count = len(indices)

        # Free previous buffers (geometry is regenerated on preview-mode switches)
        if getattr(self, 'VAO', None):
            glDeleteVertexArrays(1, [self.VAO])
        if getattr(self, '_vbo', None):
            glDeleteBuffers(1, [self._vbo])
        if getattr(self, '_ebo', None):
            glDeleteBuffers(1, [self._ebo])

        self.VAO = glGenVertexArrays(1)
        self._vbo = glGenBuffers(1)
        self._ebo = glGenBuffers(1)

        glBindVertexArray(self.VAO)

        glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        # Stride: 11 floats * 4 bytes
        # [Px, Py, Pz, Nx, Ny, Nz, U, V, Tx, Ty, Tz]
        stride = 11 * 4

        # 0: Pos (3)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))

        # 1: Norm (3)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * 4))

        # 2: UV (2)
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(6 * 4))

        # 3: Tangent (3)
        glEnableVertexAttribArray(3)
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8 * 4))

        glBindVertexArray(0)

    # Serialization is handled by src.core.layer_serializer.LayerSerializer (SRP).
