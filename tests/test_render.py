import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import QSize
from src.core.engine import Engine
from src.core.layer_stack import LayerStack
from src.layers.base_layer import BaseLayer
from src.layers.fresnel_layer import FresnelLayer
from src.layers.noise_layer import NoiseLayer
from PIL import Image
from OpenGL.GL import *

class HeadlessRenderer(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.resize(512, 512)
        self.engine = Engine()
        self.layer_stack = LayerStack()
        
        # Setup Layers
        # 1. Base Layer (Dark Red to see Additive effects)
        self.base = BaseLayer()
        self.base.base_color = [0.2, 0.0, 0.0] 
        self.layer_stack.add_layer(self.base)
        
        # 2. Fresnel (Green, Add)
        self.fresnel = FresnelLayer()
        self.fresnel.color = [0.0, 1.0, 0.0]
        self.fresnel.blend_mode = "Add"
        self.layer_stack.add_layer(self.fresnel)
        
        # 3. Noise (Multiply, Gray)
        self.noise = NoiseLayer()
        self.noise.blend_mode = "Normal" # Test visibility first
        self.noise.intensity = 1.0
        self.layer_stack.add_layer(self.noise)
        
    def initializeGL(self):
        self.engine.initialize()
        for layer in self.layer_stack:
            layer.initialize()
            
    def paintGL(self):
        self.engine.resize(512, 512)
        self.engine.render(self.layer_stack)
        
        # Capture
        tex_id = self.engine.get_texture_id()
        glBindTexture(GL_TEXTURE_2D, tex_id)
        data = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_UNSIGNED_BYTE)
        img = Image.frombytes("RGBA", (512, 512), data)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        img.save("test_render_output.png")
        print("Render saved to test_render_output.png")
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = HeadlessRenderer()
    widget.show() # Must show to create context, but we will quit immediately after paint
    sys.exit(app.exec())
