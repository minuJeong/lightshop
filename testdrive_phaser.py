
import time

import numpy as np
import moderngl as mg
import imageio


verts = """
#version 430

in vec3 in_verts;
in vec2 in_uvs;

out vec2 v_uv;

void main()
{
    v_uv = in_uvs;
    gl_Position = vec4(in_verts, 1.0);
}
"""

frags = """
#version 430

#define MAX_TIME 20.0

uniform float frame_idx;
layout(location=0) uniform sampler2D prev_frame;
in vec2 v_uv;
out vec4 out_color;

float t;
vec3 prev;
vec2 cuv;

vec3 phase_1()
{
    return vec3(cuv, 0.12345);
}

vec3 phase_2()
{
    return vec3(cuv, 0.5);
}

vec3 phase_3()
{
    return vec3(cuv, 0.75);
}

vec3 phase_4()
{
    return vec3(cuv, 0.15);
}

vec3 mix_phases(vec3 a, vec3 b, float next_time, float time)
{
    float r = t - time / (next_time - time);
    return mix(a, b, r);
}

vec3 timeline()
{
    float key_0 = 0.0;
    float key_1 = 10.0;
    float key_2 = 20.0;
    float key_3 = 30.0;
    float key_4 = 40.0;

    float r;
    if (t < key_1)
    {
        return mix_phases(
            phase_1(),
            phase_2(),
            key_1, key_0
        );
    }
    else if (t < key_2)
    {
        return mix_phases(
            phase_2(),
            phase_3(),
            key_2, key_1
        );
    }
    else if (t < key_3)
    {
        return mix_phases(
            phase_3(),
            phase_4(),
            key_3, key_2
        );
    }
    else if (t < key_4)
    {
        return mix_phases(
            phase_4(),
            phase_1(),
            key_4, key_3
        );
    }
    else
    {
        return vec3(0, 0, 0);
    }
}

void init()
{
    t = mod(frame_idx, MAX_TIME);
    prev = texture(prev_frame, v_uv).xyz;
    cuv = v_uv * 0.5 + 0.5;
}

void main()
{
    init();
    vec3 res = timeline();
    out_color = vec4(res, 1.0);
}
"""

print("initializing..")
ctx = mg.create_standalone_context()
width, height = 512, 512
program = ctx.program(vertex_shader=verts, fragment_shader=frags)
verts = np.array([
    -1.0, -1.0, 0.0,  0.0, 0.0,
    -1.0, +1.0, 0.0,  0.0, 1.0,
    +1.0, -1.0, 0.0,  1.0, 0.0,
    +1.0, +1.0, 0.0,  1.0, 1.0,
]).astype('f4')
verts_buffer = ctx.buffer(verts.tobytes())

idx = np.array([
    0, 1, 2,
    1, 2, 3
]).astype('i4')
idx_buffer = ctx.buffer(idx.tobytes())

vao = ctx.vertex_array(program, [(
    verts_buffer,
    "3f 2f",
    "in_verts", "in_uvs"
)], idx_buffer)

target_tex = ctx.texture((width, height), 4, dtype='f4')
framebuffer = ctx.framebuffer([target_tex])

print("rendering..")
render_start_time = time.time()

writer = imageio.get_writer("result.mp4", fps=25)
for i in range(2 ** 5):
    if not i % 2 ** 6:
        print(f"\trendering frame idx: {i:4}..")

    program["frame_idx"].value = float(i)

    target_tex.use(0)
    framebuffer.use()
    vao.render()
    frame_result = target_tex.read()

    data = np.frombuffer(frame_result, dtype='f4')
    data = data.reshape((width, height, 4))
    data = data[::-1]
    data = data * 255.0
    data = data.astype(np.uint8)

    writer.append_data(data)

writer.close()
print(f"spent time for rendering: {time.time() - render_start_time:.2f}")
