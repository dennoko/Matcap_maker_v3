from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QMenu, QLabel, QToolButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, Signal, QSize, QTimer

class LayerItemWidget(QWidget):
    # Signals for parent to handle Reorder
    # emit(layer_object)
    move_up_requested = Signal(object)
    move_down_requested = Signal(object)
    visibility_toggled = Signal(object) # emit(layer)
    layer_changed = Signal(object) # emit(layer)
    selection_needed = Signal(object) # emit(layer)

    def __init__(self, layer, parent=None):
        super().__init__(parent)
        self.layer = layer
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 8, 5, 8) # Increased vertical padding
        layout.setAlignment(Qt.AlignVCenter)
        
        self.setMinimumHeight(36) # Ensure minimum height for touch/click friendliness
        
        # Visibility Toggle
        self.vis_btn = QPushButton()
        self.vis_btn.setFixedSize(16, 16)
        self.vis_btn.clicked.connect(self.toggle_visibility)
        layout.addWidget(self.vis_btn)
        
        # Update style based on state
        self.update_vis_style()
        
        # Name Label
        self.label = QLabel(layer.name)
        layout.addWidget(self.label)
        
        # Color Icon (if layer has color)
        if hasattr(self.layer, 'color'):
            self.color_btn = QPushButton()
            self.color_btn.setFixedSize(18, 18)
            self.color_btn.clicked.connect(self.on_color_clicked)
            layout.addWidget(self.color_btn)
            self.update_color_style()
        
        layout.addStretch()
        
        layout.addStretch()
        
        # Handle Icon for Dragging (Visual only, D&D starts anywhere but handle implies it)
        self.handle_label = QLabel("≡")
        self.handle_label.setStyleSheet("font-size: 16px; color: #888; font-weight: bold;")
        self.handle_label.setFixedWidth(20)
        self.handle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.handle_label)

    def toggle_visibility(self):
        self.layer.enabled = not self.layer.enabled
        self.update_vis_style()
        self.visibility_toggled.emit(self.layer)
        
    def update_vis_style(self):
        # Green if enabled, Black if disabled. Circle shape.
        color = "#00FF7F" if self.layer.enabled else "#000000" # SpringGreen or Black
        self.vis_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border-radius: 8px;
                border: 1px solid #444;
            }}
            QPushButton:hover {{
                border: 1px solid #FFF;
            }}
        """)

    def update_color_style(self):
        if not hasattr(self.layer, 'color'):
            return
            
        # layer.color is typically [r, g, b] float 0-1
        c = self.layer.color
        r = int(c[0] * 255)
        g = int(c[1] * 255)
        b = int(c[2] * 255)
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        
        self.color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {hex_color};
                border-radius: 4px; /* Rounded Square */
                border: 1px solid #666;
            }}
            QPushButton:hover {{
                border: 1px solid #FFF;
            }}
        """)

    def on_color_clicked(self):
        # 1. Request Selection
        # We can't emit selection directly to list widget via signal here easily without custom signal
        # But we can assume the logical flow: User clicked this row's internal widget
        # The parent ListWidget doesn't automatically know, so we might need a signal
        
        # Actually, let's emit a signal that LayerListWidget can catch
        # We need a new signal in LayerItemWidget "selection_requested"?
        # Or just reuse one?
        # Let's add a "color_clicked" signal?
        # Wait, the instruction said "click to show property and color window".
        # So we should probably select the item first.
        self.open_color_picker()

    def open_color_picker(self):
        from PySide6.QtWidgets import QColorDialog
        from PySide6.QtGui import QColor
        
        c = self.layer.color
        initial = QColor.fromRgbF(c[0], c[1], c[2])
        
        # We need to emit a signal so the main window knows to select this layer
        # But we are inside the ItemWidget.
        # We can emit a signal that LayerListWidget connects to.
        # Let's add `color_change_requested`?
        # Or simply handle it here and just emit `layer_changed` after update.
        # But we also want to SELECT the layer.
        
        self.selection_needed.emit(self.layer)
        
        color = QColorDialog.getColor(initial, self, "Select Layer Color")
        if color.isValid():
            new_c = [color.redF(), color.greenF(), color.blueF()]
            self.layer.color = new_c
            self.update_color_style()
            self.layer_changed.emit(self.layer)

class ReorderableListWidget(QListWidget):
    reorder_completed = Signal() # Emitted after drop

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        
    def dropEvent(self, event):
        super().dropEvent(event)
        self.reorder_completed.emit()


class LayerListWidget(QWidget):
    layer_selected = Signal(object) # Emit layer object
    add_layer_requested = Signal(str) # Emit type string
    layer_changed = Signal(object) # Emit layer object when internal state changes
    stack_changed = Signal() # Emit when structure changes
    
    def __init__(self, layer_stack):
        super().__init__()
        self.layer_stack = layer_stack
        
        self.layout = QVBoxLayout(self)
        
        # Use our custom list widget
        self.list_widget = ReorderableListWidget()
        self.list_widget.currentRowChanged.connect(self.on_selection_changed)
        self.list_widget.reorder_completed.connect(self.on_reorder_completed)
        self.layout.addWidget(self.list_widget)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        # Add Layer Menu Button
        self.add_btn = QPushButton("Add Layer")
        self.add_menu = QMenu(self)
        self.add_menu.addAction("Spot Light", lambda: self.add_layer_requested.emit("spot"))
        self.add_menu.addAction("Fresnel / Rim", lambda: self.add_layer_requested.emit("fresnel"))
        self.add_menu.addAction("Noise", lambda: self.add_layer_requested.emit("noise"))
        self.add_menu.addAction("Image", lambda: self.add_layer_requested.emit("image"))
        self.add_menu.addSeparator()
        self.add_menu.addAction("Color Adjustment", lambda: self.add_layer_requested.emit("adjustment"))
        self.add_btn.setMenu(self.add_menu)
        
        self.del_btn = QPushButton("Remove")
        self.del_btn.clicked.connect(self.on_remove_clicked)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.del_btn)
        self.layout.addLayout(btn_layout)
        
        self.refresh()
        
    def on_reorder_completed(self):
        # Reconstruct LayerStack based on UI order
        new_order = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            layer = item.data(Qt.UserRole)
            new_order.append(layer)
            
        # Update Stack (Directly Access private _layers or use clear/add? 
        # LayerStack logic needs to be respected. 
        # Modifying internal list is safest if we trust our UI sync.
        
        # Assuming we can modify LayerStack._layers directly since we passed it in.
        # But `LayerStack` api is clean. Let's use `clear` and `add`?
        # `add` appends.
        
        self.layer_stack.clear()
        for layer in new_order:
            self.layer_stack.add_layer(layer)
            
        self.stack_changed.emit()
        
        # NOTE: After drop, item widgets might be lost/reset by Qt?
        # QListWidget usually keeps item data but wipes setItemWidget?
        # Let's check. If widgets are gone, we must refresh visuals.
        # Usually D&D in QListWidget with setItemWidget is tricky.
        # It moves the *Item* but `setItemWidget` association might act weird.
        # It's safer to FULL REFRESH to ensure widgets are correctly bound.
        
        # However, calling refresh() destroys current drag state? Drop is done.
        # Let's try refresh() to be safe.
        self.refresh()
        
        # Restore selection?
        # Dropped item is usually selected?
        # Let's just emit stack change.

    def on_remove_clicked(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            item = self.list_widget.item(row)
            layer = item.data(Qt.UserRole)
            self.layer_stack.remove_layer(layer)
            self.refresh()
            self.layer_selected.emit(None) # Clear selection properties
            self.stack_changed.emit()
        
    def refresh(self):
        # Block signals to prevent unnecessary updates during rebuild
        self.list_widget.blockSignals(True)
        
        # Store current selection to restore it
        current_layer = None
        current_row = self.list_widget.currentRow()
        if current_row >= 0:
            current_layer = self.list_widget.item(current_row).data(Qt.UserRole)

        self.list_widget.clear()
        
        for layer in self.layer_stack:
             item = QListWidgetItem()
             item.setData(Qt.UserRole, layer)
             
             # Create custom widget
             item_widget = LayerItemWidget(layer)
             # item_widget.move_up... Removed
             # item_widget.move_down... Removed
             item_widget.visibility_toggled.connect(lambda l: self.layer_changed.emit(l))
             item_widget.layer_changed.connect(lambda l: self.layer_changed.emit(l)) 
             item_widget.selection_needed.connect(self.select_layer)
             
             # Adjust item size hint
             item.setSizeHint(item_widget.sizeHint())
             
             self.list_widget.addItem(item)
             self.list_widget.setItemWidget(item, item_widget)
        
        # Restore selection
        if current_layer:
            self.select_layer(current_layer)

        self.list_widget.blockSignals(False)
        self.list_widget.update() # Force redraw
             
        # Set Context Menu Policy
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return
            
        layer = item.data(Qt.UserRole)
        menu = QMenu(self)
        
        duplicate_action = menu.addAction("Duplicate Layer")
        delete_action = menu.addAction("Delete Layer")
        
        action = menu.exec(self.list_widget.mapToGlobal(pos))
        
        if action == duplicate_action:
            QTimer.singleShot(0, lambda: self.duplicate_layer(layer))
        elif action == delete_action:
            QTimer.singleShot(0, lambda: self.remove_layer(layer))
            
    def duplicate_layer(self, layer):
        # 1. Serialize
        data = layer.to_dict()
        
        # 2. Deserialize
        new_layer = layer.__class__()
        new_layer.from_dict(data)
        new_layer.name = layer.name 
        
        # 3. Initialize & Insert
        # Insert after active layer? Or after the duplicated one?
        # Usually duplicate appears after the original.
        
        layers = self.layer_stack.get_layers()
        if layer in layers:
            idx = layers.index(layer)
            self.layer_stack.insert_layer(idx + 1, new_layer)
            
            # Note: MainWindow handles initialization usually, but here internal.
            # We assume subsequent render (which checks shader) or MainWin logic handles it?
            # We still don't have context here.
            # But the user logic is "Add Layer" -> MainWin -> Init.
            # "Duplicate" -> internal list -> NO MAIN WIN INIT.
            # This is a risk.
            # We should signal MainWindow?
            # Let's fix this properly: MainWindow should listen to "layer_added" signal?
            # Or assume the render loop lazily inits.
            
            # For now, stick to previous logic (insert and emit stack change)
            
            self.refresh()
            self.select_layer(new_layer)
            self.layer_selected.emit(new_layer) 
            self.stack_changed.emit()

    def remove_layer(self, layer):
        self.layer_stack.remove_layer(layer)
        self.refresh()
        self.layer_selected.emit(None)
        self.stack_changed.emit()

    def on_selection_changed(self, row):
        if row >= 0:
            item = self.list_widget.item(row)
            layer = item.data(Qt.UserRole)
            self.layer_selected.emit(layer)

    def select_layer(self, layer):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == layer:
                self.list_widget.setCurrentRow(i)
                break

    def update_active_layer_visuals(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            item = self.list_widget.item(row)
            widget = self.list_widget.itemWidget(item)
            if widget:
                widget.update_color_style()
                widget.label.setText(widget.layer.name)

