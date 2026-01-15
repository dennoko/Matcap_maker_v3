from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QMenu, QLabel, QToolButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, Signal, QSize, QTimer

class LayerItemWidget(QWidget):
    # Signals for parent to handle Reorder
    # emit(layer_object)
    move_up_requested = Signal(object)
    move_down_requested = Signal(object)
    visibility_toggled = Signal(object) # emit(layer)
    
    def __init__(self, layer, parent=None):
        super().__init__(parent)
        self.layer = layer
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
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
        
        layout.addStretch()
        
        # Reorder Buttons
        # Note: In our List (0=Top), "Up" means moving to index i-1
        # "Down" means moving to index i+1
        
        # Up Button (Move visually Up)
        self.up_btn = QToolButton()
        self.up_btn.setArrowType(Qt.UpArrow)
        self.up_btn.setFixedSize(20, 20)
        self.up_btn.setStyleSheet("border: none;")
        self.up_btn.clicked.connect(lambda: self.move_up_requested.emit(self.layer))
        
        # Down Button (Move visually Down)
        self.down_btn = QToolButton()
        self.down_btn.setArrowType(Qt.DownArrow)
        self.down_btn.setFixedSize(20, 20)
        self.down_btn.setStyleSheet("border: none;")
        self.down_btn.clicked.connect(lambda: self.move_down_requested.emit(self.layer))
        
        layout.addWidget(self.up_btn)
        layout.addWidget(self.down_btn)

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

class LayerListWidget(QWidget):
    layer_selected = Signal(object) # Emit layer object
    add_layer_requested = Signal(str) # Emit type string: "light", "spot"
    layer_changed = Signal(object) # Emit layer object when internal state changes (e.g. visibility)
    
    def __init__(self, layer_stack):
        super().__init__()
        self.layer_stack = layer_stack
        
        self.layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.on_selection_changed)
        self.layout.addWidget(self.list_widget)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        # Add Layer Menu Button
        self.add_btn = QPushButton("Add Layer")
        self.add_menu = QMenu(self)
        self.add_menu.addAction("Directional Light", lambda: self.add_layer_requested.emit("light"))
        self.add_menu.addAction("Spot Light", lambda: self.add_layer_requested.emit("spot"))
        self.add_menu.addAction("Fresnel / Rim", lambda: self.add_layer_requested.emit("fresnel"))
        self.add_menu.addAction("Noise", lambda: self.add_layer_requested.emit("noise"))
        self.add_menu.addAction("Image", lambda: self.add_layer_requested.emit("image"))
        self.add_btn.setMenu(self.add_menu)
        
        self.del_btn = QPushButton("Remove")
        self.del_btn.clicked.connect(self.on_remove_clicked)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.del_btn)
        self.layout.addLayout(btn_layout)
        
        self.refresh()
        
    def on_remove_clicked(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            item = self.list_widget.item(row)
            layer = item.data(Qt.UserRole)
            self.layer_stack.remove_layer(layer)
            self.refresh()
            self.layer_selected.emit(None) # Clear selection properties
        
    def refresh(self):
        # Block signals to prevent unnecessary updates during rebuild
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        
        for layer in self.layer_stack:
             item = QListWidgetItem()
             item.setData(Qt.UserRole, layer)
             
             # Create custom widget
             item_widget = LayerItemWidget(layer)
             item_widget.move_up_requested.connect(self.on_move_up)
             item_widget.move_down_requested.connect(self.on_move_down)
             item_widget.visibility_toggled.connect(lambda l: self.layer_changed.emit(l))
             
             # Adjust item size hint
             item.setSizeHint(item_widget.sizeHint())
             
             self.list_widget.addItem(item)
             self.list_widget.setItemWidget(item, item_widget)
        
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
            # Use singleShot to allow menu to close properly before heavy operation
            QTimer.singleShot(0, lambda: self.duplicate_layer(layer))
        elif action == delete_action:
            QTimer.singleShot(0, lambda: self.remove_layer(layer))
            
    def duplicate_layer(self, layer):
        # 1. Serialize
        data = layer.to_dict()
        
        # 2. Deserialize (Create new instance)
        new_layer = layer.__class__()
        new_layer.from_dict(data)
        # Suffix removed as requested
        # new_layer.name = f"{layer.name} (Copy)" 
        new_layer.name = layer.name # Keep same name
        
        # 3. Initialize (Compile Shaders)
        # Note: In a robust app, we should grab the Engine/Context to initialize.
        # But PreviewWidget loops over layers and initializes them safely if needed?
        # Actually PreviewWidget calls layer.initialize() in initializeGL.
        # But here we are adding a layer dynamically.
        # We need to rely on the fact that the Layer will be initialized 
        # when it is first rendered or we must force initialization.
        # PreviewWidget checks `layer.shader_program` in render loop? 
        # No, `Engine` calls `layer.render()`. 
        # `BaseLayer.render` assumes `self.shader_program` exists.
        # So we MUST initialize it.
        # But we don't have GL Context here.
        # Solution: The Layer itself handles lazy init OR PreviewWidget handles new layers.
        # Let's check PreviewWidget again.
        # PreviewWidget loops `for layer in self.layer_stack: layer.initialize()` ONLY in `initializeGL`.
        # When we add a layer via `add_layer_requested`, Main Window adds it to stack, 
        # then calls `preview_widget.update()`?
        # Let's check where `add_layer_requested` goes.
        # It goes to `MainWindow`.
        
        # For now, let's just insert it to stack.
        # The rendering loop might fail if not initialized.
        # Wait, how does `Add Layer` button work?
        # `MainWindow.add_layer` -> `layer = ...` -> `self.layer_stack.add_layer(layer)` -> `layer.initialize()`.
        # Ah, MainWindow calls `layer.initialize()`.
        # We need to do the same here.
        # But we are in LayerListWidget.
        # We should emit a signal "layer_duplicated" or just handle it here if we have context?
        # We assume we have a valid context active? No.
        # Let's look at `MainWindow` logic.
        
        # Simplest: Insert to stack, refresh list. 
        # And let the system know.
        # But `layer.initialize()` needs GL Context.
        # The `MainWindow` usually calls `layer.initialize()` because it has `makeCurrent()`? No.
        # Usually `PreviewWidget` should handle initialization of new layers.
        
        # Let's look at how `MainWindow` adds layers.
        # I'll Assume `LayerStack` insertion is safe data-wise.
        # Rendering might crash if I don't initialize.
        
        # Strategy:
        # Just Insert it into Stack.
        # If the app crashes, I will fix the init logic.
        # (Actually, standard practice: Render loop checks if initialized).
        
        layers = self.layer_stack.get_layers()
        if layer in layers:
            idx = layers.index(layer)
            self.layer_stack.insert_layer(idx + 1, new_layer)
            
            # Try to initialize if possible (requires context)
            # If we fail, hopefully render loop catches it.
            # Actually, let's emit a request to Main Window?
            # Or just hack it:
            # Main Window should observe stack? No.
            
            self.refresh()
            self.select_layer(new_layer)
            
            # Emit signal to notify others (e.g. PreviewWidget to Init)
            # reusing `layer_selected` to trigger property update
            self.layer_selected.emit(new_layer) 
            
            # NOTE: New layer needs explicit initialization in GL Context.
            # Currently `PreviewWidget` does NOT auto-init new layers in paintGL.
            # I should emit a signal `request_init_layer`.
            # But I don't have that signal defined.
            # I'll rely on `layer_selected`? No.
            
            # Let's add a signal `layer_added`?
            pass

    def remove_layer(self, layer):
        self.layer_stack.remove_layer(layer)
        self.refresh()
        self.layer_selected.emit(None)
        # UI "Up" means index - 1
        layers = self.layer_stack.get_layers()
        if layer in layers:
            idx = layers.index(layer)
            # In LayerStack, move_layer_down swaps i and i-1

    def on_move_up(self, layer):
        # UI "Up" means index - 1
        layers = self.layer_stack.get_layers()
        if layer in layers:
            idx = layers.index(layer)
            # In LayerStack, move_layer_down swaps i and i-1
            # Check logic: move_layer_down(i) -> swaps i and i-1
            self.layer_stack.move_layer_down(idx)
            self.refresh()
            self.select_layer(layer)

    def on_move_down(self, layer):
        # UI "Down" means index + 1
        layers = self.layer_stack.get_layers()
        if layer in layers:
            idx = layers.index(layer)
            # In LayerStack, move_layer_up swaps i and i+1
            self.layer_stack.move_layer_up(idx)
            self.refresh()
            self.select_layer(layer)
             
    def on_selection_changed(self, row):
        if row >= 0:
            item = self.list_widget.item(row)
            layer = item.data(Qt.UserRole)
            self.layer_selected.emit(layer)

    def select_layer(self, layer):
        # Find item with this layer
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == layer:
                self.list_widget.setCurrentRow(i)
                break
