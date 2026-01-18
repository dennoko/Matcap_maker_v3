from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QFileDialog, QMessageBox, QPushButton
from PySide6.QtCore import Qt, QTimer
from src.ui.preview_widget import PreviewWidget
from src.ui.layer_list import LayerListWidget
from src.ui.properties import PropertiesWidget
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

        # Padding Menu
        pad_menu = options_menu.addMenu("Padding")
        pads = [0, 2, 4, 8, 16, 32]
        self.pad_actions = {}
        
        current_pad = settings.export_padding
        pad_group = QActionGroup(self)
        
        for p in pads:
            act = QAction(f"{p}px", self, checkable=True)
            if p == current_pad:
                act.setChecked(True)
            act.triggered.connect(lambda checked, pad=p: self.set_padding(pad))
            pad_group.addAction(act)
            pad_menu.addAction(act)
            self.pad_actions[p] = act

        # Help Menu
        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("Third Party Notices")
        about_action.triggered.connect(self.show_about_dialog)

        # Main Components Initialization
        # 1. Preview (Needs to be created first for context/stack)
        self.preview = PreviewWidget()
        
        # 2. Layer List (Needs stack from preview)
        self.layer_list = LayerListWidget(self.preview.layer_stack)
        self.layer_list.add_layer_requested.connect(self.on_add_layer)
        self.layer_list.layer_selected.connect(self.on_layer_selected)
        
        # 3. Properties
        self.properties = PropertiesWidget()

        # --- Central Widget ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        # 1. Preview + Export (Center/Left Area) - Stretch 1
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        center_layout.addWidget(self.preview, 1) # Expand preview
        
        self.export_btn = QPushButton("Export Image")
        self.export_btn.setMinimumHeight(40) 
        self.export_btn.clicked.connect(self.export_image)
        center_layout.addWidget(self.export_btn, 0)
        
        self.main_layout.addWidget(center_container, 1) # This part expands

        # 2. Layer List (Middle Area) - Fixed Width
        layer_container = QFrame()
        layer_container.setFixedWidth(250)
        layer_layout = QVBoxLayout(layer_container)
        layer_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add a title/header for visuals (optional but consistent with Frame)
        # layer_layout.addWidget(QLabel("Layers")) 
        layer_layout.addWidget(self.layer_list)
        
        self.main_layout.addWidget(layer_container, 0) # Fixed width

        # 3. Properties (Right Area) - Fixed Width
        prop_container = QFrame()
        prop_container.setFixedWidth(350) 
        prop_layout = QVBoxLayout(prop_container)
        prop_layout.setContentsMargins(0, 0, 0, 0)
        prop_layout.addWidget(self.properties)
        
        self.main_layout.addWidget(prop_container, 0) # Fixed width

        # Update Logic (Event Driven)
        self.properties.propertyChanged.connect(self.request_render)
        self.properties.propertyChanged.connect(self.layer_list.update_active_layer_visuals) # Sync Colors/Names
        self.layer_list.layer_changed.connect(self.on_layer_changed)
        self.layer_list.stack_changed.connect(self.request_render)
        
        # Select Base Layer by default
        if self.preview.base_layer:
             self.layer_list.select_layer(self.preview.base_layer)
        
    def request_render(self):
        self.preview.update()

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
                self.request_render()
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
                # Success: Save Preview Image
                try:
                    from pathlib import Path
                    path_obj = Path(file_path)
                    if path_obj.suffix == '.json':
                        project_dir = path_obj.parent / path_obj.stem
                    else:
                        project_dir = path_obj
                        
                    preview_path = project_dir / "preview.png"
                    # Save a 512x512 preview with no padding
                    self.preview.save_render(str(preview_path), resolution=512, padding=0)
                    print(f"Project preview saved to {preview_path}")
                except Exception as e:
                    print(f"Failed to save project preview: {e}")
                    
                print("Project saved successfully.")

    def on_add_layer(self, layer_type):
        self.preview.makeCurrent()
        try:
            layer = None
            layer = None
            if layer_type == "spot":
                layer = SpotLightLayer()
            elif layer_type == "fresnel":
                layer = FresnelLayer()
            elif layer_type == "noise":
                layer = NoiseLayer()
            elif layer_type == "image":
                layer = ImageLayer()
            elif layer_type == "adjustment":
                from src.layers.adjustment_layer import AdjustmentLayer
                layer = AdjustmentLayer()
            
            if layer:
                # Insert after currently selected layer
                current_sel = self.properties.current_layer
                inserted = False
                if current_sel:
                    try:
                        layers = self.preview.layer_stack.get_layers()
                        if current_sel in layers:
                            idx = layers.index(current_sel)
                            self.preview.layer_stack.insert_layer(idx + 1, layer)
                            inserted = True
                    except Exception as e:
                        print(f"Insertion Error: {e}")
                
                if not inserted:
                    self.preview.layer_stack.add_layer(layer)

                layer.initialize()
        finally:
            self.preview.doneCurrent()
        self.layer_list.refresh()
        if layer:
            self.layer_list.select_layer(layer)
        self.request_render()

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
        
    def set_padding(self, pad):
        Settings().export_padding = pad
        print(f"Export padding set to {pad}px")
        
    def on_layer_selected(self, layer):
        self.properties.set_layer(layer)

    def on_layer_changed(self, layer):
        self.request_render()
        if self.properties.current_layer == layer:
             self.properties.set_layer(layer)
        
    def show_about_dialog(self):
        from src.ui.about_dialog import AboutDialog
        dlg = AboutDialog(self)
        dlg.exec()
