class LayerRegistry:
    """
    Central registry for available layer types.
    Implements a Singleton pattern to manage the registration and creation of layers.
    """
    _instance = None
    _layers = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LayerRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, layer_cls):
        """Register a layer class."""
        type_name = layer_cls.__name__
        cls._layers[type_name] = layer_cls
        # logging.info(f"Registered Layer: {type_name}")

    @classmethod
    def get_class(cls, type_name):
        """Get layer class by type name."""
        return cls._layers.get(type_name)

    @classmethod
    def create(cls, type_name):
        """Create an instance of a layer by type name."""
        layer_cls = cls.get_class(type_name)
        if layer_cls:
            return layer_cls()
        return None

    @classmethod
    def get_registered_names(cls):
        """Get list of registered layer names."""
        return list(cls._layers.keys())
