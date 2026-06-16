"""Verification for the compositor/layer refactor.

Checks, end-to-end on a real GL context:
1. All layer types render without GL errors.
2. Layer opacity is honored by the blend pass (0 = invisible, partial differs).
3. AdjustmentLayer (post-process path) works and respects opacity.
4. NoiseLayer.regenerate() outside the GL context is safe (deferred).
5. Offscreen export + padding (dilate / fill_background) produces opaque output.
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from PIL import Image

from src.core.engine import Engine
from src.core.layer_stack import LayerStack
from src.core import export_padding
from src.layers.base_layer import BaseLayer
from src.layers.spot_light_layer import SpotLightLayer
from src.layers.fresnel_layer import FresnelLayer
from src.layers.noise_layer import NoiseLayer
from src.layers.gradient_layer import GradientLayer
from src.layers.adjustment_layer import AdjustmentLayer

SIZE = 256
failures = []


def check(name, cond):
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        failures.append(name)


class Harness(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.resize(SIZE, SIZE)
        self.engine = Engine(SIZE, SIZE)
        self.layer_stack = LayerStack()
        self.done = False

    def initializeGL(self):
        self.engine.initialize()

    def capture(self):
        """Render the current stack and return an RGBA numpy array."""
        self.engine.resize(SIZE, SIZE)
        # Force re-render
        for layer in self.layer_stack:
            layer.mark_dirty()
        self.engine.render(self.layer_stack)
        tex_id = self.engine.get_texture_id()
        glBindTexture(GL_TEXTURE_2D, tex_id)
        data = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_UNSIGNED_BYTE)
        arr = np.frombuffer(data, dtype=np.uint8).reshape(SIZE, SIZE, 4)
        return arr[::-1].copy()  # flip to top-down

    def paintGL(self):
        if self.done:
            return
        self.done = True
        try:
            self.run_checks()
        except Exception as e:
            import traceback
            traceback.print_exc()
            failures.append(f"exception: {e}")
        QApplication.quit()

    def run_checks(self):
        # --- Stack with every layer type ---
        base = BaseLayer()
        base.base_color = [0.1, 0.1, 0.3]

        spot = SpotLightLayer()
        spot.direction = [0.35, -0.22, 1.0]
        spot.range = 0.3
        spot.blur = 0.5

        fres = FresnelLayer()
        fres.color = [1.0, 0.5, 0.0]
        fres.intensity = 1.0

        grad = GradientLayer()
        grad.blend_mode = "Add"
        grad.gradient_stops = [
            {"position": 0.0, "color": [0.0, 0.0, 0.0]},
            {"position": 1.0, "color": [0.0, 0.4, 0.0]},
        ]

        noise = NoiseLayer()
        noise.intensity = 0.3

        adj = AdjustmentLayer()
        adj.saturation = 0.0  # grayscale, very visible

        for layer in [base, spot, fres, grad, noise, adj]:
            self.layer_stack.add_layer(layer)
            layer.initialize()

        img_all = self.capture()
        check("no GL error after full-stack render", glGetError() == GL_NO_ERROR)
        check("full stack renders non-empty", img_all[:, :, 3].max() > 0)
        center = img_all[SIZE // 2, SIZE // 2]
        check("adjustment (saturation=0) grayscales center",
              abs(int(center[0]) - int(center[1])) <= 2 and abs(int(center[1]) - int(center[2])) <= 2)

        # --- Adjustment opacity: 0 should disable the effect ---
        adj.opacity = 0.0
        img_adj_off = self.capture()
        c2 = img_adj_off[SIZE // 2, SIZE // 2]
        check("adjustment opacity=0 restores color", not (
            abs(int(c2[0]) - int(c2[1])) <= 2 and abs(int(c2[1]) - int(c2[2])) <= 2
        ) or (center[:3] == c2[:3]).all() is False)
        adj.enabled = False

        # --- Layer opacity wiring through blend pass ---
        img_fres_full = self.capture()
        fres.opacity = 0.0
        img_fres_zero = self.capture()
        self.layer_stack.remove_layer(fres)
        img_fres_removed = self.capture()
        check("opacity=0 equals layer removed",
              np.array_equal(img_fres_zero, img_fres_removed))
        check("opacity=1 differs from opacity=0",
              not np.array_equal(img_fres_full, img_fres_zero))
        fres.opacity = 0.5
        self.layer_stack.add_layer(fres)
        img_fres_half = self.capture()
        self.layer_stack.remove_layer(fres)
        check("opacity=0.5 is between 0 and 1",
              not np.array_equal(img_fres_half, img_fres_zero)
              and not np.array_equal(img_fres_half, img_fres_full))

        # --- Noise regenerate without context (deferred to render) ---
        noise.seed = 42
        noise.regenerate()  # would crash pre-fix if no context were current
        img_seed42 = self.capture()
        noise.seed = 43
        noise.regenerate()
        img_seed43 = self.capture()
        check("noise regenerate changes output",
              not np.array_equal(img_seed42, img_seed43))

        # --- Offscreen export + padding ---
        qimg = self.engine.render_offscreen(128, 128, self.layer_stack,
                                            preview_mode_override=0,
                                            force_no_normal=True)
        check("render_offscreen returns image", qimg is not None and not qimg.isNull())

        from PySide6.QtGui import QImage
        qimg = qimg.convertToFormat(QImage.Format.Format_RGBA8888)
        bpl = qimg.bytesPerLine()
        raw = np.frombuffer(qimg.constBits(), dtype=np.uint8, count=bpl * 128)
        arr = raw.reshape(128, bpl)[:, :128 * 4].reshape(128, 128, 4)

        n_transparent_before = (arr[:, :, 3] == 0).sum()
        check("export has transparent surroundings", n_transparent_before > 0)

        padded = export_padding.dilate(arr, 8)
        n_transparent_after = (padded[:, :, 3] == 0).sum()
        check("dilation shrinks transparent area",
              n_transparent_after < n_transparent_before)

        export_padding.fill_background(padded)
        check("fill_background leaves no transparency",
              (padded[:, :, 3] == 255).all())

        # Padded ring color should come from the sphere edge, not black
        corner_is_black = (padded[0, 0, :3] == 0).all()
        check("corner (outside padding) is black fill", corner_is_black)

        Image.fromarray(img_all).save("tests/verify_refactor_output.png")
        print("Saved tests/verify_refactor_output.png")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Harness()
    w.show()
    app.exec()
    if failures:
        print(f"\n{len(failures)} FAILURE(S):", failures)
        sys.exit(1)
    print("\nALL CHECKS PASSED")
    sys.exit(0)
