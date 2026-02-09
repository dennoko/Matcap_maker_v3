class LayerInterface:
    def __init__(self):
        self.name = "Layer"
        self.enabled = True
        self.opacity = 1.0
        self.blend_mode = "Normal" # "Normal", "Add", "Multiply", "Screen"
        self._dirty = True  # 初期状態はダーティ（初回描画が必要）

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
        """Called every frame"""
        pass
        
    def set_parameter(self, name, value):
        """Update a parameter"""
        pass
        
    def _setup_geometry(self):
        """Default geometry setup (Sphere)"""
        from src.core.geometry import GeometryEngine
        verts, inds = GeometryEngine.generate_sphere()
        self.update_geometry(verts, inds)

    def update_geometry(self, vertices, indices):
        """Update the VAO/VBO with new geometry data"""
        from OpenGL.GL import glGenVertexArrays, glGenBuffers, glBindVertexArray, glBindBuffer, glBufferData, glEnableVertexAttribArray, glVertexAttribPointer, GL_ARRAY_BUFFER, GL_ELEMENT_ARRAY_BUFFER, GL_STATIC_DRAW, GL_FLOAT, GL_FALSE, GL_UNSIGNED_INT
        import numpy as np
        import ctypes
        
        self.index_count = len(indices)
        # print(f"Update Geometry: Count={self.index_count}")
        
        # Cleanup old if exists
        # (Skipping delete for brevity/safety, usually fine for this tool scope, but ideally delete old buffers)
        
        self.VAO = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        ebo = glGenBuffers(1)
        
        glBindVertexArray(self.VAO)
        
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
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

    # Serialization is now handled by src.core.layer_serializer.LayerSerializer
    # to_dict and from_dict have been removed to adhere to SRP.


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
            # Fallback (Treat as Normal / Pre-multiplied)
            glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
