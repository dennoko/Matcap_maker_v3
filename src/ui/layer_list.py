from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QMenu, QLabel, QToolButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, Signal, QSize

class LayerItemWidget(QWidget):
    # Signals for parent to handle Reorder
    # emit(layer_object)
    move_up_requested = Signal(object)
    move_down_requested = Signal(object)
    
    def __init__(self, layer, parent=None):
        super().__init__(parent)
        self.layer = layer
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
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

class LayerListWidget(QWidget):
    layer_selected = Signal(object) # Emit layer object
    add_layer_requested = Signal(str) # Emit type string: "light", "spot"
    
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
        self.list_widget.clear()
        for layer in self.layer_stack:
             item = QListWidgetItem()
             item.setData(Qt.UserRole, layer)
             
             # Create custom widget
             item_widget = LayerItemWidget(layer)
             item_widget.move_up_requested.connect(self.on_move_up)
             item_widget.move_down_requested.connect(self.on_move_down)
             
             # Adjust item size hint
             item.setSizeHint(item_widget.sizeHint())
             
             self.list_widget.addItem(item)
             self.list_widget.setItemWidget(item, item_widget)

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
