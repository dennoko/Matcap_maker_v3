from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout, QComboBox
from PySide6.QtCore import Qt, Signal # Added Signal
from src.layers.base_layer import BaseLayer
from src.layers.spot_light_layer import SpotLightLayer
from src.layers.fresnel_layer import FresnelLayer
from src.layers.spot_light_layer import SpotLightLayer
from src.layers.noise_layer import NoiseLayer
from src.layers.image_layer import ImageLayer
from src.layers.adjustment_layer import AdjustmentLayer
from src.ui.params import FloatSlider, ColorPicker

from src.core.i18n import tr

def get_translated_name(name):
    # Mapping for Properties Header
    map_ = {
        "Base Layer": "layer.base",
        "Spot Light": "layer.type.spot",
        "Fresnel Layer": "layer.type.fresnel",
        "Noise Layer": "layer.type.noise",
        "Image Layer": "layer.type.image",
        "Adjustment Layer": "layer.type.adjustment"
    }
    key = map_.get(name)
    if key:
        return tr(key)
    return name

class PropertiesWidget(QWidget):
    propertyChanged = Signal() # New Signal

    def __init__(self):
        super().__init__()
        # Main layout holds the content widget
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignTop)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Container for dynamic content
        self.content_widget = QWidget()
        self.main_layout.addWidget(self.content_widget)
        self.current_layer = None
        
    def set_layer(self, layer):
        self.current_layer = layer
        
        # 1. Remove old content widget
        self.main_layout.removeWidget(self.content_widget)
        self.content_widget.deleteLater()
        
        # 2. Create new content widget
        self.content_widget = QWidget()
        self.main_layout.addWidget(self.content_widget)
        
        if not layer:
            return
            
        # 3. Build new layout
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setAlignment(Qt.AlignTop)
        
        # Common Header
        display_name = get_translated_name(layer.name)
        self.layout.addWidget(QLabel(tr("prop.header", name=display_name)))
        
        # Dynamic based on type (simplest way for now)
        form = QFormLayout()
        self.layout.addLayout(form)
        
        if isinstance(layer, BaseLayer):
            self._add_color_control(form, tr("prop.color"), layer.base_color, lambda v: self._update_whole_color(layer.base_color, v, layer))
            
            # Preview Settings
            self.layout.addWidget(QLabel(tr("prop.preview_options"))) # Changed label as requested
            sub_form = QFormLayout()
            self.layout.addLayout(sub_form)
            
            # Preview Mode Selector
            modes = ["Standard", "With Normal Map"]
            # Map old "Sphere"/"Combined" values if any? No, we reset default to "Standard".
            # Just ensure UI sets 'preview_mode'.
            self._add_combo_control(sub_form, tr("prop.mode"), modes, layer.preview_mode, lambda v: self._set_attr(layer, 'preview_mode', v))
            self._add_file_picker(sub_form, tr("prop.normal_map"), layer.normal_map_path, lambda path: self._set_normal_map(layer, path))
            
            # Normal Map Tweaks
            self._add_float_control(sub_form, tr("prop.strength"), layer.normal_strength, 0.0, 5.0, lambda v: self._set_attr(layer, 'normal_strength', v))
            self._add_float_control(sub_form, tr("prop.scale"), layer.normal_scale, 0.1, 10.0, lambda v: self._set_attr(layer, 'normal_scale', v))
            self._add_float_control(sub_form, tr("prop.offset_x"), layer.normal_offset[0], -1.0, 1.0, lambda v: self._update_list(layer.normal_offset, 0, v, layer))
            self._add_float_control(sub_form, tr("prop.offset_y"), layer.normal_offset[1], -1.0, 1.0, lambda v: self._update_list(layer.normal_offset, 1, v, layer))
            
        else:
            # Common properties for all effect layers
            self._add_blend_mode_control(form, layer)
            
            if isinstance(layer, SpotLightLayer):
                self._add_float_control(form, tr("prop.intensity"), layer.intensity, 0.0, 5.0, lambda v: self._set_attr(layer, 'intensity', v))
                self._add_float_control(form, tr("prop.range"), layer.range, 0.0, 1.0, lambda v: self._set_attr(layer, 'range', v))
                self._add_float_control(form, tr("prop.blur"), layer.blur, 0.0, 1.0, lambda v: self._set_attr(layer, 'blur', v))
                
                self._add_float_control(form, tr("prop.scale_x"), layer.scale_x, 0.1, 5.0, lambda v: self._set_attr(layer, 'scale_x', v))
                self._add_float_control(form, tr("prop.scale_y"), layer.scale_y, 0.1, 5.0, lambda v: self._set_attr(layer, 'scale_y', v))
                self._add_float_control(form, tr("prop.rotation"), layer.rotation, 0.0, 360.0, lambda v: self._set_attr(layer, 'rotation', v))
                
                self._add_float_control(form, tr("prop.direction_x"), layer.direction[0], -1.0, 1.0, lambda v: self._update_list(layer.direction, 0, v, layer))
                self._add_float_control(form, tr("prop.direction_y"), layer.direction[1], -1.0, 1.0, lambda v: self._update_list(layer.direction, 1, v, layer))
                self._add_float_control(form, tr("prop.direction_z"), layer.direction[2], -1.0, 1.0, lambda v: self._update_list(layer.direction, 2, v, layer))
                self._add_color_control(form, tr("prop.color"), layer.color, lambda v: self._update_whole_color(layer.color, v, layer))

            elif isinstance(layer, FresnelLayer):
                self._add_float_control(form, tr("prop.intensity"), layer.intensity, 0.0, 5.0, lambda v: self._set_attr(layer, 'intensity', v))
                self._add_float_control(form, tr("prop.power"), layer.power, 0.0, 20.0, lambda v: self._set_attr(layer, 'power', v))
                self._add_float_control(form, tr("prop.bias"), layer.bias, -1.0, 1.0, lambda v: self._set_attr(layer, 'bias', v))
                self._add_color_control(form, tr("prop.color"), layer.color, lambda v: self._update_whole_color(layer.color, v, layer))

            elif isinstance(layer, ImageLayer):
                # Image Layer
                self._add_file_picker(form, tr("prop.image"), layer.image_path, lambda path: self._set_attr(layer, 'image_path', path))
                self._add_combo_control(form, tr("prop.mapping"), ["UV", "Planar"], layer.mapping_mode, lambda v: self._set_attr(layer, 'mapping_mode', v))
                self._add_float_control(form, tr("prop.offset_x"), layer.offset[0], -1.0, 1.0, lambda v: self._update_list(layer.offset, 0, v, layer))
                self._add_float_control(form, tr("prop.offset_y"), layer.offset[1], -1.0, 1.0, lambda v: self._update_list(layer.offset, 1, v, layer))
                self._add_float_control(form, tr("prop.scale"), layer.scale, 0.1, 5.0, lambda v: self._set_attr(layer, 'scale', v))
                self._add_float_control(form, tr("prop.rotation"), layer.rotation, 0.0, 360.0, lambda v: self._set_attr(layer, 'rotation', v))
                self._add_float_control(form, tr("prop.blur"), layer.blur, 0.0, 1.0, lambda v: self._set_attr(layer, 'blur', v))
                self._add_float_control(form, tr("prop.opacity"), layer.opacity, 0.0, 1.0, lambda v: self._set_attr(layer, 'opacity', v))
                
            elif isinstance(layer, AdjustmentLayer):
                self._add_float_control(form, tr("prop.hue"), layer.hue, -0.5, 0.5, lambda v: self._set_attr(layer, 'hue', v))
                self._add_float_control(form, tr("prop.saturation"), layer.saturation, 0.0, 2.0, lambda v: self._set_attr(layer, 'saturation', v))
                self._add_float_control(form, tr("prop.brightness"), layer.brightness, -1.0, 1.0, lambda v: self._set_attr(layer, 'brightness', v))
                self._add_float_control(form, tr("prop.contrast"), layer.contrast, 0.0, 2.0, lambda v: self._set_attr(layer, 'contrast', v))

            elif isinstance(layer, NoiseLayer):
                self._add_float_control(form, tr("prop.intensity"), layer.intensity, 0.0, 1.0, lambda v: self._set_attr(layer, 'intensity', v))
                self._add_float_control(form, tr("prop.scale"), layer.scale, 0.1, 10.0, lambda v: self._set_attr(layer, 'scale', v))
                self._add_float_control(form, tr("prop.seed_offset"), layer.seed, 0, 100, lambda v: self._regen_noise(layer, v)) # Hacky seed change
                self._add_color_control(form, tr("prop.color"), layer.color, lambda v: self._update_whole_color(layer.color, v, layer))
                
    def _regen_noise(self, layer, val):
        layer.seed = int(val)
        layer.regenerate()
        self.propertyChanged.emit()

    def _add_blend_mode_control(self, layout, layer):
        combo = QComboBox()
        modes = [
            "Normal", "Add", "Multiply", "Screen", 
            "Subtract", "Lighten", "Darken",
            "Overlay", "Soft Light", "Hard Light",
            "Color Dodge", "Difference"
        ]
        combo.addItems(modes)
        idx = combo.findText(layer.blend_mode)
        if idx >= 0:
            combo.setCurrentIndex(idx)
            
        def on_change(text):
            setattr(layer, 'blend_mode', text)
            self.propertyChanged.emit()
            
        combo.currentTextChanged.connect(on_change)
        layout.addRow(tr("prop.blend_mode"), combo)

    def _add_color_control(self, layout, label, current_val, callback):
        # current_val is [r, g, b] float
        picker = ColorPicker(current_val)
        picker.colorChanged.connect(callback)
        layout.addRow(label, picker)
        
    def _add_float_control(self, layout, label, value, min_v, max_v, callback):
        slider = FloatSlider(value, min_v, max_v)
        slider.valueChanged.connect(callback)
        layout.addRow(label, slider)

    def _set_attr(self, obj, name, val):
        setattr(obj, name, val)
        self.propertyChanged.emit()
        
    def _update_list(self, target, idx, val, layer):
        target[idx] = val
        self.propertyChanged.emit()
        
    def _set_image_path(self, layer, path):
        layer.image_path = path
        # Trigger reload immediately if possible, but layer handles logic in render loop or we can explicit call
        layer.load_texture(path)
        self.propertyChanged.emit()

    def _set_normal_map(self, layer, path):
         layer.normal_map_path = path
         # No immediate reload method on BaseLayer yet, logic will be handled in PreviewWidget
         # But maybe we should notify PreviewWidget?
         # Property changes are picked up next frame.
         self.propertyChanged.emit()
        
    def _add_file_picker(self, layout, label, current_path, callback):
        from PySide6.QtWidgets import QPushButton, QFileDialog
        import os
        
        btn_text = os.path.basename(current_path) if current_path else tr("btn.select_image")
        button = QPushButton(btn_text)
        
        def on_click():
            file_path, _ = QFileDialog.getOpenFileName(self, tr("dialog.select_image"), "", "Images (*.png *.jpg *.jpeg *.bmp)")
            if file_path:
                callback(file_path)
                button.setText(os.path.basename(file_path))
        
        button.clicked.connect(on_click)
        layout.addRow(label, button)

    def _add_combo_control(self, layout, label, options, current, callback):
        combo = QComboBox()
        combo.addItems(options)
        index = combo.findText(current)
        if index >= 0:
            combo.setCurrentIndex(index)
        combo.currentTextChanged.connect(callback)
        layout.addRow(label, combo)

    def _update_whole_color(self, target_list, new_color, layer):
        # Update R, G, B in place
        target_list[0] = new_color[0]
        target_list[1] = new_color[1]
        target_list[2] = new_color[2]
        self.propertyChanged.emit()
