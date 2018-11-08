
import numpy as np
import moderngl as mg
from PyQt5 import QtWidgets
from PyQt5 import QtCore


vertex_shader = '''
#version 430

in vec3 in_vert;
in vec2 in_uv;
out vec2 v_uv;
void main()
{
    gl_Position = vec4(in_vert.xyz, 1.0);
    v_uv = in_uv;
}
'''

fragment_shader = '''
#version 430

#define FAR 80.0
#define MARCHING_MINSTEP 0
#define MARCHING_STEPS 128
#define MARCHING_CLAMP 0.000001
#define NRM_OFS 0.001
#define AO_OFS 0.01
#define PI 3.141592
#define FOG_DIST 2.5
#define FOG_DENSITY 0.32
#define FOG_COLOR vec3(0.35, 0.37, 0.42)

// in vec2 v_uv: screen space coordniate
in vec2 v_uv;

// out color
out vec4 out_color;

// p: sample position
// r: radius
float sphere(vec3 p, float r)
{
    return length(p) - r;
}

float sample_world(vec3 p, inout vec3 c)
{
    float centerSphere = sphere(p, 0.25);

    return centerSphere;
}

// o: origin
// r: ray
// c: color
float raymarch(vec3 o, vec3 r, inout vec3 c)
{
    float t = 0.0;
    vec3 p = vec3(0);
    float d = 0.0;
    for (int i = MARCHING_MINSTEP; i < MARCHING_STEPS; i++)
    {
        p = o + r * t;
        d = sample_world(p, c);
        if (abs(d) < MARCHING_CLAMP)
        {
            return t;
        }
        t += d;
    }
    return FAR;
}

// p: sample surface
vec3 norm(vec3 p)
{
    vec2 o = vec2(NRM_OFS, 0.0);
    vec3 dump_c = vec3(0);
    return normalize(vec3(
        sample_world(p + o.xyy, dump_c) - sample_world(p - o.xyy, dump_c),
        sample_world(p + o.yxy, dump_c) - sample_world(p - o.yxy, dump_c),
        sample_world(p + o.yyx, dump_c) - sample_world(p - o.yyx, dump_c)
    ));
}

void main()
{
    // o: origin
    vec3 o = vec3(0, 1, -6.0);

    // r: ray
    vec3 r = normalize(vec3(v_uv - vec2(0.5, 0.5), 1.001));

    // l: light
    vec3 l = normalize(vec3(-0.5, -0.2, 0.1));

    // c: albedo
    vec3 c = vec3(0.125);
    float d = raymarch(o, r, c);

    // pixel color
    vec3 color = vec3(0);
    if (d < FAR)
    {
        vec3 p = o + r * d;
        vec3 n = norm(p);

        float lambert = dot(n, l);
        lambert = clamp(lambert, 0.0, 1.0);

        #define SPEC_COLOR vec3(0.85, 0.75, 0.5)
        vec3 h = normalize(o + l);
        float ndh = clamp(dot(n, h), 0.0, 1.0);
        float ndv = clamp(dot(n, -o), 0.0, 1.0);
        float spec = pow((ndh + ndv) + 0.01, 64.0) * 0.25;

        color = c * lambert + SPEC_COLOR * spec;
    }

    // add simple fog
    color = mix(FOG_COLOR, color, clamp(pow(FOG_DIST / abs(d), FOG_DENSITY), 0.0, 1.0));

    out_color = vec4(color, 1.0);
}
'''


class Renderer(QtWidgets.QOpenGLWidget):
    vaos = []

    def __init__(self):
        super(Renderer, self).__init__()
        W, H = 500, 500
        self.setMinimumSize(W, H)
        self.setMaximumSize(W, H)
        self.viewport = (0, 0, W, H)

    def initializeGL(self):
        self.context = mg.create_context()
        program = self.context.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)

        vertex_data = np.array([
            # x,    y,   z,    u,   v
            -1.0, -1.0, 0.0,  0.0, 0.0,
            +1.0, -1.0, 0.0,  1.0, 0.0,
            -1.0, +1.0, 0.0,  0.0, 1.0,
            +1.0, +1.0, 0.0,  1.0, 1.0,
        ]).astype(np.float32)
        content = [(
            self.context.buffer(vertex_data.tobytes()),
            '3f 2f',
            'in_vert', 'in_uv'
        )]
        idx_data = np.array([
            0, 1, 2,
            1, 2, 3
        ]).astype(np.int32)
        idx_buffer = self.context.buffer(idx_data.tobytes())
        vao = self.context.vertex_array(program, content, idx_buffer)
        self.vaos.append(vao)

    def paintGL(self):
        self.context.viewport = self.viewport
        for vao in self.vaos:
            vao.render()
        self.update()

app = QtWidgets.QApplication([])
mainwin = QtWidgets.QMainWindow(None, QtCore.Qt.WindowStaysOnTopHint)
renderer = Renderer()
mainwin.setCentralWidget(renderer)
mainwin.show()
app.exec()
