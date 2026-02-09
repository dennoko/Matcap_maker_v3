class LayerStack:
    def __init__(self):
        self._layers = []
        
    def add_layer(self, layer):
        self._layers.append(layer)
        return layer
        
    def insert_layer(self, index, layer):
        self._layers.insert(index, layer)
        return layer
        
    def remove_layer(self, layer):
        if layer in self._layers:
            self._layers.remove(layer)
        return layer
            
    def move_layer_up(self, index):
        if 0 <= index < len(self._layers) - 1:
            self._layers[index], self._layers[index+1] = self._layers[index+1], self._layers[index]
            
    def move_layer_down(self, index):
        if 0 < index < len(self._layers):
            self._layers[index], self._layers[index-1] = self._layers[index-1], self._layers[index]

    def get_layers(self):
        return self._layers
    
    def clear(self):
        self._layers.clear()

    def __iter__(self):
        return iter(self._layers)

    def __getitem__(self, index):
        return self._layers[index]

    def __len__(self):
        return len(self._layers)
