
'''
    example of using compute shader.

    requirements:
     - numpy
     - imageio (for output)
'''

import os

import moderngl
import numpy as np
import imageio  # for output


def source(uri, consts):
    ''' read gl code '''
    with open(uri, 'r') as fp:
        content = fp.read()

    # feed constant values
    for key, value in consts.items():
        content = content.replace(f"%%{key}%%", str(value))
    return content

# W = X * Y  // for each run, handles a row of pixels
# execute compute shader for H times to complete
W = 173
H = 111
X = W
Y = 1
Z = 1
consts = {
    "W": W,
    "H": H,
    "X": X + 1,
    "Y": Y,
    "Z": Z,
}

FRAMES = 50
OUTPUT_DIRPATH = "./output"

if not os.path.isdir(OUTPUT_DIRPATH):
    os.makedirs(OUTPUT_DIRPATH)

context = moderngl.create_standalone_context(require=430)
compute_shader = context.compute_shader(source('../gl/median_5x5.gl', consts))

# init buffers
buffer_a_data = np.random.uniform(0.0, 1.0, (H, W, 4)).astype('f4')
buffer_a = context.buffer(buffer_a_data)
buffer_b_data = np.zeros((H, W, 4)).astype('f4')
buffer_b = context.buffer(buffer_b_data)

imgs = []
last_buffer = buffer_b
for i in range(FRAMES):
    toggle = True if i % 2 else False
    buffer_a.bind_to_storage_buffer(1 if toggle else 0)
    buffer_b.bind_to_storage_buffer(0 if toggle else 1)

    # toggle 2 buffers as input and output
    last_buffer = buffer_a if toggle else buffer_b

    # local invocation id x -> pixel x
    # work groupid x -> pixel y
    # eg) buffer[x, y] = gl_LocalInvocationID.x + gl_WorkGroupID.x * W
    compute_shader.run(group_x=H, group_y=1)

    # print out
    output = np.frombuffer(last_buffer.read(), dtype=np.float32)
    output = output.reshape((H, W, 4))
    output = np.multiply(output, 255).astype(np.uint8)
    imgs.append(output)

# if you don't want to use imageio, remove this line
import io

output_gif = f"./{OUTPUT_DIRPATH}/debug.gif"
imageio.mimwrite(output_gif, imgs, "GIF", duration=0.1)

from PyQt5 import QtWidgets
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QMargins
from PyQt5.QtCore import QByteArray
from PyQt5.QtCore import QBuffer
from PyQt5.QtCore import QIODevice


class ModernPyQtGL(QtWidgets.QOpenGLWidget):
    def initializeGL(self):
        self.context = moderngl.create_context(require=430)
        self.cs = context.compute_shader(source('../gl/median_5x5.gl', consts))
        print(self.context)

    def paintGL(self):

        self.update()

    def resizeGL(self, w, h):
        self.glViewport(0, 0, w, h)

app = QtWidgets.QApplication([])
widget = QtWidgets.QWidget(None, Qt.WindowStaysOnTopHint)
root_layout = QtWidgets.QVBoxLayout()
root_layout.setSpacing(1)
gl_box = ModernPyQtGL()
root_layout.addWidget(gl_box)
widget.setLayout(root_layout)
widget.show()
app.exec()

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
