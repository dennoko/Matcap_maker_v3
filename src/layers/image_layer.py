from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np
from PIL import Image
from src.layers.interface import LayerInterface

class ImageLayer(LayerInterface):
    def __init__(self):
        super().__init__()
        self.name = "Image Layer"
        self.blend_mode = "Normal" # Default to Normal for decals/textures
        self.opacity = 1.0 # Add explicit opacity (handled by base/blend func usually, but good to have)
        
        self.shader_program = None
        self.VAO = None
        self.index_count = 0
        self.texture_id = None
        
        # Params
        self.image_path = ""
        self.mapping_mode = "UV" # "UV", "Planar" ("Spherical" omitted)
        self.blend_mode = "Add" # Default changed from Normal to Add per user request
        self.scale = 1.0
        self.rotation = 0.0 # Degrees
        self.offset = [0.0, 0.0] # [x, y]
        self.aspect_ratio = 1.0 # width / height
        
        # Internal state
        self._texture_loaded_path = None # To track reloading necessity
        
    def initialize(self):
        # Vertex Shader
        # Vertex Shader (Load shared base shader with TBN support)
        from src.core.resource_manager import ResourceManager
        self.shader_program = ResourceManager().get_shader("src/shaders/layer_base.vert", "src/shaders/layer_image.frag")


        # Geometry
        self._setup_geometry()
        
        # Load Texture if needed
        if self.image_path:
            self.load_texture(self.image_path)
            
    def load_texture(self, path):
        if not path:
            return
            
        try:
            # Get Aspect Ratio (Read only header)
            with Image.open(path) as img:
                w, h = img.size
                self.aspect_ratio = float(w) / float(h)

            # Get Texture ID from Manager
            from src.core.resource_manager import ResourceManager
            self.texture_id = ResourceManager().get_texture(path)
            
            self.image_path = path
            self._texture_loaded_path = path
            print(f"Texture loaded: {path}")
            
        except Exception as e:
            print(f"Failed to load texture {path}: {e}")

    def render(self):
        if not self.shader_program or not self.enabled:
            return

        # Check if we need to load/reload texture BEFORE checking texture_id
        if self.image_path and self.image_path != self._texture_loaded_path:
            self.load_texture(self.image_path)
        
        # Now check if texture exists
        if not self.texture_id:
            return

        self.setup_blend_func() 
        glDepthFunc(GL_LEQUAL)
        glDepthMask(GL_FALSE)
        
        glUseProgram(self.shader_program)
        
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glUniform1i(glGetUniformLocation(self.shader_program, "imageTexture"), 0)
        
        if self.mapping_mode == "UV":
            mode_int = 0
        else:  # Planar
            mode_int = 1
            
        glUniform1i(glGetUniformLocation(self.shader_program, "mappingMode"), mode_int)
        
        glUniform1f(glGetUniformLocation(self.shader_program, "scale"), self.scale)
        glUniform1f(glGetUniformLocation(self.shader_program, "rotation"), self.rotation)
        glUniform2f(glGetUniformLocation(self.shader_program, "offset"), *self.offset)
        glUniform1f(glGetUniformLocation(self.shader_program, "opacity"), self.opacity)
        
        # Pass Aspect Ratio
        glUniform1f(glGetUniformLocation(self.shader_program, "aspectRatio"), self.aspect_ratio)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthFunc(GL_LESS)
        glDepthMask(GL_TRUE)




