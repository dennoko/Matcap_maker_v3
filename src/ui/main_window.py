from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame
from PySide6.QtCore import Qt, QTimer
from src.ui.preview_widget import PreviewWidget
from src.ui.layer_list import LayerListWidget
from src.ui.properties import PropertiesWidget
from src.layers.light_layer import LightLayer
from src.layers.spot_light_layer import SpotLightLayer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Matcap Maker v3")
        self.resize(1200, 800)

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
            
            if layer:
                self.preview.layer_stack.add_layer(layer)
                layer.initialize()
        finally:
            self.preview.doneCurrent()
        self.layer_list.refresh()
        if layer:
            self.layer_list.select_layer(layer)

    def on_layer_selected(self, layer):
        self.properties.set_layer(layer)
