from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, QTimer
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np

from src.core.engine import Engine
from src.core.layer_stack import LayerStack
from src.layers.base_layer import BaseLayer
from src.layers.blend_layer import BlendLayer
from src.core.settings import Settings
from src.core.geometry import GeometryEngine
from PIL import Image
import os

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
        self.base_layer.base_color = [0.0, 0.0, 0.0] # Default Black as requested
        self.layer_stack.add_layer(self.base_layer)
        
        # Default Spot Light
        from src.layers.spot_light_layer import SpotLightLayer
        spot = SpotLightLayer()
        spot.range = 0.13
        spot.blur = 1.0
        spot.direction = [0.35, -0.22, 1.0]
        self.layer_stack.add_layer(spot)
        
        # Quad for drawing texture to screen
        self.quad_shader = None
        self.quad_vao = None
        
        # Global State
        self.current_shape_name = "Standard"
        self.current_normal_path = ""
        self.normal_map_id = None
        
        # NOTE: Animation removed as requested.
        print("DEBUG: PreviewWidget Instance Created (Rev 3 - No Anim)")
        import sys
        sys.stdout.flush()
        
    # Animation methods removed
    
    def _update_global_state(self):
        if not self.layer_stack: return
        base_layer = self.layer_stack[0]
        if not isinstance(base_layer, BaseLayer): return
        
        # Check for new layers
        current_count = len(self.layer_stack)
        # Initialize tracker if missing
        if not hasattr(self, "_known_layer_count"):
            self._known_layer_count = current_count
            
        # Preview Mode Update
        # We track `current_shape_name` as the geometry state key
        mode_changed = base_layer.preview_mode != self.current_shape_name
        layer_count_changed = current_count != self._known_layer_count
        
        if mode_changed or layer_count_changed:
            self.current_shape_name = base_layer.preview_mode
            self._known_layer_count = current_count
            
            self._update_all_geometry(self.current_shape_name)
            self.update() # Trigger redraw
            
        # Normal Map Update
        if base_layer.normal_map_path != self.current_normal_path:
            self._load_normal_map(base_layer.normal_map_path)
            
        # Pass to Engine
        # Only enable normal map if we have one AND we are in "With Normal Map" mode
        use_normal = bool(self.normal_map_id) and (base_layer.preview_mode == "With Normal Map")
        
        self.engine.set_global_normal_map(
            self.normal_map_id, 
            use_normal,
            base_layer.normal_strength,
            base_layer.normal_scale,
            base_layer.normal_offset
        )
        
        # Set Preview Mode Int
        # 0 = Standard, 1 = With Normal Map
        mode_int = 1 if base_layer.preview_mode == "With Normal Map" else 0
        self.engine.set_preview_mode(mode_int)

    def _update_all_geometry(self, mode):
        vertices, indices = [], []
        
        if mode == "Standard":
            # Single Sphere
            vertices, indices = GeometryEngine.generate_sphere()
            
        elif mode == "With Normal Map":
            # Side-by-Side Spheres
            vertices, indices = GeometryEngine.generate_comparison_spheres()
            
        else:
            # Fallback
            vertices, indices = GeometryEngine.generate_sphere()
            
        # Update all layers
        # TODO: Handle multi-threading if ever needed, but for now main thread
        # We need CURRENT OpenGL Context?
        # update_geometry mainly writes to arrays? No, it buffers data to GPU using GL calls.
        # So we MUST be in context. _update_global_state is called in paintGL (Context Active).
        for layer in self.layer_stack:
            layer.update_geometry(vertices, indices)
            
    def _load_normal_map(self, path):
        self.current_normal_path = path
        if self.normal_map_id:
            glDeleteTextures([self.normal_map_id])
            self.normal_map_id = None
            
        if not path or not os.path.exists(path):
            return

        try:
            img = Image.open(path)
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
            img_data = img.convert("RGB").tobytes() # Normals don't need alpha usually
            w, h = img.size
            
            self.normal_map_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.normal_map_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
            glGenerateMipmap(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, 0)
            
            print(f"Loaded Normal Map: {path}")
            
        except Exception as e:
            print(f"Failed to load normal map {path}: {e}")

        
    def initializeGL(self):
        print(f"PreviewWidget: InitializeGL called. Context: {self.context()}")
        try:
            # Initialize Engine (FBOs)
            self.engine.initialize()
            
            # Initialize Layers
            for layer in self.layer_stack:
                try:
                    layer.initialize()
                except Exception as e:
                    print(f"ERROR initializing layer {layer.name}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Initialize Screen Quad
            self._init_quad()
            
        except Exception as e:
             print(f"CRITICAL ERROR in initializeGL: {e}")
             import traceback
             traceback.print_exc()

    def resizeGL(self, w, h):
        self.engine.resize(w, h)
        # We don't change viewport here directly because paintGL might need custom viewport for aspect ratio
        self.width_ = w
        self.height_ = h

    def paintGL(self):
        # Save the QOpenGLWidget's FBO (it might not be 0!)
        default_fbo = glGetIntegerv(GL_FRAMEBUFFER_BINDING)
        
        # Check Updates
        self._update_global_state()
        
        # Lazy Init Fallback
        if not self.quad_shader:
            if not hasattr(self, "_warned_shader"):
                print("WARNING: Quad Shader is None in paintGL. Attempting lazy init...")
                self._warned_shader = True
                self._init_quad()

        # Check for uninitialized layers (e.g. newly duplicated)
        for layer in self.layer_stack:
            if not hasattr(layer, 'shader_program') or layer.shader_program is None:
                try:
                    # We are in PaintGL, so Context is Active
                    layer.initialize()
                    # Also sync geometry
                    layer.update_geometry(*GeometryEngine.generate_sphere() if self.current_shape_name=="Standard" else GeometryEngine.generate_comparison_spheres())
                except Exception as e:
                    print(f"Error lazy-initializing layer {layer.name}: {e}")

        # 1. Render Layers to FBO via Engine
        # print("Render Stack") 
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
        
        try:
            # Construct absolute path to ensure headers are found
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # base_dir should be .../src
            # shaders are in .../src/shaders
            vert_path = os.path.join(base_dir, "shaders", "quad.vert")
            frag_path = os.path.join(base_dir, "shaders", "quad.frag")
            
            print(f"Loading shaders from: {vert_path}")
            
            if not os.path.exists(vert_path):
                print(f"ERROR: Vertex shader not found at {vert_path}")
            if not os.path.exists(frag_path):
                print(f"ERROR: Fragment shader not found at {frag_path}")

            with open(vert_path, "r", encoding="utf-8") as f: vert_src = f.read()
            with open(frag_path, "r", encoding="utf-8") as f: frag_src = f.read()
            
            vs = shaders.compileShader(vert_src, GL_VERTEX_SHADER)
            fs = shaders.compileShader(frag_src, GL_FRAGMENT_SHADER)
            self.quad_shader = shaders.compileProgram(vs, fs)
            print(f"Quad Shader Compiled Successfully: {self.quad_shader}")
        except Exception as e:
            print(f"Quad Shader FATAL error: {e}")
            import traceback
            traceback.print_exc()

    def save_render(self, path):
        # Use Settings for resolution
        settings = Settings()
        res = settings.export_resolution
        
        self.makeCurrent()
        try:
            # FORCE STANDARD GEOMETRY FOR EXPORT
            # We must update all layers to use the standard sphere geometry temporarily
            # to ensure the export is perfect even if view is Comparison/Cube.
            
            # 1. Save current state
            old_shape = self.current_shape_name
            
            # 2. Force Standard Geometry
            # Note: We don't change self.current_shape_name visually to avoid UI flicker if possible,
            # but since we are blocking main thread, it's fine.
            verts, inds = GeometryEngine.generate_sphere() # Default radius 1.0 now
            
            for layer in self.layer_stack:
                layer.update_geometry(verts, inds)
                
            # 3. Render Offscreen via Engine with Override Mode = 0 (Standard) and Force No Normal
            image = self.engine.render_offscreen(res, res, self.layer_stack, preview_mode_override=0, force_no_normal=True)
            
            if image and not image.isNull():
                image.save(path)
                print(f"Saved render to {path} ({res}x{res})")
            else:
                print("Failed to capture render.")
                
            # 4. Restore Geometry (if needed)
            if old_shape != "Standard":
                # Restore to whatever it was
                self._update_all_geometry(old_shape)
            else:
                # WAS Standard, but we regenerated it anyway. No harm keeping it.
                pass
                
        except Exception as e:
            print(f"Save Render Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.doneCurrent()

