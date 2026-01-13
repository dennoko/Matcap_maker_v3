from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout, QComboBox
from PySide6.QtCore import Qt
from src.layers.base_layer import BaseLayer
from src.layers.light_layer import LightLayer
from src.layers.spot_light_layer import SpotLightLayer
from src.layers.fresnel_layer import FresnelLayer
from src.layers.spot_light_layer import SpotLightLayer
from src.layers.noise_layer import NoiseLayer
from src.ui.params import FloatSlider, ColorPicker

class PropertiesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.current_layer = None
        self.layout.setAlignment(Qt.AlignTop)
        
    def set_layer(self, layer):
        self.current_layer = layer
        # Clear existing controls properly
        self._clear_layout(self.layout)
                
        if not layer:
            return
            
        # Common Header
        self.layout.addWidget(QLabel(f"Properties: {layer.name}"))
        
        # Dynamic based on type (simplest way for now)
        form = QFormLayout()
        self.layout.addLayout(form)
        
        if isinstance(layer, BaseLayer):
            self._add_color_control(form, "Color", layer.base_color, lambda v: self._update_whole_color(layer.base_color, v, layer))
            
        else:
            # Common properties for all effect layers
            self._add_blend_mode_control(form, layer)
            
            if isinstance(layer, LightLayer):
                self._add_float_control(form, "Intensity", layer.intensity, 0.0, 5.0, lambda v: self._set_attr(layer, 'intensity', v))
                self._add_float_control(form, "Dir X", layer.direction[0], -1.0, 1.0, lambda v: self._update_list(layer.direction, 0, v, layer))
                self._add_float_control(form, "Dir Y", layer.direction[1], -1.0, 1.0, lambda v: self._update_list(layer.direction, 1, v, layer))
                self._add_float_control(form, "Dir Z", layer.direction[2], -1.0, 1.0, lambda v: self._update_list(layer.direction, 2, v, layer))
                self._add_color_control(form, "Color", layer.color, lambda v: self._update_whole_color(layer.color, v, layer))

            elif isinstance(layer, SpotLightLayer):
                self._add_float_control(form, "Intensity", layer.intensity, 0.0, 5.0, lambda v: self._set_attr(layer, 'intensity', v))
                self._add_float_control(form, "Range", layer.range, 0.0, 1.0, lambda v: self._set_attr(layer, 'range', v))
                self._add_float_control(form, "Blur", layer.blur, 0.0, 1.0, lambda v: self._set_attr(layer, 'blur', v))
                self._add_float_control(form, "Dir X", layer.direction[0], -1.0, 1.0, lambda v: self._update_list(layer.direction, 0, v, layer))
                self._add_float_control(form, "Dir Y", layer.direction[1], -1.0, 1.0, lambda v: self._update_list(layer.direction, 1, v, layer))
                self._add_float_control(form, "Dir Z", layer.direction[2], -1.0, 1.0, lambda v: self._update_list(layer.direction, 2, v, layer))
                self._add_color_control(form, "Color", layer.color, lambda v: self._update_whole_color(layer.color, v, layer))

            elif isinstance(layer, FresnelLayer):
                self._add_float_control(form, "Intensity", layer.intensity, 0.0, 5.0, lambda v: self._set_attr(layer, 'intensity', v))
                self._add_float_control(form, "Power", layer.power, 0.0, 20.0, lambda v: self._set_attr(layer, 'power', v))
                self._add_float_control(form, "Bias", layer.bias, -1.0, 1.0, lambda v: self._set_attr(layer, 'bias', v))
                self._add_color_control(form, "Color", layer.color, lambda v: self._update_whole_color(layer.color, v, layer))

            elif isinstance(layer, NoiseLayer):
                self._add_float_control(form, "Intensity", layer.intensity, 0.0, 1.0, lambda v: self._set_attr(layer, 'intensity', v))
                self._add_float_control(form, "Scale", layer.scale, 0.1, 10.0, lambda v: self._set_attr(layer, 'scale', v))
                self._add_float_control(form, "Seed Offset", layer.seed, 0, 100, lambda v: self._regen_noise(layer, v)) # Hacky seed change
                self._add_color_control(form, "Color", layer.color, lambda v: self._update_whole_color(layer.color, v, layer))
                
    def _regen_noise(self, layer, val):
        layer.seed = int(val)
        layer.regenerate()

    def _add_blend_mode_control(self, layout, layer):
        combo = QComboBox()
        modes = ["Normal", "Add", "Multiply", "Screen"]
        combo.addItems(modes)
        
        current = layer.blend_mode if hasattr(layer, 'blend_mode') else "Normal"
        index = combo.findText(current)
        if index >= 0:
            combo.setCurrentIndex(index)
            
        combo.currentTextChanged.connect(lambda text: setattr(layer, 'blend_mode', text))
        layout.addRow("Blend Mode", combo)

    def _clear_layout(self, layout):
        if not layout: return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
                item.layout().deleteLater()

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
        
    def _update_list(self, target, idx, val, layer):
        target[idx] = val
        
    def _update_whole_color(self, target_list, new_color, layer):
        # Update R, G, B in place
        target_list[0] = new_color[0]
        target_list[1] = new_color[1]
        target_list[2] = new_color[2]
