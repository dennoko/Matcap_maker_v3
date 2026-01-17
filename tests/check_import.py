import sys
import os

# Add src to path
sys.path.append(os.getcwd())

try:
    print("Attempting to import AdjustmentLayer...")
    from src.layers.adjustment_layer import AdjustmentLayer
    print("Import successful:", AdjustmentLayer)
except Exception as e:
    print("Import failed:", e)
    import traceback
    traceback.print_exc()

print("Attempting to import ProjectIO...")
try:
    from src.core.project_io import ProjectIO
    print("ProjectIO Import successful")
except Exception as e:
    print("ProjectIO Import failed:", e)
    import traceback
    traceback.print_exc()
