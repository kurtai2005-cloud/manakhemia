// Pixel grass tuft / flower-cluster card: nearest, alpha cut, lit as ground (normal up).
// Original shader for 微光小圃 test.
shader_type spatial;
render_mode cull_disabled, diffuse_lambert, specular_disabled;
uniform sampler2D albedo_tex : source_color, filter_nearest;
uniform float shade = 0.9;
uniform float rim_top = 0.0; // golden tips (set from capture.gd)
uniform float rim_amt : hint_range(0.0, 1.0) = 0.0; // 0.3 tried in r4: bushes went lime
// v0.6.18-pilot vc27: night sky × card albedo (coverage = alpha; no root glow, no camera band)
uniform float night_toe_gain = 0.0;
uniform vec3 night_sky_rgb = vec3(0.70, 0.92, 1.00);
uniform float sway = 0.9; // v6.7 wind: wu at the tip (tuft quads are unscaled), synced with clump_card
// v6.9 pet bend (Kurt: grass / bushes / flowers bend away from 團絨 and spring back).
// pet_pos_ws = 遊程's prop_bump.gd feed; pet_lag_ws = spring-damped lag (art_depth.gd).
global uniform vec3 pet_pos_ws;
global uniform vec3 pet_lag_ws;
uniform float push = 7.0;      // wu of bend at the tip (0 = off)
uniform float push_r0 = 8.0;   // full bend inside this XZ radius
uniform float push_r1 = 30.0;  // no bend beyond
vec3 pet_push(vec3 base) {
	vec2 d0 = base.xz - pet_pos_ws.xz;
	vec2 d1 = base.xz - pet_lag_ws.xz;
	float l0 = length(d0);
	float l1 = length(d1);
	float hy = 1.0 - smoothstep(25.0, 50.0, abs(base.y - pet_pos_ws.y + 10.0));
	vec2 p = d0 / max(l0, 0.01) * (1.0 - smoothstep(push_r0, push_r1, l0)) * 0.65
		+ d1 / max(l1, 0.01) * (1.0 - smoothstep(push_r0, push_r1, l1)) * 0.35;
	p *= hy;
	return vec3(p.x, -0.4 * length(p), p.y);
}
// v6.9 one cloud field for the whole scene (project.godot shader_globals, art_depth.gd feeds
// cloud_off): a point p is under the same cloud as the ground point p − SUN·(p.y/SUN.y).
global uniform sampler2D cloud_tex : filter_linear, repeat_enable;
global uniform vec2 cloud_off;
global uniform float cloud_amt;
float cloud_at(vec3 p) {
	vec2 g = p.xz - vec2(-0.645, -0.453) * (p.y / 0.616);
	return texture(cloud_tex, (g - cloud_off) / 560.0).r;
}
varying float cl_k;
float h1(float n) { return fract(sin(n * 12.9898) * 43758.5453); }
float wind(float t, float ph) { return sin(t * 1.15 + ph) * 0.7 + sin(t * 2.7 + ph * 1.9) * 0.3; }

void vertex() {
	float ph = h1(float(INSTANCE_ID) * 0.37 + 9.1) * 6.2832;
	float top = clamp(1.0 - UV.y, 0.0, 1.0);
	VERTEX.x += sway * wind(TIME, ph) * top * top;
	vec3 pb = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	cl_k = 1.0 - cloud_amt * cloud_at(pb);
	if (push > 0.0) {
		VERTEX += inverse(mat3(MODEL_MATRIX)) * (pet_push(pb) * push * top * top);
	}
}

void fragment() {
	vec4 c = texture(albedo_tex, UV);
	ALBEDO = c.rgb * shade * cl_k;
	vec3 em = vec3(1.0, 0.74, 0.36) * rim_top * smoothstep(0.55, 0.05, UV.y) * c.a;
	if (night_toe_gain > 0.0) {
		em += ALBEDO * night_sky_rgb * night_toe_gain * c.a;
	}
	EMISSION = em;
	ALPHA = c.a;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	ROUGHNESS = 1.0;
	RIM = rim_amt;
	RIM_TINT = 0.6;
	NORMAL = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
}
