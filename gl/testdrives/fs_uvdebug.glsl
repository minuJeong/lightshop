#version 430

uniform vec4 u_resolution;
uniform float u_frame;

in vec2 v_uvs;
layout(location=0) out vec4 out_color;

void main()
{
    vec4 glfcxy = clamp(gl_FragCoord.xyzw / u_resolution, 0.0, 1.0);

    float r = u_frame * 0.1;
    float sr = sin(r);
    float cr = cos(r);
    glfcxy = mat4(
        +cr,    -sr,    +0.0,   +0.0,
        +sr,    +cr,    +0.0,   +0.0,
        +0.0,   +0.0,   +1.0,   +0.0,
        -0.5,   -0.5,   +0.0,   +1.0
    ) * glfcxy;

    out_color = vec4(0, 0, v_uvs.x, 1.0) * 0.000001;
    out_color += glfcxy;
}
