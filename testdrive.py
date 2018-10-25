
import time
import math
import random

import numpy as np
import moderngl as mg
from PyQt5 import QtWidgets
from PyQt5 import QtCore


class ComputeWorker(QtCore.QThread):
    def __init__(self):
        super(ComputeWorker, self).__init__()

    def run(self):
        print("RUN!!!")
        pass


class Renderer(QtWidgets.QOpenGLWidget):
    COUNT = 1024
    STRUCT_SIZE = 12

    def __init__(self):
        super(Renderer, self).__init__()
        W, H = 720, 720
        self.setMinimumSize(W, H)
        self.setMaximumSize(W, H)
        self.viewport = (0, 0, W, H)

    def initializeGL(self):
        self.context = mg.create_context()
        self.program = self.context.program(
            vertex_shader="""
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
            """,
            fragment_shader="""
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

        self.prevframe = time.time()

        # calc position with compute shader
        self.compute_shader = self.context.compute_shader("""
            #version 430
            layout(local_size_x=1, local_size_y=1, local_size_z=1) in;
            layout(binding=0) buffer balls_in
            {
                // pos.w <- radius
                // avoid to use vec2, vec3 in buffer structure
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
                const int x = int(gl_GlobalInvocationID.x);

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
        """)

        compute_data = []
        for i in range(Renderer.COUNT):
            _angle = (i / Renderer.COUNT) * math.pi * 2.0
            _dist = 0.125
            radius = random.random() * 0.02 + 0.06
            x = math.cos(_angle) * _dist
            y = math.sin(_angle) * _dist
            z = 0.0
            w = radius
            _v = random.random() * 0.0045 + 0.0025
            vx = math.cos(_angle) * _v
            vy = math.sin(_angle) * _v
            vz = 0.0
            vw = 0.0
            r = random.random()
            g = random.random()
            b = random.random()
            a = 0.0

            line = [x, y, z, w,  vx, vy, vz, vw,  r, g, b, a]
            compute_data.append(line)

        compute_databytes = np.array(compute_data).astype('f4').tobytes()

        self.compute_buffer_a = self.context.buffer(compute_databytes)
        self.compute_buffer_b = self.context.buffer(compute_databytes)
        self.toggle_buffer = False
        self.target_buffer = self.compute_buffer_b

    def paintGL(self):
        self.context.viewport = self.viewport

        self.toggle_buffer = not self.toggle_buffer
        a, b = (0, 1) if self.toggle_buffer else (1, 0)
        self.compute_buffer_a.bind_to_storage_buffer(a)
        self.compute_buffer_b.bind_to_storage_buffer(b)
        self.compute_shader.run(group_x=Renderer.COUNT)

        target_buffer = \
            self.compute_buffer_a \
            if self.toggle_buffer else \
            self.compute_buffer_b
        data = np.frombuffer(target_buffer.read(), dtype='f4')
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
            bo = [
                (
                    item_vertex_buffer,
                    '2f 2f 3f',
                    'in_vert', 'in_uv', 'in_col'),
            ]

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
