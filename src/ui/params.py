from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSlider, QDoubleSpinBox, QPushButton, QColorDialog, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

class FloatSlider(QWidget):
    valueChanged = Signal(float)

    def __init__(self, value=0.0, min_slider=0.0, max_slider=1.0, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self) # Changed to Vertical
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2) # Tight spacing
        
        # SpinBox (Top)
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setRange(-999999.0, 999999.0)
        self.spinbox.setSingleStep(0.1) # Changed step to 0.1
        self.spinbox.setDecimals(3)
        self.spinbox.setValue(value)
        
        # Slider (Bottom)
        self.slider = QSlider(Qt.Horizontal)
        self.min_slider = min_slider
        self.max_slider = max_slider
        self.slider_steps = 1000
        self.slider.setRange(0, self.slider_steps)
        
        self.layout.addWidget(self.spinbox)
        self.layout.addWidget(self.slider)
        
        # Connect signals
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)
        
        # Initial sync
        self._update_slider_from_val(value)

    def _on_slider_changed(self, val):
        # Map slider int to float
        ratio = val / self.slider_steps
        float_val = self.min_slider + (self.max_slider - self.min_slider) * ratio
        
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(float_val)
        self.spinbox.blockSignals(False)
        
        self.valueChanged.emit(float_val)

    def _on_spinbox_changed(self, val):
        self._update_slider_from_val(val)
        self.valueChanged.emit(val)

    def _update_slider_from_val(self, val):
        # Map float to slider int (clamped visually, but value persists)
        ratio = (val - self.min_slider) / (self.max_slider - self.min_slider) if (self.max_slider - self.min_slider) != 0 else 0
        slider_val = int(ratio * self.slider_steps)
        slider_val = max(0, min(self.slider_steps, slider_val))
        
        self.slider.blockSignals(True)
        self.slider.setValue(slider_val)
        self.slider.blockSignals(False)
        
    def setValue(self, val):
        self.spinbox.setValue(val)


class ColorPicker(QWidget):
    colorChanged = Signal(list) # Emits [r, g, b] float 0-1

    def __init__(self, color=[1.0, 1.0, 1.0], parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.current_color = color
        
        # Preview Label (Acts as the button)
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(60, 25) # Slightly larger/wider
        self.preview_label.setCursor(Qt.PointingHandCursor)
        self.preview_label.mousePressEvent = self.open_dialog_event 
        
        self.layout.addWidget(self.preview_label)
        self.layout.addStretch() # align left
        
        self.update_style()

    def update_style(self):
        r = int(self.current_color[0] * 255)
        g = int(self.current_color[1] * 255)
        b = int(self.current_color[2] * 255)
        self.preview_label.setStyleSheet(f"background-color: rgb({r},{g},{b}); border: 1px solid #888; border-radius: 4px;")

    def open_dialog_event(self, event):
        self.open_dialog()

    def open_dialog(self):
        initial = QColor(
            int(self.current_color[0] * 255),
            int(self.current_color[1] * 255),
            int(self.current_color[2] * 255)
        )
        color = QColorDialog.getColor(initial, self, "Select Color")
        
        if color.isValid():
            self.current_color = [color.redF(), color.greenF(), color.blueF()]
            self.update_style()
            self.colorChanged.emit(self.current_color)
