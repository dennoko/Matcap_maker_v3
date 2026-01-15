import sys
import os
import time
from PySide6.QtWidgets import QApplication
from PIL import Image

# Add src to path
sys.path.append(os.getcwd())

from src.ui.preview_widget import PreviewWidget
from src.layers.base_layer import BaseLayer
from src.core.settings import Settings

def test_export():
    app = QApplication.instance() or QApplication(sys.argv)
    
    preview = PreviewWidget()
    preview.show() # Must show to initialize GL
    
    # Wait for GL init
    time.sleep(1.0)
    app.processEvents()
    
    # Setup Layers: Pure White Base Layer
    preview.layer_stack.clear()
    
    base_layer = BaseLayer()
    base_layer.base_color = [1.0, 1.0, 1.0] # White
    base_layer.metallic = 0.0
    base_layer.roughness = 1.0 # Minimize specular
    # Ensure no shadows or lighting
    # Add ambient or disable lighting? 
    # BaseLayer implementation is Unlit if just color?
    # Let's check layer_base.frag: "FragColor = vec4(baseColor, 1.0);" 
    # Yes, it is unlit flat color. Perfect.
    
    preview.layer_stack.add_layer(base_layer)
    base_layer.initialize()
    
    # Set Resolution
    Settings().export_resolution = 512
    
    # Export
    output_path = os.path.abspath("tests/test_output.png")
    if os.path.exists(output_path):
        os.remove(output_path)
        
    print("Exporting...")
    # Force preview mode to comparison to test the override
    preview.current_shape_name = "With Normal Map" 
    preview.engine.set_preview_mode(1)
    
    preview.save_render(output_path)
    
    app.processEvents()
    preview.close()
    
    if not os.path.exists(output_path):
        print("FAIL: Output file not created.")
        return False
        
    # Verify Image
    img = Image.open(output_path)
    img = img.convert("RGBA")
    width, height = img.size
    print(f"Image Size: {width}x{height}")
    
    # Analyze Coverage
    # Find bounding box of non-transparent/non-black pixels
    # Since background is black (0,0,0,0) or (0,0,0,1)?
    # Engine.render_offscreen clears to Transparent Black (0,0,0,0).
    # Matcap sphere is White (1,1,1,1).
    
    bbox = img.getbbox() # Returns (left, upper, right, lower)
    print(f"Bounding Box: {bbox}")
    
    if bbox is None:
        print("FAIL: Image is empty.")
        return False
        
    # Check margins
    left, upper, right, lower = bbox
    
    margin_left = left
    margin_top = upper
    margin_right = width - right
    margin_bottom = height - lower
    
    print(f"Margins: L={margin_left}, T={margin_top}, R={margin_right}, B={margin_bottom}")
    
    # Expectation: 0 margins (or very close, e.g., 0-1 px due to antialiasing)
    # Since radius is 1.0, it should touch edges.
    
    max_margin = 1
    if margin_left > max_margin or margin_top > max_margin or margin_right > max_margin or margin_bottom > max_margin:
        print("FAIL: Margins are too large. Sphere is not filling the frame.")
        return False
        
    print("PASS: Margins are acceptable.")
    
    # Check Shape (Aspect Ratio of bbox should be 1.0)
    w_box = right - left
    h_box = lower - upper
    ratio = w_box / h_box
    print(f"BBox Aspect Ratio: {ratio:.4f}")
    
    if abs(ratio - 1.0) > 0.02:
        print("FAIL: Shape is not square (not a sphere?)")
        return False
        
    return True

if __name__ == "__main__":
    success = test_export()
    if success:
        print("TEST PASSED")
        sys.exit(0)
    else:
        print("TEST FAILED")
        sys.exit(1)
