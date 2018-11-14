
from PyQt5 import QtWidgets
import moderngl as mg
import numpy as np


vertex_shader = """
#version 430

in vec3 in_vert;
in vec2 in_texcoord0;

out vec2 v_texcoord0;

void main()
{
    v_texcoord0 = in_texcoord0;
    gl_Position = vec4(in_vert, 0.0);
}
"""

fragment_shader = """
#version 430

in vec2 v_texcoord0;
out vec4 out_color;
void main()
{
    out_color = vec4(v_texcoord0, 0.5, 1.0);
}
"""


class Renderer(QtWidgets.QOpenGLWidget):
    def __init__(self):
        super(Renderer, self).__init__()
        W, H = 500, 500
        self.setMaximumSize(W, H)
        self.setMinimumSize(W, H)
        self.vaos = []

    def initializeGL(self):
        context = mg.create_context()
        program = context.program(
            vertex_shader=vertex_shader, fragment_shader=fragment_shader)

        vertex_data = np.array([
            # x     y     z     u    v
            (-1.0, -1.0, +0.0,  0.0, 0.0),
            (-1.0, +1.0, +0.0,  1.0, 0.0),
            (+1.0, -1.0, +0.0,  0.0, 1.0),
            (+1.0, +1.0, +0.0,  1.0, 1.0),
        ]).astype(np.float32)
        index_data = np.array([
            0, 1, 2,
            1, 2, 3
        ]).astype(np.int32)
        vb = context.buffer(vertex_data.tobytes())
        ib = context.buffer(index_data.tobytes())

        content = [(
            vb,
            '3f 2f',
            'in_vert', 'in_texcoord0'
        )]
        self.vaos.append(
            context.vertex_array(program, content, ib))

    def paintGL(self):
        for vao in self.vaos:
            vao.render()


def main():
    app = QtWidgets.QApplication([])

    mainwin = QtWidgets.QMainWindow()
    root_widget = QtWidgets.QWidget()
    root_layout = QtWidgets.QVBoxLayout()
    renderer = Renderer()
    root_layout.addWidget(renderer)
    root_widget.setLayout(root_layout)
    mainwin.setCentralWidget(root_widget)
    mainwin.show()

    app.exec()

if __name__ == "__main__":
    main()
