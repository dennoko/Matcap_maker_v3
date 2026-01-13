class LayerStack:
    def __init__(self):
        self._layers = []
        
    def add_layer(self, layer):
        self._layers.append(layer)
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
    
    def __iter__(self):
        return iter(self._layers)
