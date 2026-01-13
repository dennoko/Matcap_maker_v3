class LayerInterface:
    def __init__(self):
        self.enabled = True
        self.name = "Layer"
        
    def initialize(self):
        """Called once when GL context is ready"""
        pass
        
    def render(self):
        """Called every frame"""
        pass
        
    def set_parameter(self, name, value):
        """Update a parameter"""
        pass
