
import time
import math
import random

import numpy as np
import moderngl as mg
from PyQt5 import QtWidgets
from PyQt5 import QtCore


simple_vertex_shader_code = """
    #version 430

    in vec2 in_vert;
    in vec2 in_uv;
    in vec3 in_col;

    out vec2 v_pos;
    out vec2 v_uv;
    out vec3 v_col;

    out float v_rad;
    void main()
    {
        v_uv = in_uv;
        v_col = in_col;

        gl_Position = vec4(in_vert.xy, 0.0, 1.0);
        v_pos = abs(in_vert.xy);
    }
    """

simple_fragment_shader_code = """
    #version 430

    in vec2 v_pos;
    in vec2 v_uv;
    in vec3 v_col;
    out vec4 out_color;
    void main()
    {
        if (length(vec2(0.5, 0.5) - v_uv.xy) > 0.25)
        {
            discard;
        }

        vec3 c = v_col;
        c.xy += v_uv.xy * 0.05;
        c.xy += v_pos.xy * 0.75;
        out_color = vec4(c, 1.0);
    }
    """

# calc position with compute shader
compute_worker_shader_code = """
#version 430

layout(local_size_x=%COMPUTE_SIZE%) in;
layout(binding=0) buffer balls_in
{
    vec4 pos[1];
    vec4 vel[1];
    vec4 col[1];
} In;
layout(binding=1) buffer balls_out
{
    vec4 pos[1];
    vec4 vel[1];
    vec4 col[1];
} Out;

void main()
{
    int x = int(gl_LocalInvocationIndex);

    vec4 p = In.pos[x];
    vec4 v = In.vel[x];
    vec4 c = In.col[x];

    p.xy += v.xy;

    float rad = p.w * 0.5;
    if (p.x - rad <= -1.0)
    {
        p.x = -1.0 + rad;
        v.x *= -1.0;
    }
    else if (p.x + rad >= 1.0)
    {
        p.x = 1.0 - rad;
        v.x *= -1.0;
    }

    if (p.y - rad <= -1.0)
    {
        p.y = -1.0 + rad;
        v.y *= -1.0;
    }
    else if (p.y + rad >= 1.0)
    {
        p.y = 1.0 - rad;
        v.y *= -1.0;
    }

    Out.pos[x] = p;
    Out.vel[x] = v;
    Out.col[x] = c;
}
"""


class ComputeToggleTimer(QtCore.QThread):
    compute_update_signal = QtCore.pyqtSignal(bool)

    def __init__(self, group_x):
        super(ComputeToggleTimer, self).__init__()
        self.toggle_buffer = False

    def run(self):
        while True:
            self.toggle_buffer = not self.toggle_buffer
            self.compute_update_signal.emit(self.toggle_buffer)
            self.msleep(32)


class Renderer(QtWidgets.QOpenGLWidget):
    COUNT = 128
    STRUCT_SIZE = 12

    worker_thread = None

    def __init__(self):
        super(Renderer, self).__init__()
        W, H = 480, 480
        self.setMinimumSize(W, H)
        self.setMaximumSize(W, H)
        self.viewport = (0, 0, W, H)

    def update_computeworker(self, toggle):
        if toggle:
            a, b = 0, 1
            self.target_buffer = self.compute_buffer_b
        else:
            a, b = 1, 0
            self.target_buffer = self.compute_buffer_a

        self.compute_buffer_a.bind_to_storage_buffer(a)
        self.compute_buffer_b.bind_to_storage_buffer(b)

        self.compute_shader.run(group_x=Renderer.STRUCT_SIZE)

        if False:
            data = np.frombuffer(self.target_buffer.read(), dtype='f4')
            data = data.reshape((Renderer.COUNT, Renderer.STRUCT_SIZE))
            np.set_printoptions(threshold=np.nan)
            with open('debug.log', 'w') as fp:
                fp.write(f'x, y \t| vx, vy \t| r, g, b\n')
                for line in data:
                    fp.write(f'{line[0]:.2f}, {line[1]:.2f}    \t| ')
                    fp.write(f'{line[4]:.2f}, {line[5]:.2f}    \t| ')
                    fp.write(f'{line[8]:.2f}, {line[9]:.2f}, {line[10]:.2f}  \n')

    def initializeGL(self):
        self.context = mg.create_context()
        self.program = self.context.program(
            vertex_shader=simple_vertex_shader_code,
            fragment_shader=simple_fragment_shader_code
        )

        index_data = np.array([
            0, 1, 2,
            1, 2, 3,
        ]).astype('i4')
        self.index_buffer = self.context.buffer(index_data.tobytes())

        self.vbo_data = np.array([
            # x     y     u    v     r    g    b
            [-1.0, -1.0,  0.0, 0.0,  0.0, 0.0, 0.0],
            [-1.0, +1.0,  0.0, 1.0,  0.0, 0.0, 0.0],
            [+1.0, -1.0,  1.0, 0.0,  0.0, 0.0, 0.0],
            [+1.0, +1.0,  1.0, 1.0,  0.0, 0.0, 0.0],
        ]).astype('f4')

        compute_shader_code_parsed = compute_worker_shader_code.replace("%COMPUTE_SIZE%", str(Renderer.COUNT))
        self.compute_shader = self.context.compute_shader(compute_shader_code_parsed)

        compute_data = []
        for i in range(Renderer.COUNT):
            _angle = (i / Renderer.COUNT) * math.pi * 2.0
            _dist = 0.125
            radius = random.random() * 0.04 + 0.04
            x = math.cos(_angle) * _dist
            y = math.sin(_angle) * _dist
            z = 0.0
            w = radius
            _v = random.random() * 0.045 + 0.025
            vx = math.cos(_angle) * _v
            vy = math.sin(_angle) * _v
            vz = 0.0
            vw = 0.0
            r = random.random()
            g = random.random()
            b = random.random()
            a = 0.0

            # match bytes
            compute_data.append(
                [x, y, z, w,  vx, vy, vz, vw,  r, g, b, a])

        compute_databytes = np.array(compute_data).astype('f4').tobytes()

        self.compute_buffer_a = self.context.buffer(compute_databytes)
        self.compute_buffer_b = self.context.buffer(compute_databytes)
        self.target_buffer = self.compute_buffer_b

        self.timer_thread = ComputeToggleTimer(Renderer.STRUCT_SIZE)
        self.timer_thread.compute_update_signal.connect(self.update_computeworker)
        self.timer_thread.start()

    def paintGL(self):
        self.context.viewport = self.viewport
        data = np.frombuffer(self.target_buffer.read(), dtype='f4')
        data = data.reshape((Renderer.COUNT, Renderer.STRUCT_SIZE))

        self.vaos = []
        for i, item in enumerate(data):
            # popout 1x1 quad
            item_vertex = self.vbo_data.copy()

            # apply rad
            item_vertex[:, [0, 1]] *= item[3]

            # xy
            item_vertex[:, 0] += item[0]
            item_vertex[:, 1] += item[1]

            # rgb
            item_vertex[:, 4] = item[8]
            item_vertex[:, 5] = item[9]
            item_vertex[:, 6] = item[10]

            # generate vertex buffer object to render
            item_vertex_buffer = self.context.buffer(item_vertex.tobytes())
            bo = [(
                item_vertex_buffer,
                '2f 2f 3f',
                'in_vert', 'in_uv', 'in_col'
            )]

            # generate vertex array object and render
            self.context.vertex_array(
                self.program, bo, self.index_buffer
            ).render()
        self.update()

        self.context.clear(0, 0, 0)


def main():
    app = QtWidgets.QApplication([])
    mainwin = QtWidgets.QMainWindow()
    root = QtWidgets.QFrame()
    root_ly = QtWidgets.QVBoxLayout()
    renderer = Renderer()
    root_ly.addWidget(renderer)
    root.setLayout(root_ly)
    mainwin.setCentralWidget(root)
    mainwin.show()
    app.exec()

if __name__ == "__main__":
    main()
