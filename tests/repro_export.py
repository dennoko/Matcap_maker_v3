
import sys
import os
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import QSize
from PIL import Image

# Add src to path
sys.path.append(os.getcwd())

from src.core.engine import Engine
from src.core.layer_stack import LayerStack
from src.layers.base_layer import BaseLayer
from src.core.geometry import GeometryEngine

class TestWidget(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.resize(500, 500)
        self.engine = None
    
    def initializeGL(self):
        self.engine = Engine()
        self.engine.initialize()
        
    def paintGL(self):
        pass # Not needed for offscreen test

def test_export_size():
    app = QApplication(sys.argv)
    
    widget = TestWidget()
    widget.show() # Need to show to get context?
    
    # Process events to let init happen
    app.processEvents()
    
    # Make sure we have context
    widget.makeCurrent()
    
    if not widget.engine:
        print("Engine not initialized!")
        return
        
    engine = widget.engine
    
    # Create Stack
    stack = LayerStack()
    layer = BaseLayer()
    layer.preview_mode = "Standard"
    layer.base_color = [1.0, 1.0, 1.0] # White
    
    # Force init layer
    layer.initialize()
    stack.add_layer(layer)
    
    # Geometry (Radius 1.0)
    v, i = GeometryEngine.generate_sphere(radius=1.0)
    layer.update_geometry(v, i)
    
    # Render Offscreen 2048x2048
    res = 2048
    print(f"Rendering at {res}x{res}...")
    qimg = engine.render_offscreen(res, res, stack, preview_mode_override=0, force_no_normal=True)
    
    if qimg.isNull():
        print("Failed to render image.")
        return
        
    print(f"Output Image Size: {qimg.width()}x{qimg.height()}")
    
    # Check Content Size (Measure White Circle)
    # Convert to PIL
    ptr = qimg.constBits()
    bpl = qimg.bytesPerLine()
    h = qimg.height()
    w = qimg.width()
    
    # Simple check: Middle Row
    # Row index 1024
    mid_y = h // 2
    
    # Access pixel data manually or save and reload
    # Let's save to temp file to verify manually or use PIL
    temp_path = "test_export_2048.png"
    qimg.save(temp_path)
    print(f"Saved to {temp_path}")
    
    with Image.open(temp_path) as img:
        arr = np.array(img)
        # Check middle row alpha or color
        # White sphere on black background (Engine clears to transparent, wait, Engine clears to 0,0,0,0)
        # BaseLayer renders Opaque White?
        # Let's check where the first non-zero pixel is in middle row.
        
        mid_row = arr[mid_y]
        # mid_row shape (2048, 4) or (2048, 3)
        
        non_zero = np.where(mid_row[:, 3] > 0)[0] if mid_row.shape[1] == 4 else np.where(mid_row[:, 0] > 0)[0]
        
        if len(non_zero) == 0:
            print("Image is empty!")
        else:
            start = non_zero[0]
            end = non_zero[-1]
            diameter = end - start
            print(f"Sphere Diameter in pixels: {diameter}")
            print(f"Expected Diameter: ~{res} (Full Width)")
            
            relative_size = diameter / res
            print(f"Relative Size: {relative_size:.2f}")
            
    widget.close()

if __name__ == "__main__":
    test_export_size()
