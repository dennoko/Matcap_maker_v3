"""Verification for the Blur/Sharpen layer, improved image blur and image Scale X/Y.

Checks, end-to-end on a real GL context:
1. BlurSharpenLayer (2-pass post-process) renders without GL errors and changes
   the output in both Blur and Sharpen modes.
2. ImageLayer renders, and its per-axis Scale X / Scale Y produce different
   results (anisotropic scaling works).
3. ImageLayer blur renders without GL errors and changes the output.
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
from src.layers.base_layer import BaseLayer
from src.layers.fresnel_layer import FresnelLayer
from src.layers.image_layer import ImageLayer
from src.layers.blur_sharpen_layer import BlurSharpenLayer

SIZE = 256
failures = []
TMP_IMG = os.path.join(os.path.dirname(__file__), "_tmp_checker.png")


def check(name, cond):
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        failures.append(name)


def make_checker(path):
    # High-frequency checker so blur/sharpen and scale are clearly visible.
    a = np.zeros((64, 64, 4), dtype=np.uint8)
    a[..., 3] = 255
    a[::2, ::2, :3] = 255
    a[1::2, 1::2, :3] = 255
    # Make X and Y distinguishable: tint columns vs rows.
    a[:, :32, 0] = 255
    Image.fromarray(a).save(path)


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
        self.engine.resize(SIZE, SIZE)
        for layer in self.layer_stack:
            layer.mark_dirty()
        self.engine.render(self.layer_stack)
        tex_id = self.engine.get_texture_id()
        glBindTexture(GL_TEXTURE_2D, tex_id)
        data = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_UNSIGNED_BYTE)
        arr = np.frombuffer(data, dtype=np.uint8).reshape(SIZE, SIZE, 4)
        return arr[::-1].copy()

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
        # --- Blur/Sharpen post-process layer ---
        base = BaseLayer()
        base.base_color = [0.2, 0.2, 0.4]
        fres = FresnelLayer()  # some high-frequency edge content to blur/sharpen
        fres.color = [1.0, 0.6, 0.0]
        fres.intensity = 1.0
        fres.power = 6.0

        bs = BlurSharpenLayer()
        bs.mode = "Blur"
        bs.radius = 0.8

        for layer in [base, fres]:
            self.layer_stack.add_layer(layer)
            layer.initialize()

        img_no_bs = self.capture()
        check("no GL error before blur layer", glGetError() == GL_NO_ERROR)

        self.layer_stack.add_layer(bs)
        bs.initialize()
        img_blur = self.capture()
        check("no GL error after blur (2-pass) render", glGetError() == GL_NO_ERROR)
        check("blur changes the output", not np.array_equal(img_no_bs, img_blur))

        # Blur must NOT enlarge the silhouette (matcap circle) outward.
        cov_base = (img_no_bs[:, :, 3] > 0).sum()
        cov_blur = (img_blur[:, :, 3] > 0).sum()
        check("blur does not expand the circle coverage", cov_blur <= cov_base)
        # Any pixel transparent in the base must stay transparent after blur.
        new_outside = ((img_no_bs[:, :, 3] == 0) & (img_blur[:, :, 3] > 0)).sum()
        check("blur adds no coverage outside original silhouette", new_outside == 0)

        bs.mode = "Sharpen"
        bs.amount = 1.5
        img_sharp = self.capture()
        check("no GL error after sharpen render", glGetError() == GL_NO_ERROR)
        check("sharpen differs from blur", not np.array_equal(img_blur, img_sharp))

        bs.opacity = 0.0
        img_bs_off = self.capture()
        check("blur/sharpen opacity=0 restores input",
              np.array_equal(img_bs_off, img_no_bs))

        self.layer_stack.remove_layer(bs)

        # --- Image layer: render, anisotropic scale, blur ---
        make_checker(TMP_IMG)
        img_layer = ImageLayer()
        img_layer.image_path = TMP_IMG
        img_layer.mapping_mode = "Planar"
        img_layer.blend_mode = "Normal"
        self.layer_stack.add_layer(img_layer)
        img_layer.initialize()

        img_layer.scale_x = 2.0
        img_layer.scale_y = 1.0
        cap_sx = self.capture()
        check("no GL error after image render", glGetError() == GL_NO_ERROR)

        img_layer.scale_x = 1.0
        img_layer.scale_y = 2.0
        cap_sy = self.capture()
        check("Scale X vs Scale Y produce different output",
              not np.array_equal(cap_sx, cap_sy))

        img_layer.scale_x = 1.0
        img_layer.scale_y = 1.0
        img_layer.blur = 0.0
        cap_noblur = self.capture()
        img_layer.blur = 0.9
        cap_blur = self.capture()
        check("no GL error after image blur render", glGetError() == GL_NO_ERROR)
        check("image blur changes the output",
              not np.array_equal(cap_noblur, cap_blur))

        Image.fromarray(img_sharp).save("tests/verify_blur_sharpen_output.png")
        print("Saved tests/verify_blur_sharpen_output.png")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Harness()
    w.show()
    app.exec()
    if os.path.exists(TMP_IMG):
        os.remove(TMP_IMG)
    if failures:
        print(f"\n{len(failures)} FAILURE(S):", failures)
        sys.exit(1)
    print("\nALL CHECKS PASSED")
    sys.exit(0)
