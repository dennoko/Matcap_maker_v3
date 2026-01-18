from src.core.layer_registry import LayerRegistry
from src.layers.base_layer import BaseLayer
from src.layers.spot_light_layer import SpotLightLayer
from src.layers.fresnel_layer import FresnelLayer
from src.layers.noise_layer import NoiseLayer
from src.layers.image_layer import ImageLayer
from src.layers.adjustment_layer import AdjustmentLayer

# Explicitly register layers here.
# In a more advanced setup, this could be done via decorators or auto-discovery,
# but explicit registration is safe and clear for now.

LayerRegistry.register(BaseLayer)
LayerRegistry.register(SpotLightLayer)
LayerRegistry.register(FresnelLayer)
LayerRegistry.register(NoiseLayer)
LayerRegistry.register(ImageLayer)
LayerRegistry.register(AdjustmentLayer)
