#version 430

uniform sampler2D source;

in vec2 v_uvcoord;
out vec4 out_color;

void main()
{
    out_color = vec4(v_uvcoord.xy, 0.5, 0.0);
}
