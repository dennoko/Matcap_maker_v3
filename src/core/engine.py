from OpenGL.GL import *
from PySide6.QtOpenGL import QOpenGLFramebufferObject, QOpenGLFramebufferObjectFormat

class Engine:
    def __init__(self, width=512, height=512):
        self.width = width
        self.height = height
        self.fbo = None
        
    def initialize(self):
        # Initial creation
        self._create_fbo()
        
    def resize(self, width, height):
        self.width = width
        self.height = height
        self._create_fbo()
            
    def render(self, layer_stack):
        if not self.fbo:
            return
            
        # Flush previous errors
        while glGetError() != GL_NO_ERROR: pass

        # 1. Bind FBO
        self.fbo.bind()
        
        # Clear FBO
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Standard blending
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Render All Layers
        for layer in layer_stack:
            if layer.enabled:
                layer.render()
                
        # 2. Release FBO
        self.fbo.release()
        
    def get_texture_id(self):
        return self.fbo.texture() if self.fbo else 0

    def _create_fbo(self):
        # Recreate FBO
        if self.fbo:
            del self.fbo
            self.fbo = None
            
        fmt = QOpenGLFramebufferObjectFormat()
        fmt.setAttachment(QOpenGLFramebufferObject.CombinedDepthStencil)
        
        self.fbo = QOpenGLFramebufferObject(self.width, self.height, fmt)
        if not self.fbo.isValid():
            print("ERROR: QOpenGLFramebufferObject is invalid!")
