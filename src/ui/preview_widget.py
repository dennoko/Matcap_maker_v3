from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np

from src.core.engine import Engine
from src.core.layer_stack import LayerStack
from src.layers.base_layer import BaseLayer
from src.layers.blend_layer import BlendLayer

from PySide6.QtGui import QSurfaceFormat

class PreviewWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        
        # Request OpenGL 3.3 Core
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        self.setFormat(fmt)
        
        self.engine = Engine()
        self.layer_stack = LayerStack()
        
        self.width_ = 400
        self.height_ = 400
        
        # Default Layer
        self.base_layer = BaseLayer()
        self.layer_stack.add_layer(self.base_layer)
        # self.layer_stack.add_layer(BlendLayer()) # Checkpoint 3 Add
        
        # Quad for drawing texture to screen
        self.quad_shader = None
        self.quad_vao = None
        
    def initializeGL(self):
        print(f"GL_VERSION: {glGetString(GL_VERSION)}")
        print(f"GL_RENDERER: {glGetString(GL_RENDERER)}")
        
        # Initialize Engine (FBOs)
        self.engine.initialize()
        
        # Initialize Layers
        for layer in self.layer_stack:
            layer.initialize()
            
        # Initialize Screen Quad
        self._init_quad()

    def resizeGL(self, w, h):
        self.engine.resize(w, h)
        # We don't change viewport here directly because paintGL might need custom viewport for aspect ratio
        self.width_ = w
        self.height_ = h

    def paintGL(self):
        # Save the QOpenGLWidget's FBO (it might not be 0!)
        default_fbo = glGetIntegerv(GL_FRAMEBUFFER_BINDING)
        
        # 1. Render Layers to FBO via Engine
        self.engine.render(self.layer_stack)
        
        # 2. Render FBO Texture to Screen
        # Restore the widget's FBO
        glBindFramebuffer(GL_FRAMEBUFFER, default_fbo)
        glClearColor(0.2, 0.2, 0.2, 1.0) 
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Calculate viewport for 1:1 Aspect Ratio
        side = min(self.width_, self.height_)
        x = (self.width_ - side) // 2
        y = (self.height_ - side) // 2
        glViewport(x, y, side, side)
        
        # Disable Depth Test & Culling for Screen Quad to ensure it always draws
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        
        if self.quad_shader:
            glUseProgram(self.quad_shader)
            glBindVertexArray(self.quad_vao)
            
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.engine.get_texture_id())
            glUniform1i(glGetUniformLocation(self.quad_shader, "screenTexture"), 0)
            
            glDrawArrays(GL_TRIANGLES, 0, 6)
            glBindVertexArray(0)
            
        # Re-enable defaults if needed (though next frame clears anyway)
        glEnable(GL_DEPTH_TEST)
        
        # Restore Viewport for next pass if needed?
        # Actually standard widget behavior might reset it, but better safe.
        glViewport(0, 0, self.width_, self.height_)

    def _init_quad(self):
        # Remove any existing VAO to force fresh start
        if self.quad_vao:
            glDeleteVertexArrays(1, [self.quad_vao])
            
        # Standard Full Screen Quad
        # XYZ, UV
        quadVertices = np.array([
            -1.0,  1.0, 0.0,  0.0, 1.0,
            -1.0, -1.0, 0.0,  0.0, 0.0,
             1.0, -1.0, 0.0,  1.0, 0.0,

            -1.0,  1.0, 0.0,  0.0, 1.0,
             1.0, -1.0, 0.0,  1.0, 0.0,
             1.0,  1.0, 0.0,  1.0, 1.0
        ], dtype=np.float32)

        self.quad_vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        
        glBindVertexArray(self.quad_vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, quadVertices.nbytes, quadVertices, GL_STATIC_DRAW)
        
        stride = 5 * 4 # 5 floats * 4 bytes
        # Pos
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        # TexCoord
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * 4))
        
        glBindVertexArray(0)
        
        print("DEBUG: Quad VAO Initialized")
        try:
            with open("src/shaders/quad.vert", "r") as f: vert_src = f.read()
            with open("src/shaders/quad.frag", "r") as f: frag_src = f.read()
            
            vs = shaders.compileShader(vert_src, GL_VERTEX_SHADER)
            fs = shaders.compileShader(frag_src, GL_FRAGMENT_SHADER)
            self.quad_shader = shaders.compileProgram(vs, fs)
        except Exception as e:
            print(f"Quad Shader error: {e}")

