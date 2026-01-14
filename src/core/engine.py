from OpenGL.GL import *
from PySide6.QtOpenGL import QOpenGLFramebufferObject, QOpenGLFramebufferObjectFormat

class Engine:
    def __init__(self, width=512, height=512):
        self.width = width
        self.height = height
        self.fbo = None
        self.global_normal_id = None
        self.use_global_normal = False
        self.preview_rotation = 0.0
        
    def initialize(self):
        # Initial creation
        self._create_fbo()
        
    def resize(self, width, height):
        self.width = width
        self.height = height
        self._create_fbo()
            
    def set_global_normal_map(self, texture_id, use_map):
        self.global_normal_id = texture_id
        self.use_global_normal = use_map

    def set_preview_rotation(self, angle):
        self.preview_rotation = angle

    def render(self, layer_stack):
        if not self.fbo:
            return
            
        # Flush previous errors
        while glGetError() != GL_NO_ERROR: pass

        # print(f"Engine Render: Layers={len(layer_stack)} FBO={self.fbo.handle()} GlobalNorm={self.use_global_normal}")

        # 1. Bind FBO
        self.fbo.bind()
        
        # Clear FBO
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Standard blending
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Setup Global Normal Map (Unit 5)
        glActiveTexture(GL_TEXTURE5)
        if self.use_global_normal and self.global_normal_id:
            glBindTexture(GL_TEXTURE_2D, self.global_normal_id)
        else:
            glBindTexture(GL_TEXTURE_2D, 0)
        
        # Render All Layers
        for layer in layer_stack:
            if layer.enabled and layer.shader_program:
                # We need to set uniforms AFTER glUseProgram, which happens in layer.render()
                # BUT we can't inject it easily without modifying layer.render() or calling glUseProgram beforehand.
                # Calling glUseProgram twice is fine (internal GL check is fast).
                glUseProgram(layer.shader_program)
                
                # Set Global Uniforms
                glUniform1i(glGetUniformLocation(layer.shader_program, "normalMap"), 5)
                glUniform1i(glGetUniformLocation(layer.shader_program, "useNormalMap"), 1 if self.use_global_normal else 0)
                
                # Preview Rotation Removed
                # glUniform1f(glGetUniformLocation(layer.shader_program, "previewRotation"), self.preview_rotation)
                
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

    def render_offscreen(self, width, height, layer_stack):
        """Render the stack to an image at specific resolution"""
        # Create temp FBO
        fmt = QOpenGLFramebufferObjectFormat()
        fmt.setAttachment(QOpenGLFramebufferObject.CombinedDepthStencil)
        temp_fbo = QOpenGLFramebufferObject(width, height, fmt)
        
        if not temp_fbo.isValid():
            print("Failed to create offscreen FBO")
            return None
            
        temp_fbo.bind()
        
        # Setup Viewport for this FBO
        glViewport(0, 0, width, height)
        
        # Clear
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Blending
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Render Layers
        # IMPORTANT: Layers rely on current viewport? 
        # Most layers (Base, Light) assume viewport is set correctly.
        # However, if they used cached aspect ratio or screen size, might be issue.
        # But our shaders rely on `gl_Position` (Clip Space) and `aTexCoords`, so Resolution Independent.
        # EXCEPT PreviewWidget centering logic? No, that's Quad. Engines layers are 3D.
        # Light Directions are valid.
        # SpotLight "Range" maps to dot product, resolution independent.
        # Noise Scale is resolution independent (UV based).
        # Image Scale is UV based.
        
        for layer in layer_stack:
            if layer.enabled:
                layer.render()
                
        # Capture Image
        image = temp_fbo.toImage()
        
        temp_fbo.release()
        
        # Cleanup (del might not be enough immediately but Python GC handles it usually)
        # QOpenGLFramebufferObject cleans up GL resource on destruction
        
        return image
