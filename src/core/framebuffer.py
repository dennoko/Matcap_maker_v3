from OpenGL.GL import *
import ctypes

class FrameBuffer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        try:
            # glGenFramebuffers returns a list-like or scalar depending on impl. Force list then take first?
            # Or usually scalar if n=1.
            bufs = glGenFramebuffers(1)
            self.fbo = int(bufs) if not isinstance(bufs, list) else int(bufs[0])
            print(f"DEBUG: Created FBO ID: {self.fbo}")
            
            texs = glGenTextures(1)
            self.texture = int(texs) if not isinstance(texs, list) else int(texs[0])
            
            rbos = glGenRenderbuffers(1)
            self.rbo = int(rbos) if not isinstance(rbos, list) else int(rbos[0])
            
            self.resize(width, height)
        except Exception as e:
            print(f"FBO Init Error: {e}")
            raise e
        
    def resize(self, width, height):
        self.width = width
        self.height = height
        
        print(f"DEBUG: Resizing FBO {self.fbo} to {width}x{height}")
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        
        # Texture attachment
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texture, 0)
        
        # RBO for Depth/Stencil
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, width, height)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, self.rbo)
        
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            print("ERROR::FRAMEBUFFER:: Framebuffer is not complete!")
            
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        
    def bind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glViewport(0, 0, self.width, self.height)
        
    def unbind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
