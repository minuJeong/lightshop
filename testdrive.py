
import math

import pymunk as pm
import numpy as np
import moderngl as mg
from PyQt5 import QtWidgets


class Renderer(QtWidgets.QOpenGLWidget):

    def __init__(self):
        super(Renderer, self).__init__()
        W, H = 720, 480
        self.setMinimumSize(W, H)
        self.setMaximumSize(W, H)
        self.viewport = (0, 0, W, H)

        self.space = pm.Space()
        self.space.gravity = (0, -1000)

        self.scene_items = []
        for i in range(10):
            _angle = (i / 10) * math.pi * 2.0
            _dist = 0.2
            px = math.cos(_angle) * _dist
            py = math.sin(_angle) * _dist
            body = pm.Body(1, 1666)
            body.position = (px, py)
            self.scene_items.append(body)
            poly = pm.Poly.create_box(body)
            self.space.add(body, poly)

        self.space.step(0.02)

    def initializeGL(self):
        self.context = mg.create_context()
        self.program = self.context.program(
            vertex_shader="""
            #version 430

            in vec2 in_objpos;
            in vec2 in_vert;
            in vec2 in_uv;
            out vec2 v_uv;
            out vec3 v_cc;
            void main()
            {
                v_uv = in_uv;
                v_cc = vec3(in_objpos.xy + in_vert.xy, 0.0);
                gl_Position = vec4(in_objpos.xy + in_vert.xy, 0.0, 1.0);
            }
            """,
            fragment_shader="""
            #version 430

            in vec2 v_uv;
            in vec3 v_cc;
            out vec4 out_color;
            void main()
            {
                vec3 c = vec3(v_uv.xy, 0.0);
                out_color = vec4(c, 1.0);
            }
            """
        )

        vbo_data = np.array([
            -1.0, -1.0,
            -1.0, +1.0,
            +1.0, -1.0,
            +1.0, +1.0,
        ]).astype('f4') * 0.2
        self.vertex_buffer = self.context.buffer(vbo_data.tobytes())

        uv_data = np.array([
            0.0, 0.0,
            0.0, 1.0,
            1.0, 0.0,
            1.0, 1.0,
        ]).astype('f4')
        self.uv_buffer = self.context.buffer(uv_data.tobytes())

        index_data = np.array([
            0, 1, 2,
            1, 2, 3,
        ]).astype('i4')
        self.index_buffer = self.context.buffer(index_data.tobytes())

        self.vaos = []
        for item in self.scene_items:
            pos_data = np.array([item.position.x, item.position.y]).astype('f4')
            pos_buffer = self.context.buffer(pos_data.tobytes())
            self.buffer_object = [
                (pos_buffer, '3f', 'in_objpos'),
                (self.vertex_buffer, '3f', 'in_vert'),
                (self.uv_buffer, '2f', 'in_uv'),
            ]

            vao = self.context.vertex_array(self.program, self.buffer_object, self.index_buffer)
            self.vaos.append(vao)

        self.bg_vao = self.context.vertex_array(self.program, [
            (self.vertex_buffer, '3f', 'in_vert'),
            (self.uv_buffer, '2f', 'in_uv'),
        ], self.index_buffer)

    def paintGL(self):
        self.context.viewport = self.viewport
        self.bg_vao.render()
        for vao in self.vaos:
            vao.render()
        print('paint!')


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
