from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QFileDialog, QMessageBox
from PySide6.QtCore import Qt, QTimer
from src.ui.preview_widget import PreviewWidget
from src.ui.layer_list import LayerListWidget
from src.ui.properties import PropertiesWidget
from src.layers.light_layer import LightLayer
from src.layers.spot_light_layer import SpotLightLayer
from src.layers.fresnel_layer import FresnelLayer
from src.layers.fresnel_layer import FresnelLayer
from src.layers.noise_layer import NoiseLayer
from src.layers.image_layer import ImageLayer
from src.core.project_io import ProjectIO
from src.core.settings import Settings
import os
from datetime import datetime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Matcap Maker v3")
        self.resize(1200, 800)

        # Menu Bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        
        load_action = file_menu.addAction("Open Project...")
        load_action.triggered.connect(self.load_project)
        
        save_action = file_menu.addAction("Save Project...")
        save_action.triggered.connect(self.save_project)

        file_menu.addSeparator()
        
        export_action = file_menu.addAction("Export Image")
        export_action.triggered.connect(self.export_image)

        # Options Menu
        options_menu = menubar.addMenu("Options")
        res_menu = options_menu.addMenu("Resolution")
        
        resolutions = [64, 128, 256, 512, 1024, 2048, 4096]
        self.res_actions = {}
        
        settings = Settings()
        current_res = settings.export_resolution
        
        from PySide6.QtGui import QAction, QActionGroup
        res_group = QActionGroup(self)
        
        for r in resolutions:
            act = QAction(f"{r}x{r}", self, checkable=True)
            if r == current_res:
                act.setChecked(True)
            act.triggered.connect(lambda checked, res=r: self.set_resolution(res))
            res_group.addAction(act)
            res_menu.addAction(act)
            self.res_actions[r] = act

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
        right_container.setFixedWidth(400) # Fixed width as requested by user
        right_layout = QVBoxLayout(right_container)
        right_layout.addWidget(self.properties)
        self.main_layout.addWidget(right_container, 0) # 0 stretch factor since fixed width

        # Update Timer (Simple 60 FPS redraw to catch property changes)
        # Real app should use signals, but for V3 rapid dev, constant redraw is safer for smooth param preview
        self.timer = QTimer()
        self.timer.timeout.connect(self.preview.update)
        self.timer.start(16)

    def load_project(self):
        start_dir = Settings().get_projects_dir()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Project", start_dir, "JSON Files (*.json)")
        if not file_path:
            return
            
        # Ensure Context
        self.preview.makeCurrent()
        try:
            # Load new layers
            new_layers = ProjectIO.load_project(file_path, None)
            
            if new_layers is not None:
                # Clear and Replace
                self.preview.layer_stack.clear()
                for layer in new_layers:
                    self.preview.layer_stack.add_layer(layer)
                    layer.initialize() # Re-init GL resources (shaders/buffers)
                
                # Update UI
                self.layer_list.refresh()
                self.properties.set_layer(None) # Clear property panel
                print(f"Project loaded from {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project:\n{e}")
        finally:
            self.preview.doneCurrent()

    def save_project(self):
        start_dir = Settings().get_projects_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"project_{timestamp}.json"
        full_path = os.path.join(start_dir, default_name)
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Project", full_path, "JSON Files (*.json)")
        if file_path:
            success, errors = ProjectIO.save_project(file_path, self.preview.layer_stack)
            
            if not success:
                QMessageBox.critical(self, "Error", f"Failed to save project:\n{errors}")
            elif errors:
                # Partial success (copy failed)
                msg = "Project saved, but some assets could not be copied:\n" + "\n".join(errors)
                QMessageBox.warning(self, "Warning", msg)
            else:
                print("Project saved successfully.")

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
            elif layer_type == "image":
                layer = ImageLayer()
            
            if layer:
                self.preview.layer_stack.add_layer(layer)
                layer.initialize()
        finally:
            self.preview.doneCurrent()
        self.layer_list.refresh()
        if layer:
            self.layer_list.select_layer(layer)

    def export_image(self):
        start_dir = Settings().get_output_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"matcap_{timestamp}.png"
        full_path = os.path.join(start_dir, default_name)
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Image", full_path, "Images (*.png *.jpg)")
        if file_path:
            self.preview.save_render(file_path)

    def set_resolution(self, res):
        Settings().export_resolution = res
        print(f"Export resolution set to {res}")
        
    def on_layer_selected(self, layer):
        self.properties.set_layer(layer)
