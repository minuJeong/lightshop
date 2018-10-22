#version 430

uniform sampler2D source;

in vec2 v_uvcoord;
out vec4 out_color;

void main()
{
    #define OFFSET vec2(0.0, 0.002)
    vec4 tex_color_00 = texture(source, v_uvcoord.xy + OFFSET.xy);
    vec4 tex_color_01 = texture(source, v_uvcoord.xy + OFFSET.yx);
    vec4 tex_color_10 = texture(source, v_uvcoord.xy + OFFSET.xy);
    vec4 tex_color_11 = texture(source, v_uvcoord.xy + OFFSET.yx);

    vec4 color = tex_color_00 + tex_color_01 + tex_color_10 + tex_color_11;
    color *= 0.25;
    out_color = vec4(color.xyz, 1.0);
}
