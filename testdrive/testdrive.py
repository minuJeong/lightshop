
from itertools import product
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

# W = X * Y  // for each run, handles a row of pixels
# execute compute shader for H times to complete
W = 256
H = 128
X = W
Y = 1
Z = 1
definer = {
    "W": W,
    "H": H,
    "X": X + 1,
    "Y": Y,
    "Z": Z,
}

context = moderngl.create_standalone_context(require=430)
compute_shader = context.compute_shader(source(definer))

# init buffers
buffer_a_data = np.random.uniform(0.0, 1.0, (H, W, 4)).astype('f4')
buffer_a = context.buffer(buffer_a_data)
buffer_b_data = np.zeros((H, W, 4)).astype('f4')
buffer_b = context.buffer(buffer_b_data)

# debug buffer a
debug_a = buffer_a_data[:, :, 0]
debug_a = np.multiply(debug_a, 255.0).astype(np.uint8).reshape((H, W))
Image.fromarray(debug_a, "L").save("testdrive_buffer_a_r.png")

last_buffer = buffer_b
i = 0
for _ in range(10):
    toggle = True if i % 2 else False
    buffer_a.bind_to_storage_buffer(1 if toggle else 0)
    buffer_b.bind_to_storage_buffer(0 if toggle else 1)
    last_buffer = buffer_a if toggle else buffer_b

    for x in range(10, H + 1):
        compute_shader.run(group_x=x, group_y=1)

    # print out
    output = np.frombuffer(last_buffer.read(), dtype=np.float32)
    output = output.reshape((H, W, 4))
    output = np.multiply(output, 255).astype(np.uint8)
    img = Image.fromarray(output, "RGBA")
    img.save(f"testdrive_{i}.png")

    print(f"executed {i}")
    time.sleep(0.1)

    i += 1

"""
# DEBUG TESTS

grid = []
for u in np.linspace(0.0, 1.0, W):
    for v in np.linspace(0.0, 1.0, H):
        grid.append([u, v])
grid = np.array(grid).reshape((W, H, 2))
buffer_s = context.buffer(grid.astype('f4'))
buffer_s.bind_to_storage_buffer(2)

data = []
C = W + H
for x in range(W):
    for y in range(H):
        v = (x + y) / C
        data.append((v, v, v))
data = np.array(data).reshape((W, H, 3))
img = Image.fromarray(np.multiply(data, 255.0).astype(np.int8), "RGB")
img.save("uvs.tiff")


# debug grid
grid_img_data = np.zeros((H, W, 4), dtype=np.float32)
grid_img_data[:, :, [0, 1]] = grid[:, :,[0, 1]].transpose((1, 0, 2))
grid_img_data[:, :, [2, 3]] = [0.1, 1.0]
grid_img_data = np.multiply(grid_img_data, 255.0).astype(np.uint8)
grid_img = Image.fromarray(grid_img_data, "RGBA")
grid_img.save("grid.png")

# save grid target
grid_target = Image.new("RGBA", (W, H))
grid_target_px = grid_target.load()
for x in range(W):
    for y in range(H):
        r = int((float(x) / W) * 255.0)
        g = int((float(y) / H) * 255.0)
        grid_target_px[x, y] = (r, g, 128, 255)
grid_target.save("grid_target.png")

grid_target_buffered = np.array(grid_target).astype(np.uint8).reshape((H, W, 4))
# grid_target_buffered[:,:,3] = 255
grid_target_buffered[:,:] = grid_target_buffered[::-1,::]
grid_target_buffered = memoryview(grid_target_buffered)
grid_target_buffered_img = Image.frombuffer("RGBA", (W, H), grid_target_buffered, 'raw', "RGBA", 0, 1)
grid_target_buffered_img.save("grid_target_rearranged.png")


img_d = np.zeros((H, W, 4), dtype=np.uint8)
img_d[:, :, :] = (0, 128, 64, 255)
for row in img_d[:, :, :]:
    row[:, 0] += np.linspace(0, 255, W).astype(np.uint8)
img_d[:, 0, 0] += np.linspace(0, 255, H).astype(np.uint8)
img_d_i = Image.fromarray(img_d, "RGBA")
img_d_i.save("img_d_i.png")

"""
