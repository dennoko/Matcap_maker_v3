from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QMenu
from PySide6.QtCore import Qt, Signal

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
             item = QListWidgetItem(layer.name)
             item.setData(Qt.UserRole, layer)
             self.list_widget.addItem(item)
             
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
