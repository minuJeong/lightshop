
import os
import sys

sys.path.append(os.path.dirname(__file__))


import numpy as np
from PIL import Image

from _common import _flatten_array


def _randomized_vertical_gradient(width, height):
    import random

    def lerp(x, y, w):
        rw = 1.0 - w
        r = x[0] * rw + y[0] * w
        g = x[1] * rw + y[1] * w
        b = x[2] * rw + y[2] * w
        return r, g, b

    palettes = []
    for i in range(10):
        v = i * 0.1 + random.random() * 0.1
        palettes.append((v, v, v))

    palettes[0] = (0.0, 0.0, 0.0)
    palettes[9] = (1.0, 1.0, 1.0)

    data = np.zeros(shape=(height, width, 4))
    for x in range(width):
        for y in range(height):
            hr = y / height

            for i in range(1, 10):
                if hr < i * 0.1:
                    p = (hr - ((i - 1) * 0.1)) / 0.1
                    p0 = palettes[i - 1]
                    p1 = palettes[i - 0]
                    r, g, b = lerp(p0, p1, p)
                    break
            data[y, x] = (r, g, b, 1.0)
    return _flatten_array(data)


def _generate_screentone(width, height):
    data = np.zeros(shape=(height, width, 4))
    for x in range(height):
        for y in range(width):
            if abs((x % 4) - (y % 4)) < 0.4:
                data[x, y] = (0, 0, 0, 1.0)
            else:
                data[x, y] = (1, 1, 1, 1.0)
    return _flatten_array(data)


if __name__ == "__main__":
    data = _generate_screentone(512, 512)
    img = Image.fromarray(data)
    img.save("input_tex.png")
