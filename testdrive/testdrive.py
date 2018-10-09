
import math

import numpy as np
import moderngl


def source(args):
    with open('testdrive.gl') as fp:
        content = fp.read()

    for key, value in args.items():
        content = content.replace(f"%%{key}%%", str(value))
    return content

# W = X * Y  // for each run, handles one line of pixels
# execute compute shader for H times to complete
X = 8
Y = 8
W = 64
H = 64
definer = {
    "X": X,
    "Y": Y,
    "WIDTH": W,
    "HEIGHT": H,
}

context = moderngl.create_standalone_context(require=430)
compute_shader = context.compute_shader(source(definer))

data = np.random.uniform(0.0, 100.0, (W, H))
buffer_a = context.buffer(data.astype('f4'))
buffer_b = context.buffer(np.ones((W, H)).astype('f4'))
buffer_a.bind_to_storage_buffer(0)
buffer_b.bind_to_storage_buffer(2)

for y in range(0, H):
    compute_shader.run(group_x=1, group_y=y)

# print out
output = np.frombuffer(buffer_b.read(), dtype=np.float32)
output = output.reshape((W, H))

np.set_printoptions(linewidth=100000, threshold=np.NaN)
print(output)
