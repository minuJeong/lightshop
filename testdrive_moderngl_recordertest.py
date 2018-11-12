
import time

import numpy as np
import moderngl as mg
import imageio as ii

from PyQt5 import QtWidgets


vertex_shader = """
#version 430

in vec3 in_verts;
in vec2 in_uv;

out vec2 v_uv;

void main()
{
    v_uv = in_uv;
    gl_Position = vec4(in_verts, 1.0);
}
"""

fragment_shader = """
#version 430

uniform float T;

in vec2 v_uv;

out vec4 out_color;

void main()
{
    if (T < 1.0)
    {
        out_color = vec4(v_uv, sin(T * 10.0), 1.0);
    }
    else if (T < 5.0)
    {
        vec2 uv = v_uv;
        uv = uv * 2.0 - 1.0;
        float l = dot(uv, uv);
        vec3 rgb = vec3(l, cos(T), 0.0);
        out_color = vec4(rgb, 1.0);
    }
    else
    {
        out_color = vec4(0.2, 0.0, 0.0, 1.0);
    }
}
"""

class Renderer(QtWidgets.QOpenGLWidget):
    def __init__(self):
        super(Renderer, self).__init__()

        self.W, self.H = 400, 400
        self.viewport = (0, 0, self.W, self.H)
        self.setMinimumSize(self.W, self.H)
        self.setMaximumSize(self.W, self.H)

    def initializeGL(self):
        self.context = mg.create_context()
        self.context.viewport = self.viewport
        program = self.context.program(
            vertex_shader=vertex_shader, fragment_shader=fragment_shader)

        verts = np.array([
            -1.0, -1.0, +0.0,  0.0, 0.0,
            -1.0, +1.0, +0.0,  0.0, 1.0,
            +1.0, -1.0, +0.0,  1.0, 0.0,
            +1.0, +1.0, +0.0,  1.0, 1.0
        ]).astype('f4')

        indices = np.array([
            0, 1, 2,
            1, 2, 3
        ]).astype('i4')

        self.vao = self.context.vertex_array(
            program,
            [(
                self.context.buffer(verts.tobytes()),
                "3f 2f",
                "in_verts", "in_uv"
            )], self.context.buffer(indices.tobytes()))
        self.out_texture = self.context.texture((512, 512), 3, dtype='f4')
        self.framebuffer = self.context.framebuffer(self.out_texture)

        self.recordings = []

        self.unif_t = program['T']
        self.prev_time = time.time()
        self.elapsed_time = 0.0

    def paintGL(self):
        t = time.time()
        delta_time = t - self.prev_time
        self.elapsed_time += delta_time
        self.unif_t.value = self.elapsed_time
        self.prev_time = t

        self.vao.render()
        self.update()

        self.framebuffer.use()
        self.vao.render()

        self.recordings.append(np.frombuffer(self.out_texture.read(), dtype=np.float32))

    def closeEvent(self, e):
        converted_arrays = []
        for record in self.recordings:
            converted_out = record.reshape((512, 512, 3))
            converted_out = converted_out * 255.0
            converted_out = converted_out.astype(np.uint8)
            converted_arrays.append(converted_out)
        ii.mimwrite("output.mp4", converted_arrays)
        self.recordings = []

def main():
    app = QtWidgets.QApplication([])
    renderer = Renderer()
    renderer.show()
    app.exec()

if __name__ == "__main__":
    main()
