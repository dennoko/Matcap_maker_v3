from OpenGL.GL import *
from OpenGL.GL import shaders
from PIL import Image
import os
from src.core.utils import get_resource_path

class ResourceManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResourceManager, cls).__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        # Cache dictionaries
        self._shaders = {}  # key: (vert_path, frag_path), value: program_id
        self._textures = {} # key: path, value: texture_id
        
    def get_shader(self, vert_path, frag_path):
        """Get or compile a shader program."""
        # Resolve paths for frozen environment
        v_path = get_resource_path(vert_path)
        f_path = get_resource_path(frag_path)
        
        key = (v_path, f_path)
        if key in self._shaders:
            return self._shaders[key]
            
        # Compile new shader
        program = self._compile_shader(v_path, f_path)
        if program:
            self._shaders[key] = program
            
        return program
        
    def get_texture(self, path):
        """Get or load a texture."""
        if not path:
            return None
            
        # Check if path is absolute (external file) or relative (internal resource)
        # If absolute, use as is. If relative, resolve via utils.
        full_path = path
        if not os.path.isabs(path):
             full_path = get_resource_path(path)
             
        if not os.path.exists(full_path):
            print(f"ResourceManager: Texture not found: {full_path}")
            return None
            
        if full_path in self._textures:
            return self._textures[full_path]
            
        # Load new texture
        tex_id = self._load_texture_from_file(full_path)
        if tex_id:
            self._textures[full_path] = tex_id
            
        return tex_id
        
    def _compile_shader(self, vert_path, frag_path):
        try:
            with open(vert_path, 'r', encoding='utf-8') as f:
                vs_source = f.read()
            with open(frag_path, 'r', encoding='utf-8') as f:
                fs_source = f.read()
                
            vertex_shader = shaders.compileShader(vs_source, GL_VERTEX_SHADER)
            fragment_shader = shaders.compileShader(fs_source, GL_FRAGMENT_SHADER)
            program = shaders.compileProgram(vertex_shader, fragment_shader)
            return program
        except Exception as e:
            print(f"ResourceManager: Shader Compile Error ({vert_path}, {frag_path}): {e}")
            return None

    def _load_texture_from_file(self, path):
        try:
            img = Image.open(path)
            # Ensure correct format
            img = img.convert("RGBA")
            # Flip for OpenGL
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
            img_data = img.tobytes()
            w, h = img.size
            
            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
            glGenerateMipmap(GL_TEXTURE_2D)
            
            glBindTexture(GL_TEXTURE_2D, 0)
            print(f"ResourceManager: Loaded texture {path}")
            return tex_id
        except Exception as e:
            print(f"ResourceManager: Failed to load texture {path}: {e}")
            return None
            
    def reload_texture(self, path):
        """Force reload a texture (e.g. if file changed on disk)."""
        if path in self._textures:
            glDeleteTextures([self._textures[path]])
            del self._textures[path]
        return self.get_texture(path)

    def clear(self):
        """Clear all resources (e.g. on shutdown)."""
        for prog in self._shaders.values():
            glDeleteProgram(prog)
        self._shaders.clear()
        
        for tex in self._textures.values():
            glDeleteTextures([tex])
        self._textures.clear()
