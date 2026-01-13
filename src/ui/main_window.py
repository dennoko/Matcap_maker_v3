from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QFileDialog
from PySide6.QtCore import Qt, QTimer
from src.ui.preview_widget import PreviewWidget
from src.ui.layer_list import LayerListWidget
from src.ui.properties import PropertiesWidget
from src.layers.light_layer import LightLayer
from src.layers.spot_light_layer import SpotLightLayer
from src.layers.fresnel_layer import FresnelLayer
from src.layers.noise_layer import NoiseLayer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Matcap Maker v3")
        self.resize(1200, 800)

        # Menu Bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        
        export_action = file_menu.addAction("Export Image")
        export_action.triggered.connect(self.export_image)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # 1. Left Panel: Layer List
        self.layer_list = None # Init after Preview since we need stack
        
        # 2. Center: Preview (Create first to get stack)
        self.preview = PreviewWidget()
        
        # Initialize Layer List with stack from preview
        self.layer_list = LayerListWidget(self.preview.layer_stack)
        self.layer_list.add_layer_requested.connect(self.on_add_layer)
        self.layer_list.layer_selected.connect(self.on_layer_selected)
        
        # 3. Right: Properties
        self.properties = PropertiesWidget()

        # Layout Assembly
        # Left (Layers)
        left_container = QFrame()
        left_layout = QVBoxLayout(left_container)
        left_layout.addWidget(self.layer_list)
        self.main_layout.addWidget(left_container, 1)

        # Center (Preview)
        self.main_layout.addWidget(self.preview, 3)

        # Right (Properties)
        right_container = QFrame()
        right_layout = QVBoxLayout(right_container)
        right_layout.addWidget(self.properties)
        self.main_layout.addWidget(right_container, 1)

        # Update Timer (Simple 60 FPS redraw to catch property changes)
        # Real app should use signals, but for V3 rapid dev, constant redraw is safer for smooth param preview
        self.timer = QTimer()
        self.timer.timeout.connect(self.preview.update)
        self.timer.start(16)

    def on_add_layer(self, layer_type):
        self.preview.makeCurrent()
        try:
            layer = None
            if layer_type == "light":
                layer = LightLayer()
            elif layer_type == "spot":
                layer = SpotLightLayer()
            elif layer_type == "fresnel":
                layer = FresnelLayer()
            elif layer_type == "noise":
                layer = NoiseLayer()
            
            if layer:
                self.preview.layer_stack.add_layer(layer)
                layer.initialize()
        finally:
            self.preview.doneCurrent()
        self.layer_list.refresh()
        if layer:
            self.layer_list.select_layer(layer)

    def export_image(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Image", "matcap.png", "Images (*.png *.jpg)")
        if file_path:
            # Add timestamp to filename if requested
            # User asked to "Add timestamp to end of name to avoid overlap"
            # But normally user chooses name in Dialog.
            # I will append timestamp automatically to the suggested name inside the logic OR just before save?
            # Actually, standard behavior is: User picks name. We might overwrite if exists.
            # User request: "timestmap added to exported name to avoid duplication".
            # This implies if I save "matcap.png", it becomes "matcap_20230101_120000.png".
            # But the Dialog asks for name.
            # I will modify the DEFAULT name in the dialog, or append it to the result.
            # Let's append it to the result before saving.
            
            import os
            from datetime import datetime
            
            root, ext = os.path.splitext(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = f"{root}_{timestamp}{ext}"
            
            self.preview.save_render(final_path)

    def on_layer_selected(self, layer):
        self.properties.set_layer(layer)
