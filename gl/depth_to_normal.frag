#version 330

uniform sampler2D source;

varying vec2 v_uvcoord;
out vec4 out_color;

void main()
{
    vec4 tex_rgba = texture(source, v_uvcoord);
    out_color = vec4(tex_rgba.xyz, 0.0);
}
