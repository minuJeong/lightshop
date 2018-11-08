
'''
calculate ball bouncing with compute shader

author: minu jeong
'''

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
    c.xy += v_uv.xy * 0.00001;
    c.xy += v_pos.xy * 0.00001;
    out_color = vec4(c, 1.0);
}
"""

simple_bg_fragment_shader_code = """
#version 430

in vec3 v_col;
out vec4 out_color;
void main()
{
    vec3 c = v_col;
    out_color = vec4(c, 1.0);
}
"""

# calc position with compute shader
compute_advance_worker_shader_code = """
#version 430
#define GROUP_SIZE %COMPUTE_SIZE%
#define ADVANT_SIZE %ADVANT_SIZE%

#define WALL_ELASTICITY 0.3
#define GRAVITY 0.02
#define AIR_FRICTION 0.88

layout(local_size_x=GROUP_SIZE) in;

struct Ball
{
    vec4 pos;
    vec4 vel;
    vec4 col;
};

layout(std430, binding=0) buffer balls_in
{
    Ball balls[];
} In;
layout(std430, binding=1) buffer balls_out
{
    Ball balls[];
} Out;

void main()
{
    int x = int(gl_GlobalInvocationID);

    Ball in_ball = In.balls[x];
    vec4 p = in_ball.pos.xyzw;
    vec4 v = in_ball.vel.xyzw;
    vec4 c = in_ball.col.xyzw;

    v.y += -GRAVITY;

    float rad = p.w * 0.5;
    float scale_v = length(v);

    if (p.x + v.x - rad <= -1.0)
    {
        p.x = -1.0 + rad;
        v.x *= -WALL_ELASTICITY;
    }
    else if (p.x + v.x + rad >= 1.0)
    {
        p.x = 1.0 - rad;
        v.x *= -WALL_ELASTICITY;
    }

    if (p.y + v.y - rad <= -1.0)
    {
        p.y = -1.0 + rad;
        v.y *= -WALL_ELASTICITY;
    }
    else if (p.y + v.y + rad >= 1.0)
    {
        p.y = 1.0 - rad;
        v.y *= -WALL_ELASTICITY;
    }

    p.xy += v.xy;
    v *= AIR_FRICTION;

    for (int y = x; y < GROUP_SIZE; y++)
    {
        if (x == y) { continue; }

        Ball ob = In.balls[y];
        vec4 op = ob.pos.xyzw;

        vec2 d = op.xy - p.xy;
        float sr = op.w * 0.5 + rad;
        if (d.x * d.x + d.y * d.y < sr * sr)
        {
            float a = d.x != 0.0 ? atan(d.y, d.x) : 3.1415;
            vec2 unit_revert = vec2(cos(a), sin(a));
            p.xy = op.xy - unit_revert * sr;
            v.xy = unit_revert * scale_v * -0.25;
        }
    }

    Ball out_ball;
    out_ball.pos = p;
    out_ball.vel = v;
    out_ball.col = c;

    Out.balls[x] = out_ball;
}
"""


class ComputeToggleTimer(QtCore.QThread):
    compute_update_signal = QtCore.pyqtSignal(float)

    def __init__(self, compute_complete_signal):
        super(ComputeToggleTimer, self).__init__()
        self.compute_complete_flag = False
        compute_complete_signal.connect(self.compute_complete)

    def compute_complete(self):
        self.compute_complete_flag = False

    def run(self):
        while True:
            previous_frame = time.time()
            while self.compute_complete_flag:
                self.msleep(1)
            delta_time = time.time() - previous_frame
            self.compute_update_signal.emit(delta_time)
            self.compute_complete_flag = True


class Renderer(QtWidgets.QOpenGLWidget):
    COUNT = 500
    STRUCT_SIZE = 12
    ADVANT_SIZE = 1

    worker_thread = None
    advant_toggle_uniform = None

    compute_complete_signal = QtCore.pyqtSignal()

    def __init__(self, framerate_label):
        super(Renderer, self).__init__()
        W, H = 512, 512
        self.setMinimumSize(W, H)
        self.setMaximumSize(W, H)
        self.viewport = (0, 0, W, H)
        self.toggle = False
        self.framerate_label = framerate_label
        self.vaos = []

    def initializeGL(self):
        self.context = mg.create_context()
        self.program = self.context.program(
            vertex_shader=simple_vertex_shader_code,
            fragment_shader=simple_fragment_shader_code)

        self.bg_program = self.context.program(
            vertex_shader=simple_vertex_shader_code,
            fragment_shader=simple_bg_fragment_shader_code)

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

        compute_shader_advance_code_parsed = compute_advance_worker_shader_code \
            .replace("%COMPUTE_SIZE%", str(Renderer.COUNT)) \
            .replace("%ADVANT_SIZE%", str(Renderer.ADVANT_SIZE))
        self.compute_shader_advance = self.context.compute_shader(compute_shader_advance_code_parsed)

        compute_data = []
        for i in range(Renderer.COUNT):
            _angle = (i / Renderer.COUNT) * math.pi * 2.0
            _dist = 0.125
            radius = random.random() * 0.04 + 0.02
            x = math.cos(_angle) * _dist
            y = math.sin(_angle) * _dist
            z = 0.0
            w = radius
            _v = random.random() * 0.05 + 0.05
            vx = math.cos(_angle) * _v
            vy = math.sin(_angle) * _v
            vz = 0.0
            vw = 0.0
            r = 1.0 * random.random()
            g = 1.0 * random.random()
            b = 1.0 * random.random()
            a = 1.0

            # match bytes
            compute_data.append(
                [x, y, z, w,  vx, vy, vz, vw,  r, g, b, a])

        compute_data = np.array(compute_data).astype('f4')
        compute_data_bytes = compute_data.tobytes()

        self.compute_buffer_a = self.context.buffer(compute_data_bytes)
        self.compute_buffer_b = self.context.buffer(compute_data_bytes)
        self.target_buffer = self.compute_buffer_b

        bg_quad = self.vbo_data.copy()[:, [0, 1, 4, 5, 6]]
        bg_quad[:, [2, 3, 4]] = (0.5, 0.1, 0.25)
        self.background_quad = self.context.vertex_array(
            self.bg_program,
            [(
                self.context.buffer(bg_quad.tobytes()),
                '2f 3f',
                'in_vert', 'in_col'
            )],
            self.index_buffer)

        self.timer_thread = ComputeToggleTimer(self.compute_complete_signal)
        self.timer_thread.compute_update_signal.connect(self.update_computeworker)
        self.timer_thread.start()

        self.debug_texture = self.context.texture((512, 512), 3, dtype='f4')
        self.framebuffer = self.context.framebuffer(self.debug_texture)

        self.idx = 0
        self.recording = []

    def update_computeworker(self, delta_time):
        if self.toggle:
            self.compute_buffer_a.bind_to_storage_buffer(0)
            self.compute_buffer_b.bind_to_storage_buffer(1)
            target_buffer = self.compute_buffer_b
        else:
            self.compute_buffer_a.bind_to_storage_buffer(1)
            self.compute_buffer_b.bind_to_storage_buffer(0)
            target_buffer = self.compute_buffer_a
        self.toggle = not self.toggle
        self.compute_shader_advance.run(group_x=Renderer.STRUCT_SIZE)
        self.target_buffer = target_buffer

        # display framerate
        if delta_time:
            self.framerate_label.setText(f"Framerate: {1.0 / delta_time:.2f}")

        self.compute_complete_signal.emit()

    def generate_quads(self, buffer):
        """
        generate quads using CPU ALU
        use intel MKL with numpy to speed this up

        TODO: consider to move this to be populated from compute shader
        """

        def gen_quad(rad, pos, color):
            quad = self.vbo_data.copy()
            quad[:, [0, 1]] *= rad
            quad[:, [0, 1, 4, 5, 6]] += pos + color
            return quad

        self.vaos = []
        data = np.frombuffer(buffer.read(), dtype='f4')
        data = data.reshape((Renderer.COUNT, Renderer.STRUCT_SIZE))
        for item in data:
            quad = gen_quad(item[3], (item[0], item[1]), (item[8], item[9], item[10]))

            # generate vertex buffer object to render
            item_vertex_buffer = self.context.buffer(quad.tobytes())
            bo = [(
                item_vertex_buffer,
                '2f 2f 3f',
                'in_vert', 'in_uv', 'in_col'
            )]

            # generate vertex array object
            yield self.context.vertex_array(
                self.program, bo, self.index_buffer)

    def paintGL(self):
        self.context.viewport = self.viewport
        self.background_quad.render()
        for quad in self.generate_quads(self.target_buffer):
            quad.render()
        self.update()

        if self.idx > 50:
            if self.recording:
                import imageio
                imageio.mimwrite("compute_shader_demo.gif", self.recording)
                self.recording = []
                print("recording finished")
            return
        print(f"capturing frame: {self.idx} / 50..")
        self.idx += 1

        self.framebuffer.use()
        self.background_quad.render()
        for quad in self.generate_quads(self.target_buffer):
            quad.render()

        debug_data = np.frombuffer(
            self.debug_texture.read(), dtype=np.float32)
        debug_data = debug_data.reshape((512, 512, 3))
        debug_data = debug_data[::-1,]
        debug_data = debug_data * 255.0
        debug_data = debug_data.astype(np.uint8)
        self.recording.append(debug_data)


def main():
    app = QtWidgets.QApplication([])
    mainwin = QtWidgets.QMainWindow(None, QtCore.Qt.WindowStaysOnTopHint)
    root = QtWidgets.QFrame()
    root_ly = QtWidgets.QVBoxLayout()
    framerate_label = QtWidgets.QLabel()
    root_ly.addWidget(framerate_label)
    renderer = Renderer(framerate_label)
    root_ly.addWidget(renderer)
    root.setLayout(root_ly)
    mainwin.setCentralWidget(root)
    mainwin.show()
    app.exec()

if __name__ == "__main__":
    main()
