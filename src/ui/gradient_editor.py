from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QDoubleSpinBox)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import (QPainter, QLinearGradient, QColor, QPen,
                            QBrush, QPainterPath, QCursor)
from src.ui.params import ColorPicker
from src.core.i18n import tr


class GradientCanvas(QWidget):
    """Gradient bar with draggable color pins."""

    stopSelected   = Signal(int)        # idx
    stopMoved      = Signal(int, float) # idx, new_position
    stopAdded      = Signal(float)      # position
    stopDoubleClicked = Signal(int)     # idx

    BAR_H   = 28
    PIN_H   = 16
    PIN_W   = 12
    PAD     = 8   # horizontal padding so edge-pins are fully visible
    HIT_R   = 10  # hit-test radius for pins (px)

    def __init__(self, stops, parent=None):
        super().__init__(parent)
        self._stops = stops  # shared reference
        self._selected = 0
        self._dragging = False
        self._drag_idx = None
        self.setFixedHeight(self.BAR_H + self.PIN_H + 4)
        self.setMinimumWidth(100)

    # ── public ────────────────────────────────────────────────────────────────

    def set_stops(self, stops):
        self._stops = stops
        self._selected = min(self._selected, len(stops) - 1)
        self.update()

    def set_selected(self, idx):
        self._selected = idx
        self.update()

    # ── geometry helpers ───────────────────────────────────────────────────────

    def _bar_rect(self):
        return QRect(self.PAD, 0, self.width() - 2 * self.PAD, self.BAR_H)

    def _pos_to_x(self, pos):
        r = self._bar_rect()
        return r.left() + pos * r.width()

    def _x_to_pos(self, x):
        r = self._bar_rect()
        return max(0.0, min(1.0, (x - r.left()) / r.width()))

    def _find_pin_at(self, x, y):
        if y < self.BAR_H - 4:
            return None
        best_idx, best_dist = None, self.HIT_R + 1
        for i, stop in enumerate(self._stops):
            dist = abs(x - self._pos_to_x(stop["position"]))
            if dist < best_dist:
                best_dist, best_idx = dist, i
        return best_idx

    # ── paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        bar = self._bar_rect()

        # Gradient bar
        sorted_stops = sorted(self._stops, key=lambda s: s["position"])
        grad = QLinearGradient(bar.left(), 0, bar.right(), 0)
        for s in sorted_stops:
            c = s["color"]
            grad.setColorAt(s["position"], QColor.fromRgbF(c[0], c[1], c[2]))
        p.fillRect(bar, grad)
        p.setPen(QPen(QColor("#555"), 1))
        p.drawRect(bar)

        # Pins (triangles pointing up into the bar)
        for i, stop in enumerate(self._stops):
            cx = self._pos_to_x(stop["position"])
            tip_y  = self.BAR_H - 1
            base_y = self.BAR_H + self.PIN_H
            hw = self.PIN_W // 2

            path = QPainterPath()
            path.moveTo(cx, tip_y)
            path.lineTo(cx - hw, base_y)
            path.lineTo(cx + hw, base_y)
            path.closeSubpath()

            c = stop["color"]
            p.fillPath(path, QBrush(QColor.fromRgbF(c[0], c[1], c[2])))

            if i == self._selected:
                p.setPen(QPen(QColor("#FFFFFF"), 2))
            else:
                p.setPen(QPen(QColor("#888"), 1))
            p.drawPath(path)

        p.end()

    # ── mouse ─────────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        x, y = event.position().x(), event.position().y()
        idx = self._find_pin_at(x, y)
        if idx is not None:
            self._selected = idx
            self._dragging = True
            self._drag_idx = idx
            self.stopSelected.emit(idx)
            self.update()
        else:
            # Click on bar → add new stop
            self.stopAdded.emit(self._x_to_pos(x))

    def mouseMoveEvent(self, event):
        x = event.position().x()
        if self._dragging and self._drag_idx is not None:
            new_pos = self._x_to_pos(x)
            self.stopMoved.emit(self._drag_idx, new_pos)
            self.update()
        else:
            # Cursor hint
            idx = self._find_pin_at(x, event.position().y())
            if idx is not None:
                self.setCursor(Qt.SizeHorCursor)
            else:
                self.setCursor(Qt.CrossCursor)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._drag_idx = None

    def mouseDoubleClickEvent(self, event):
        x, y = event.position().x(), event.position().y()
        idx = self._find_pin_at(x, y)
        if idx is not None:
            self.stopDoubleClicked.emit(idx)


class GradientEditorWidget(QWidget):
    """
    Full gradient editor: visual gradient bar with draggable pins + controls
    for the currently selected pin (color, position, delete).
    """
    stopsChanged = Signal(list)

    MAX_STOPS = 8

    def __init__(self, stops, parent=None):
        super().__init__(parent)
        self._stops = [{"position": s["position"], "color": list(s["color"])}
                       for s in stops]
        self._selected_idx = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)

        # Hint label
        hint = QLabel(tr("prop.gradient.hint"))
        hint.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(hint)

        # Canvas
        self._canvas = GradientCanvas(self._stops)
        self._canvas.stopSelected.connect(self._on_stop_selected)
        self._canvas.stopMoved.connect(self._on_stop_moved)
        self._canvas.stopAdded.connect(self._on_stop_added)
        self._canvas.stopDoubleClicked.connect(self._open_color_picker)
        layout.addWidget(self._canvas)

        # Controls for selected stop
        ctrl = QWidget()
        ctrl_layout = QHBoxLayout(ctrl)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        ctrl_layout.setSpacing(6)

        self._color_picker = ColorPicker(self._stops[0]["color"])
        self._color_picker.colorChanged.connect(self._on_color_changed)
        ctrl_layout.addWidget(self._color_picker)

        ctrl_layout.addWidget(QLabel(tr("prop.gradient.position")))

        self._pos_spin = QDoubleSpinBox()
        self._pos_spin.setRange(0.0, 1.0)
        self._pos_spin.setSingleStep(0.01)
        self._pos_spin.setDecimals(3)
        self._pos_spin.setValue(self._stops[0]["position"])
        self._pos_spin.valueChanged.connect(self._on_pos_spin_changed)
        ctrl_layout.addWidget(self._pos_spin, stretch=1)

        self._del_btn = QPushButton(tr("prop.gradient.delete_btn"))
        self._del_btn.setToolTip(tr("prop.gradient.remove_stop"))
        self._del_btn.clicked.connect(self._on_delete)
        ctrl_layout.addWidget(self._del_btn)

        layout.addWidget(ctrl)

        self._update_controls()

    # ── internal helpers ──────────────────────────────────────────────────────

    def _update_controls(self):
        if not self._stops:
            return
        stop = self._stops[self._selected_idx]
        self._color_picker.current_color = list(stop["color"])
        self._color_picker.update_style()
        self._pos_spin.blockSignals(True)
        self._pos_spin.setValue(stop["position"])
        self._pos_spin.blockSignals(False)
        self._del_btn.setEnabled(len(self._stops) > 2)

    def _sample_color_at(self, t):
        """Interpolate gradient color at position t (for new stop initial color)."""
        ss = sorted(self._stops, key=lambda s: s["position"])
        if t <= ss[0]["position"]:
            return list(ss[0]["color"])
        if t >= ss[-1]["position"]:
            return list(ss[-1]["color"])
        for i in range(len(ss) - 1):
            p0, p1 = ss[i]["position"], ss[i + 1]["position"]
            if p0 <= t <= p1:
                lt = (t - p0) / (p1 - p0) if (p1 - p0) > 0.0001 else 0.0
                c0, c1 = ss[i]["color"], ss[i + 1]["color"]
                return [c0[j] + (c1[j] - c0[j]) * lt for j in range(3)]
        return [0.5, 0.5, 0.5]

    # ── slots ─────────────────────────────────────────────────────────────────

    def _on_stop_selected(self, idx):
        self._selected_idx = idx
        self._update_controls()

    def _on_stop_moved(self, idx, pos):
        self._stops[idx]["position"] = pos
        if idx == self._selected_idx:
            self._pos_spin.blockSignals(True)
            self._pos_spin.setValue(pos)
            self._pos_spin.blockSignals(False)
        self._canvas.update()
        self.stopsChanged.emit(self._stops)

    def _on_stop_added(self, pos):
        if len(self._stops) >= self.MAX_STOPS:
            return
        new_stop = {"position": pos, "color": self._sample_color_at(pos)}
        self._stops.append(new_stop)
        self._selected_idx = len(self._stops) - 1
        self._canvas.set_stops(self._stops)
        self._canvas.set_selected(self._selected_idx)
        self._update_controls()
        self.stopsChanged.emit(self._stops)

    def _on_color_changed(self, color):
        self._stops[self._selected_idx]["color"] = list(color)
        self._canvas.update()
        self.stopsChanged.emit(self._stops)

    def _on_pos_spin_changed(self, val):
        self._stops[self._selected_idx]["position"] = val
        self._canvas.update()
        self.stopsChanged.emit(self._stops)

    def _on_delete(self):
        if len(self._stops) <= 2:
            return
        self._stops.pop(self._selected_idx)
        self._selected_idx = max(0, self._selected_idx - 1)
        self._canvas.set_stops(self._stops)
        self._canvas.set_selected(self._selected_idx)
        self._update_controls()
        self.stopsChanged.emit(self._stops)

    def _open_color_picker(self, idx):
        """Open color dialog directly (from double-click on pin)."""
        self._selected_idx = idx
        self._update_controls()
        self._color_picker.open_dialog()
