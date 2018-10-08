#version 330

in vec2 in_vert;
in vec2 in_uvcoord;

varying vec2 v_uvcoord;

void main()
{
    v_uvcoord = in_uvcoord;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
