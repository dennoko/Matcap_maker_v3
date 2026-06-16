"""CPU-side image post-processing for exports (texture dilation / padding).

Prevents UV-seam bleeding by extending valid colors outward into the
transparent surroundings before saving. See DOCS/technical_manual/05.
"""
import numpy as np

# 8-neighbourhood: cardinal + diagonal
_SHIFTS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1),
]


def dilate(image, iterations):
    """Extend valid (alpha > 0) pixels outward into transparent ones.

    image: (H, W, 4) uint8 RGBA array (not modified).
    Returns a new uint8 array. Each iteration grows the valid region by one
    pixel, filling each hole with the average of its valid 8-neighbours.

    Works in float32 throughout and rounds once at the end, so repeated
    averaging doesn't accumulate uint8 truncation errors.
    """
    if iterations <= 0:
        return image.copy()

    current = image.astype(np.float32)
    h, w = current.shape[:2]

    # Scratch buffers reused across iterations (a 4K image is ~270MB as
    # float32; reallocation per direction/iteration dominates runtime).
    accum = np.empty_like(current)
    count = np.empty((h, w, 1), dtype=np.float32)
    shifted = np.empty_like(current)

    for _ in range(iterations):
        holes = current[:, :, 3] <= 0
        if not holes.any():
            break

        accum.fill(0.0)
        count.fill(0.0)

        for dy, dx in _SHIFTS:
            # Shift without wrap-around (np.roll would bleed across edges)
            shifted.fill(0.0)
            src_y = slice(max(0, -dy), min(h, h - dy))
            src_x = slice(max(0, -dx), min(w, w - dx))
            dst_y = slice(max(0, dy), min(h, h + dy))
            dst_x = slice(max(0, dx), min(w, w + dx))
            shifted[dst_y, dst_x] = current[src_y, src_x]

            fillable = holes & (shifted[:, :, 3] > 0)
            accum[fillable] += shifted[fillable]
            count[fillable] += 1.0

        valid = count[:, :, 0] > 0
        current[valid] = accum[valid] / count[valid]

    return np.rint(np.clip(current, 0.0, 255.0)).astype(np.uint8)


def fill_background(image, color=(0, 0, 0, 255)):
    """Fill fully transparent pixels with a solid color (in place)."""
    image[image[:, :, 3] == 0] = color
    return image
