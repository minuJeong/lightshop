
import time
import math

import numpy as np
import moderngl

from PIL import Image


def source(args):
    with open('testdrive.gl') as fp:
        content = fp.read()

    for key, value in args.items():
        content = content.replace(f"%%{key}%%", str(value))
    return content

# W = X * Y  // for each run, handles one line of pixels
# execute compute shader for H times to complete
X = 512
Y = 1
Z = 1
W = 512
H = 512
definer = {
    "X": X,
    "Y": Y,
    "Z": Z,
    "W": W,
    "H": H,
}

context = moderngl.create_standalone_context(require=430)
compute_shader = context.compute_shader(source(definer))

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
i = 0
while True:

    toggle = i % 2
    buffer_a.bind_to_storage_buffer(1 if toggle else 0)
    buffer_b.bind_to_storage_buffer(0 if toggle else 1)
    last_buffer = buffer_a if toggle else buffer_b

    for x in range(1, H + 1):
        compute_shader.run(group_x=x, group_y=1)

    # print out
    output = np.frombuffer(last_buffer.read(), dtype=np.float32)
    output = output.reshape((H, W, 4))
    output = np.multiply(output, 255).astype(np.int8)
    img = Image.fromarray(output, "RGBA")
    img.save("testdrive.tiff")

    print(f"executed {i}, {toggle}!")
    time.sleep(2.0)

    i += 1

"""
# DEBUG TIFF EXPORTING

data = []
C = W + H
for x in range(W):
    for y in range(H):
        v = (x + y) / C
        data.append((v, v, v))
data = np.array(data).reshape((W, H, 3))
img = Image.fromarray(np.multiply(data, 255.0).astype(np.int8), "RGB")
img.save("uvs.tiff")
"""
