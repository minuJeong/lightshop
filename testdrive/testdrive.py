
import time
import math

import numpy as np
import moderngl
import imageio
from PIL import Image


def source(src, consts):
    with open(src) as fp:
        content = fp.read()

    for key, value in consts.items():
        content = content.replace(f"%%{key}%%", str(value))
    return content

W = 1280
H = 720
Y = 1
Z = 1
X = W
consts = {
    "X": X,
    "Y": Y,
    "Z": Z,
    "W": W,
    "H": H,
}

context = moderngl.create_standalone_context(require=430)
compute_shader = context.compute_shader(source('../gl/median_5x5.glsl', consts))

_scale = 1.0

grid = []
for u in np.linspace(0.0, 1.0, W):
    for v in np.linspace(0.0, 1.0, H):
        grid.append([u, v])
grid = np.array(grid).reshape((W, H, 2))

buffer_a = context.buffer(np.random.uniform(0.0, _scale, (W, H, 4)).astype('f4'))
buffer_b = context.buffer(np.ones((W, H, 4)).astype('f4'))
buffer_s = context.buffer(grid.astype('f4'))
buffer_s.bind_to_storage_buffer(2)

last_buffer = buffer_b

imgs = []
for i in range(48):
    toggle = i % 2
    buffer_a.bind_to_storage_buffer(1 if toggle else 0)
    buffer_b.bind_to_storage_buffer(0 if toggle else 1)
    last_buffer = buffer_a if toggle else buffer_b

    compute_shader.run(group_x=H, group_y=1)

    # print out
    output = np.frombuffer(last_buffer.read(), dtype=np.float32)
    output = output.reshape((H, W, 4))
    output = np.multiply(output, 255).astype(np.uint8)
    imgs.append(output)

    print(f"executed {i}, {toggle}!")

imageio.mimwrite("./output/out.gif", imgs, duration=0.1)
