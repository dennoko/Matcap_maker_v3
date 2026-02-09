class LayerStack:
    def __init__(self):
        self._layers = []
        self._on_structure_changed = None  # コールバック: 構造変更時にキャッシュ無効化

    def set_structure_changed_callback(self, callback):
        """構造変更時に呼び出されるコールバックを設定"""
        self._on_structure_changed = callback

    def _notify_structure_changed(self):
        """構造変更を通知"""
        if self._on_structure_changed:
            self._on_structure_changed()
        
    def add_layer(self, layer):
        self._layers.append(layer)
        self._notify_structure_changed()
        return layer
        
    def insert_layer(self, index, layer):
        self._layers.insert(index, layer)
        self._notify_structure_changed()
        return layer
        
    def remove_layer(self, layer):
        if layer in self._layers:
            self._layers.remove(layer)
            self._notify_structure_changed()
        return layer
            
    def move_layer_up(self, index):
        if 0 <= index < len(self._layers) - 1:
            self._layers[index], self._layers[index+1] = self._layers[index+1], self._layers[index]
            self._notify_structure_changed()
            
    def move_layer_down(self, index):
        if 0 < index < len(self._layers):
            self._layers[index], self._layers[index-1] = self._layers[index-1], self._layers[index]
            self._notify_structure_changed()

    def get_layers(self):
        return self._layers
    
    def clear(self):
        self._layers.clear()
        self._notify_structure_changed()

    def __iter__(self):
        return iter(self._layers)

    def __getitem__(self, index):
        return self._layers[index]

    def __len__(self):
        return len(self._layers)

