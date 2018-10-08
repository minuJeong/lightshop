
import math

import numpy as np
import moderngl


def source(args):
    with open('testdrive.gl') as fp:
        content = fp.read()

    for key, value in args.items():
        content = content.replace(f"%%{key}%%", str(value))
    return content

X = 32
Y = 32
WIDTH = 512
HEIGHT = 512
CHANNEL = 4
definer = {
    "X": X,
    "Y": Y,
    "WIDTH": WIDTH,
    "HEIGHT": HEIGHT,
    "CHANNEL": CHANNEL,
}

context = moderngl.create_standalone_context(require=430)
buffer_a = context.buffer(np.random.uniform(0.0, 100.0, (WIDTH, HEIGHT, CHANNEL)).astype('f4'))
buffer_b = context.buffer(np.zeros((WIDTH, HEIGHT, CHANNEL)).astype('f4'))
compute_shader = context.compute_shader(source(definer))

buffer_a.bind_to_storage_buffer(0)
buffer_b.bind_to_storage_buffer(1)

texres = WIDTH * HEIGHT
groupres = X * Y
for x in range(0, math.ceil(texres / groupres)):
    compute_shader.run(group_x=x, group_y=1)

# print out
output = np.frombuffer(buffer_b.read(), dtype=np.float32)
output = output.reshape((WIDTH, HEIGHT, CHANNEL))
for row in output:
    print(',\t'.join(map(lambda e: f"{e:.3f}", [x[0] for x in row.tolist()])))
