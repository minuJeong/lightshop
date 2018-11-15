#version 430

uniform mat4 u_projection;
uniform mat4 u_view;
uniform mat4 u_model;

in vec2 in_verts;
in vec2 in_uvs;

out vec2 v_uvs;

void main()
{
    v_uvs = in_uvs;
    mat4 mvp = u_projection * u_view * u_model;
    gl_Position = mvp * vec4(in_verts, 0.0, 1.0);
}
