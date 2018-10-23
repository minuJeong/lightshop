
import time
import math
import random

import numpy as np
import moderngl as mg
from PyQt5 import QtWidgets


class Renderer(QtWidgets.QOpenGLWidget):
    COUNT = 1024

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
            out vec2 v_uv;
            void main()
            {
                v_uv = in_uv;
                vec4 vpos = vec4(in_vert.xy, 0.0, 1.0);
                gl_Position = vpos;
            }
            """,
            fragment_shader="""
            #version 430

            in vec2 v_uv;
            out vec4 out_color;
            void main()
            {
                if (length(vec2(0.5, 0.5) - v_uv.xy) > 0.25)
                {
                    discard;
                }
                out_color = vec4(v_uv.xy, 0.0, 1.0);
            }
            """
        )

        index_data = np.array([
            0, 1, 2,
            1, 2, 3,
        ]).astype('i4')
        self.index_buffer = self.context.buffer(index_data.tobytes())

        self.vbo_data = np.array([
            # x     y     u    v
            [-1.0, -1.0,  0.0, 0.0, ],
            [-1.0, +1.0,  0.0, 1.0, ],
            [+1.0, -1.0,  1.0, 0.0, ],
            [+1.0, +1.0,  1.0, 1.0, ],
        ]).astype('f4')

        self.prevframe = time.time()

        # calc position with compute shader
        self.compute_shader = self.context.compute_shader("""
        #version 430
        layout(local_size_x=1024, local_size_y=1, local_size_z=1) in;
        layout(binding=0) buffer balls
        {
            float rad[1];
            vec2 pos[1];
            vec2 vel[1];
        };

        void main()
        {
            const int x = int(gl_LocalInvocationID.x);
            const float r = rad[x];

            vec2 p = pos[x];
            vec2 v = vel[x];
            p += v;
            if (p.x - r <= -1.0)
            {
                p.x = -1.0 + r;
                v.x *= -1.0;
            }
            else if (p.x + r >= 1.0)
            {
                p.x = 1.0 - r;
                v.x *= -1.0;
            }

            if (p.y - r <= -1.0)
            {
                p.y = -1.0 + r;
                v.y *= -1.0;
            }
            else if (p.y + r >= 1.0)
            {
                p.y = 1.0 - r;
                v.y *= -1.0;
            }

            pos[x] = p;
            vel[x] = v;
        }
        """)

        compute_data = []
        for i in range(Renderer.COUNT):
            _angle = (i / Renderer.COUNT) * math.pi * 2.0
            _dist = 0.125
            radius = random.random() * 0.04 + 0.04
            x = math.cos(_angle) * _dist
            y = math.sin(_angle) * _dist
            _v = random.random() * 0.000045 + 0.000025
            vx = math.cos(_angle) * _v
            vy = math.sin(_angle) * _v
            compute_data.append([radius, x, y, vx, vy])

        self.compute_buffer = self.context.buffer(
            np.array(compute_data).astype('f4').tobytes()
        )
        self.compute_buffer.bind_to_storage_buffer(0)

    def paintGL(self):
        self.context.viewport = self.viewport

        data = np.frombuffer(self.compute_buffer.read(), dtype=np.float32)
        data = data.reshape((Renderer.COUNT, 5))
        self.vaos = []
        for i, item in enumerate(data):
            item_vertex = self.vbo_data.copy()
            item_vertex[:, [0, 1]] *= item[0]
            item_vertex[:, 0] += item[1]
            item_vertex[:, 1] += item[2]
            item_vertex_buffer = self.context.buffer(item_vertex.tobytes())
            bo = [
                (item_vertex_buffer, '2f 2f', 'in_vert', 'in_uv'),
            ]
            self.context.vertex_array(
                self.program, bo, self.index_buffer
            ).render()

        self.compute_shader.run(group_x=Renderer.COUNT)
        self.update()


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
