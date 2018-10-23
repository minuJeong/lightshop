
import time
import math
import random

import numpy as np
import moderngl as mg
from PyQt5 import QtWidgets


class Ball(object):
    radius = 0.02
    x = 0
    y = 0
    vx = 0
    vy = 0

class Renderer(QtWidgets.QOpenGLWidget):

    def __init__(self):
        super(Renderer, self).__init__()
        W, H = 720, 720
        self.setMinimumSize(W, H)
        self.setMaximumSize(W, H)
        self.viewport = (0, 0, W, H)

        COUNT = 500
        self.scene_items = []
        for i in range(COUNT):
            item = Ball()
            angle = (i / COUNT) * math.pi * 2.0
            dist = 0.125
            item.radius = random.random() * 0.04 + 0.01
            item.x = math.cos(angle) * dist
            item.y = math.sin(angle) * dist
            v = random.random() * 0.45 + 0.15
            item.vx = math.cos(angle) * v
            item.vy = math.sin(angle) * v
            self.scene_items.append(item)

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
        self.prevframe = time.time()

    def paintGL(self):
        self.context.viewport = self.viewport

        vbo_data = np.array([
            # pos xy      u    v
            [-1.0, -1.0,  0.0, 0.0, ],
            [-1.0, +1.0,  0.0, 1.0, ],
            [+1.0, -1.0,  1.0, 0.0, ],
            [+1.0, +1.0,  1.0, 1.0, ],
        ]).astype('f4')
        self.vaos = []
        for item in self.scene_items:
            item_vertex = vbo_data.copy()

            # apply attr
            item_vertex[:, [0, 1]] *= item.radius * 2.0
            item_vertex[:, [0, 1]] += [item.x, item.y]
            item_vertex_buffer = self.context.buffer(item_vertex.tobytes())
            self.buffer_object = [
                (item_vertex_buffer, '2f 2f', 'in_vert', 'in_uv'),
            ]

            vao = self.context.vertex_array(self.program, self.buffer_object, self.index_buffer)
            self.vaos.append(vao)

        for vao in self.vaos:
            vao.render()

        self.update()

        newtime = time.time()
        dt = newtime - self.prevframe
        self.prevframe = newtime

        for item in self.scene_items:
            item.x += item.vx * dt
            item.y += item.vy * dt

            if item.x - item.radius <= -1.0:
                item.x = -1.0 + item.radius
                item.vx *= -1
            elif item.x + item.radius >= 1.0:
                item.x = 1.0 - item.radius
                item.vx *= -1

            if item.y - item.radius <= -1.0:
                item.y = -1.0 + item.radius
                item.vy *= -1
            elif item.y + item.radius >= 1.0:
                item.y = 1.0 - item.radius
                item.vy *= -1


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
