import sys
import os

# Add src to path
sys.path.append(os.getcwd())

# 1. Trigger Registration via import
import src.main
from src.core.layer_registry import LayerRegistry

print("=== Verifying Layer Registry ===")
names = LayerRegistry.get_registered_names()
print(f"Registered Layers: {names}")

expected = ["BaseLayer", "SpotLightLayer", "FresnelLayer", "NoiseLayer", "ImageLayer", "AdjustmentLayer"]
missing = [x for x in expected if x not in names]

if missing:
    print(f"FAIL: Missing layers: {missing}")
    sys.exit(1)

print("PASS: All expected layers registered.")

# 2. Verify Instantiation
print("\n=== Verifying Instantiation ===")
for name in names:
    try:
        instance = LayerRegistry.create(name)
        if instance is None:
            print(f"FAIL: Failed to create {name}")
            sys.exit(1)
        print(f"Created {name}: {instance}")
    except Exception as e:
        print(f"FAIL: Exception creating {name}: {e}")
        sys.exit(1)

print("PASS: All layers instantiated.")

# 3. Verify ProjectIO via Registry (Mock)
from src.core.project_io import ProjectIO
print("\n=== Verifying ProjectIO Integration ===")

# Create a mock layer stack
stack = []
l1 = LayerRegistry.create("BaseLayer")
l1.name = "My Base"
stack.append(l1)

l2 = LayerRegistry.create("SpotLightLayer")
l2.name = "My Spot"
stack.append(l2)

# Save to temp file
import tempfile
import shutil
import json

details = []

try:
    tmp_dir = tempfile.mkdtemp()
    project_path = os.path.join(tmp_dir, "test_proj.json")
    
    print(f"Saving to {project_path}...")
    success, errs = ProjectIO.save_project(project_path, stack)
    if not success:
        print(f"FAIL: Save failed: {errs}")
        sys.exit(1)
        
    print("Save successful. Loading back...")
    
    # Logic in ProjectIO: valid project file is project_dir/project.json
    # save_project(".../test_proj.json") -> creates dir ".../test_proj" -> saves ".../test_proj/project.json"
    real_load_path = os.path.join(tmp_dir, "test_proj", "project.json")
    
    loaded_layers = ProjectIO.load_project(real_load_path, None)
    
    if loaded_layers is None:
        print("FAIL: Load returned None")
        sys.exit(1)
        
    if len(loaded_layers) != 2:
        print(f"FAIL: Expected 2 layers, got {len(loaded_layers)}")
        sys.exit(1)
        
    if loaded_layers[0].name != "My Base":
         print(f"FAIL: Layer 0 name mismatch: {loaded_layers[0].name}")
         sys.exit(1)

    if not isinstance(loaded_layers[1], LayerRegistry.get_class("SpotLightLayer")):
         print("FAIL: Layer 1 type mismatch.")
         sys.exit(1)

    print("PASS: ProjectIO Save/Load working with Registry.")

finally:
    if 'tmp_dir' in locals():
        try:
            shutil.rmtree(tmp_dir)
        except:
            pass

print("\n=== PHASE 1 VERIFICATION COMPLETE === ")
