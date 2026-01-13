from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QFormLayout, QDoubleSpinBox
from PySide6.QtCore import Qt
from src.layers.base_layer import BaseLayer
from src.layers.light_layer import LightLayer

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
            self._add_color_control(form, "Color R", layer.base_color, 0, lambda v: self._update_color(layer.base_color, 0, v, layer))
            self._add_color_control(form, "Color G", layer.base_color, 1, lambda v: self._update_color(layer.base_color, 1, v, layer))
            self._add_color_control(form, "Color B", layer.base_color, 2, lambda v: self._update_color(layer.base_color, 2, v, layer))
            
        elif isinstance(layer, LightLayer):
            self._add_float_control(form, "Intensity", layer.intensity, 0.0, 5.0, lambda v: self._set_attr(layer, 'intensity', v))
            self._add_float_control(form, "Dir X", layer.direction[0], -1.0, 1.0, lambda v: self._update_list(layer.direction, 0, v, layer))
            self._add_float_control(form, "Dir Y", layer.direction[1], -1.0, 1.0, lambda v: self._update_list(layer.direction, 1, v, layer))
            self._add_float_control(form, "Dir Z", layer.direction[2], -1.0, 1.0, lambda v: self._update_list(layer.direction, 2, v, layer))

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

    def _add_color_control(self, layout, label, target_list, index, callback):
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 255)
        slider.setValue(int(target_list[index] * 255))
        slider.valueChanged.connect(lambda v: callback(v / 255.0))
        layout.addRow(label, slider)
        
    def _add_float_control(self, layout, label, value, min_v, max_v, callback):
        sb = QDoubleSpinBox()
        sb.setRange(min_v, max_v)
        sb.setSingleStep(0.1)
        sb.setValue(value)
        sb.valueChanged.connect(callback)
        layout.addRow(label, sb)

    def _update_color(self, target, idx, val, layer):
        target[idx] = val
        # Trigger redraw? Signal needed or simple callback
        # Main Window will handle redraw trigger separately or we pass a callback?
        # For now, let's assume we rely on main loop or manual trigger.
        
    def _set_attr(self, obj, name, val):
        setattr(obj, name, val)
        
    def _update_list(self, target, idx, val, layer):
        target[idx] = val
