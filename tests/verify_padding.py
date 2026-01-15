import sys
import os
import time
from PySide6.QtWidgets import QApplication
from PIL import Image
import numpy as np

# Add src to path
sys.path.append(os.getcwd())

from src.ui.preview_widget import PreviewWidget
from src.layers.base_layer import BaseLayer
from src.core.settings import Settings

def test_padding():
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
    
    # 1. Export with 0 padding
    Settings().export_padding = 0
    path_0 = os.path.abspath("tests/pad_0.png")
    if os.path.exists(path_0): os.remove(path_0)
    
    print("Exporting Pad 0...")
    preview.save_render(path_0)
    time.sleep(0.5)
    app.processEvents()
    
    # 2. Export with 32 padding
    Settings().export_padding = 32
    path_32 = os.path.abspath("tests/pad_32.png")
    if os.path.exists(path_32): os.remove(path_32)
    
    print("Exporting Pad 32...")
    preview.save_render(path_32)
    time.sleep(0.5)
    app.processEvents()
    preview.close()
    
    # Verification
    if not os.path.exists(path_0) or not os.path.exists(path_32):
        print("FAIL: Export files missing.")
        return False
        
    img0 = Image.open(path_0).convert("RGBA")
    img32 = Image.open(path_32).convert("RGBA")
    
    arr0 = np.array(img0)
    arr32 = np.array(img32)
    
    # Count non-zero alpha pixels
    count0 = np.sum(arr0[:, :, 3] > 0)
    count32 = np.sum(arr32[:, :, 3] > 0)
    
    print(f"Opaque Pixels - Pad 0: {count0}")
    print(f"Opaque Pixels - Pad 32: {count32}")
    
    if count32 > count0:
        print("PASS: Padding increased opaque area.")
        diff = count32 - count0
        print(f"Difference: {diff} pixels")
        return True
    else:
        print("FAIL: Padding did not increase opaque area.")
        return False

if __name__ == "__main__":
    if test_padding():
        sys.exit(0)
    else:
        sys.exit(1)
