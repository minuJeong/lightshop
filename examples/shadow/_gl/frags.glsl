
#version 430

#define PI 3.141592653589793

#define NEAR 0.05
#define FAR 1000.0
#define SURFACE 0.00012
#define STEP 128.0

uniform float u_time;


in vec2 v_uvs;

out vec4 out_color;
out vec2 out_uv;
out float out_time;


float sphere(vec3 p, float radius)
{
    return length(p) - radius;
}

float world(vec3 p, inout vec3 base_color)
{
    float _rad = 1.5;

    float floor = abs(-_rad - p.y);
    if (floor < SURFACE)
    {
        base_color = vec3(0.15, 0.45, 0.15);
        return floor;
    }

    float ds = sphere(p, _rad);
    if (ds < SURFACE)
    {
        base_color = vec3(0.5, 0.0, 0.0);
        return ds;
    }

    float d = min(floor, ds);
    return d;
}

float raymarch(vec3 o, vec3 r, inout vec3 base_color)
{
    float travel = NEAR;
    vec3 p = vec3(0.0);

    float d;
    for (float i = 0.0; i < 512.0; i++)
    {
        p = o + r * travel;
        d = world(p, base_color);
        travel += d;
        if (d < SURFACE)
        {
            return travel;
        }
    }

    return FAR;
}

vec3 normal(vec3 p)
{
    vec2 e = vec2(SURFACE, 0.0);
    vec3 _c;
    return normalize(vec3(
        world(p + e.xyy, _c) - world(p - e.xyy, _c),
        world(p + e.yxy, _c) - world(p - e.yxy, _c),
        world(p + e.yyx, _c) - world(p - e.yyx, _c)
    ));
}

float ggx(vec3 vct_dots, float rough, float min_fresnel)
{
    float NdL = vct_dots.x;
    float LdH = vct_dots.y;
    float NdH = vct_dots.z;

    float a = pow(rough, 4.0);
    float denom = 1.0 + NdH * NdH * (a - 1.0);

    float rrh2 = pow(rough * rough * 0.5, 2.0);

    float distribution = a / (PI * denom * denom);
    float fresnel = 0.7 + 0.3 * pow(1.0 - LdH, 5.0);

    float rcp_rrh2 = 1.0 / (1.0 - rrh2) + rrh2;
    float _ggx = distribution * NdL * fresnel * rcp_rrh2;
    return _ggx;
}

float soft_shadow(vec3 o, vec3 r)
{
    float k = 2.4;

    float t = 0.02;
    float res = 1.0;
    float ph = 1e20;

    vec3 _c;
    for (float i = 0.0; i < 128.0; i++)
    {
        float h = world(o + r * t, _c);
        if (h < SURFACE)
        {
            return 0.0;
        }

        float y = h * h / (2.0 * ph);
        float d = sqrt(h * h - y * y);
        res = min(res, k * d / max(0.0, t - y));
        ph = h;
        t += h;
    }
    return res;
}

vec3 aces_film_tonemap(vec3 hdr)
{
    float a = 2.51;
    float b = 0.03;
    float c = 2.43;
    float d = 0.59;

    float e = 0.14;

    vec3 x = hdr * (a * hdr + b);
    vec3 y = hdr * (c * hdr + d) + e;

    return clamp(x / y, 0.0, 1.0);
}

void main()
{
    vec3 light = vec3(0.0, 20.0, 0.0);
    light.x = cos(u_time * 1.5) * 40.0;
    light.y = cos(u_time * 8.0) * 20.0 + 25.0;
    light.z = sin(u_time * 1.5) * 40.0;

    vec3 L = normalize(light);

    vec2 uv = v_uvs - 0.5;
    vec3 o = vec3(0.0, 0.75, -10.0);
    vec3 r = vec3(uv, 1.0);
    r.y -= 0.1;
    r = normalize(r);

    vec3 base_color = vec3(0.2, 0.3, 0.6);
    float d = raymarch(o, r, base_color);

    vec3 hdr = base_color;
    if (d < FAR)
    {
        vec3 P = o + r * d;
        vec3 N = normal(P);
        vec3 V = normalize(-o);
        vec3 H = normalize(L - V);

        float LdH = max(0.0, dot(L, H));
        float NdH = max(0.0, dot(N, H));
        float NdL = max(0.0, dot(N, L));
        float F = max(0.0, dot(N, V));

        float spec = ggx(vec3(LdH, NdH, NdL), 0.2, 0.7);
        hdr = vec3(spec) + base_color;

        vec3 shadow_lp = normalize(light - P);
        float d_shadow = soft_shadow(P, shadow_lp);

        float shadow_intensity = 0.85;
        hdr *= mix(1.0, d_shadow, shadow_intensity);
    }

    vec3 ldr = aces_film_tonemap(hdr);

    out_color.xyz = ldr;
    out_color.w = 1.0;

    out_uv = v_uvs;
    out_time = u_time;
}
