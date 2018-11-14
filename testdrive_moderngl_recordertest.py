
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

#define MAX_TIME 5.0

uniform float T;

in vec2 v_uv;

out vec4 out_color;

float t;
vec2 uv;

vec4 flatten(float v)
{
    return vec4(v, v, v, 1.0);
}

vec4 func_grid()
{
    float a = length(v_uv);
    bool b_modx = mod(uv.x + sin(t * 4.34) * 0.002, 0.1) < 0.01;
    bool b_mody = mod(uv.y + cos(t * 4.34) * 0.002, 0.1) < 0.01;
    a = b_modx || b_mody ? sin(t * 2.22) * 0.5 + 0.5 : 0.0;
    return vec4(a, a, a, 1.0);
}

vec4 func_length_flat()
{
    float l = dot(uv, uv);
    return flatten(l);
}

vec4 func_coslength(float length_intensity, float time_intensity)
{
    float ll = dot(uv, uv) * length_intensity;
    float tt = t * time_intensity;
    float cl = cos(ll + tt) * 0.5 + 0.5;
    cl = pow(cl, 4.0);
    return flatten(cl);
}

vec4 func_rotator(float time_intensity, float intensity=1.0, float power=1.0)
{
    float tbased = t * time_intensity;
    float lbased = pow(length(uv), power);
    float angle = tbased + lbased;
    angle = angle * intensity;
    angle = mod(angle, 6.28);
    mat2 rm = mat2(
        +cos(angle), -sin(angle),
        +sin(angle), +cos(angle)
    );
    vec2 ruv = rm * uv;
    return vec4(ruv, ruv.x, 1.0);
}

vec4 timeline()
{
    // #define STEP (1.0 / 7.0)
    #define STEP (1.0 / 4.0)

    float kf_1 = MAX_TIME * (STEP * 1.0);
    float kf_2 = MAX_TIME * (STEP * 2.0);
    float kf_3 = MAX_TIME * (STEP * 3.0);
    float kf_4 = MAX_TIME * (STEP * 4.0);
    float kf_5 = MAX_TIME * (STEP * 5.0);
    float kf_6 = MAX_TIME * (STEP * 6.0);
    float kf_7 = MAX_TIME * (STEP * 7.0);
    float frame_span = MAX_TIME * STEP;

    // sacrifice performance for convenient editing
    vec4 a = func_rotator(-24.5, +1.5, 2.5);
    vec4 b = func_length_flat();
    vec4 c = func_rotator(-24.5, -1.5, 2.5);
    vec4 d = func_length_flat();

    // vec4 a = func_length_flat();
    // vec4 b = func_rotator(10.15, 2.2, 2.2);
    // vec4 c = func_coslength(22.0, 42.5);
    // vec4 d = func_rotator(-15.75, 1.85, 1.75);
    vec4 e = func_grid();
    vec4 f = func_coslength(8.0, +12.5);
    vec4 g = func_coslength(8.0, -12.5);

    float r;
    vec4 x;
    vec4 y;

    if (t < kf_1)
    {
        x = a;
        y = b;
        r = t / frame_span;
    }
    else if (t < kf_2)
    {
        x = b;
        y = c;
        r = (t - kf_1) / frame_span;
    }
    else if (t < kf_3)
    {
        x = c;
        y = d;
        r = (t - kf_2) / frame_span;
    }
    else if (t < kf_4)
    {
        x = d;
        // y = e;
        y = a;
        r = (t - kf_3) / frame_span;
    }
    else if (t < kf_5)
    {
        x = e;
        y = f;
        r = (t - kf_4) / frame_span;
    }
    else if (t < kf_6)
    {
        x = f;
        y = g;
        r = (t - kf_5) / frame_span;
    }
    else if (t <= kf_7)
    {
        x = g;
        y = a;
        r = (t - kf_6) / frame_span;
    }
    else
    {
        return vec4(0, 0, 0, 0.0);
    }

    vec4 result = mix(x, y, r);
    return clamp(result, 0.0, 1.0);
}

void main()
{
    t = mod(T, MAX_TIME);
    uv = v_uv * 2.0 - 1.0;

    out_color = timeline();
    out_color.w = 1.0;
}
"""

class Renderer(QtWidgets.QOpenGLWidget):
    RECORDING = True

    def __init__(self):
        super(Renderer, self).__init__()

        self.W, self.H = 128, 128
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
        self.out_texture = self.context.texture((self.W, self.H), 4, dtype='f4')
        self.framebuffer = self.context.framebuffer(self.out_texture)

        self.unif_t = program['T']
        self.prev_time = time.time()
        self.elapsed_time = 0.0

        if self.RECORDING:
            self.writer = ii.get_writer("output.mp4", fps=60)

    def paintGL(self):
        t = time.time()
        delta_time = t - self.prev_time
        self.elapsed_time += delta_time
        self.unif_t.value = self.elapsed_time
        self.prev_time = t

        self.vao.render()
        self.update()

        if self.RECORDING:
            self.framebuffer.use()
            self.vao.render()
            data = np.frombuffer(self.out_texture.read(), dtype=np.float32)
            data = data.reshape((self.W, self.H, 4))
            data = data * 255.0
            data = data.astype(np.uint8)
            self.writer.append_data(data)

    def closeEvent(self, e):
        self.hide()

        if self.RECORDING:
            self.writer.close()

def main():
    app = QtWidgets.QApplication([])
    renderer = Renderer()
    renderer.show()
    app.exec()

if __name__ == "__main__":
    main()
