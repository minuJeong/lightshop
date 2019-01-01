
#version 430

#define X %X
#define Y %Y
#define Z %Z
#define WIDTH %WIDTH
#define HEIGHT %HEIGHT

layout (local_size_x=X, local_size_y=Y, local_size_z=Z) in;
layout (std430, binding=0) buffer in_0
{
    vec4 inxs[1];
};

layout (std430, binding=1) buffer out_0
{
    vec4 outxs[1];
};

vec3 rotate(vec3 p, vec3 r)
{
    vec3 c = cos(r);
    vec3 s = sin(r);
    mat3 rx = mat3(
        1, 0, 0, b
        0, c.x, -s.x,
        0, s.x, c.s
    );
    mat3 ry = mat3(
        c.y, 0, s.y,
        0, 1, 0,
        -s.y, 0, c.y
    );
    mat3 rz = mat3(
        c.z, -s.z, 0,
        s.z, c.z, 0,
        0, 0, 1
    );
    return rz * ry * rx * p;
}

float blend(float a, float b, float k)
{
    float h = clamp(0.5 + 0.5 * (a - b) / k, 0.0, 1.0);
    return mix(a, b, h) - k * h * (1.0 - h);
}

float box(vec3 p, vec3 b)
{
    return length(max(abs(p) - b, 0.0));
}

float sphere(vec3 cursor, float r)
{
    return length(cursor) - r;
}

float sample_world(vec3 cursor)
{
    float ds = sphere(cursor - vec3(0.5, 0.0, -0.6), 0.75);
    float db = box(cursor - vec3(-0.5, 0.0, 0.0), vec3(0.35));

    float dblend = blend(ds, db, 0.5);

    return dblend;
}

float raymarch(vec3 origin, vec3 ray)
{
    float travel = 0.0;
    vec3 cursor = vec3(0.0);
    float distance = 0.0;
    for (int i = 0; i < 128; i++)
    {
        cursor = origin + ray * travel;
        distance = sample_world(cursor);
        if (abs(distance) < 0.002)
        {
            return travel;
        }

        travel += distance;
    }

    return 50.0;
}

vec3 get_normal(vec3 p)
{
    vec2 o = vec2(0.001, 0.0);
    return normalize(vec3(
        sample_world(p + o.xyy) - sample_world(p - o.xyy),
        sample_world(p + o.yxy) - sample_world(p - o.yxy),
        sample_world(p + o.yyx) - sample_world(p - o.yyx)
    ));
}

void main()
{
    int i = int(gl_LocalInvocationID.x);
    int j = int(gl_WorkGroupID.x);
    int idx = i + j * WIDTH;

    vec2 uv = vec2(float(i) / float(WIDTH), float(j) / float(HEIGHT));
    
    vec3 origin = vec3(0, 0, -5.0);
    vec3 ray = normalize(vec3(uv - vec2(0.5, 0.5), 1.0001));
    vec3 light = vec3(-3.0, 3.0, 1.0);

    vec3 rgb = vec3(0.0);

    float distance = raymarch(origin, ray);
    if (distance < 50.0)
    {
        light = normalize(light);
        vec3 normal = get_normal(origin + ray * distance);

        vec3 view = -origin;
        vec3 half_vl = normalize(view + light);

        float ndh = dot(normal, -half_vl);

        float diffuse = dot(-light, normal);
        float spec = pow(ndh, 128.0);
        spec = clamp(spec, 0.0, 1.0);

        rgb = vec3(diffuse + spec);
    }

    outxs[idx] = vec4(clamp(rgb, 0.0, 1.0), 1.0);
}
