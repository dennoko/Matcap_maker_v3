import sys
import os
import time
from PySide6.QtWidgets import QApplication
from PIL import Image
import numpy as np
from PySide6.QtGui import QColor

# Add src to path
sys.path.append(os.getcwd())

from src.ui.preview_widget import PreviewWidget
from src.layers.base_layer import BaseLayer
from src.core.settings import Settings

def test_padding_and_fill():
    app = QApplication.instance() or QApplication(sys.argv)
    
    preview = PreviewWidget()
    preview.show() 
    time.sleep(0.5)
    app.processEvents()
    
    # Setup
    preview.layer_stack.clear()
    base_layer = BaseLayer()
    base_layer.base_color = [1.0, 1.0, 1.0] # White
    preview.layer_stack.add_layer(base_layer)
    base_layer.initialize()
    
    Settings().export_resolution = 512
    Settings().export_padding = 10 # Some padding
    
    path = os.path.abspath("tests/pad_fill.png")
    if os.path.exists(path): os.remove(path)
    
    print("Exporting Pad 10 with Black Fill...")
    preview.save_render(path)
    time.sleep(0.5)
    app.processEvents()
    preview.close()
    
    # Verification
    if not os.path.exists(path):
        print("FAIL: Export file missing.")
        return False
        
    img = Image.open(path).convert("RGBA")
    arr = np.array(img)
    
    # Check Corner (Usually transparent background)
    corner = arr[0, 0] # Top Left
    print(f"Corner Pixel: {corner}")
    
    # Expectation: Black Opaque (0, 0, 0, 255) because of the new fill logic
    # Previously it would be (0,0,0,0)
    
    if corner[3] == 255 and corner[0] == 0 and corner[1] == 0 and corner[2] == 0:
        print("PASS: Background is OPOQUE BLACK.")
        return True
    else:
        print(f"FAIL: Background is NOT opaque black. Got {corner}")
        return False

if __name__ == "__main__":
    if test_padding_and_fill():
        sys.exit(0)
    else:
        sys.exit(1)
