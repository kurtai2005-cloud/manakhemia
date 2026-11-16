// v6.7 planted foreground plant (original). Crossed cards rooted in the soil (base buried
// 1.5 wu), lit like the lawn (receives High shadows), alpha-scissor cut (writes depth →
// correct occlusion with 團絨, no sorting), soft contact darkening at the foot, wind sway in
// sync with clump / tuft / ground_dapple.
shader_type spatial;
render_mode cull_disabled, diffuse_lambert, specular_disabled;
uniform sampler2D albedo_tex : source_color, filter_nearest;
uniform float sway = 1.4;
uniform float shade = 0.95;
varying float vh;

float h1(float n) { return fract(sin(n * 12.9898) * 43758.5453); }
float wind(float t, float ph) { return sin(t * 1.15 + ph) * 0.7 + sin(t * 2.7 + ph * 1.9) * 0.3; }

// v6.9 pet bend (Kurt: grass / bushes / flowers bend away from 團絨 and spring back).
// pet_pos_ws = 遊程's prop_bump.gd feed; pet_lag_ws = spring-damped lag (art_depth.gd).
global uniform vec3 pet_pos_ws;
global uniform vec3 pet_lag_ws;
uniform float push = 9.0;      // wu of bend at the tip (0 = off)
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
void vertex() {
	vh = clamp(1.0 - UV.y, 0.0, 1.0);
	vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float ph = dot(wp.xz, vec2(0.031, 0.027)) + COLOR.r * 6.2832;
	VERTEX.x += sway * wind(TIME, ph) * vh * vh;
	VERTEX.z += sway * 0.5 * wind(TIME * 1.2, ph + 2.0) * vh * vh;
	vec3 pb = vec3(wp.x, 0.0, wp.z);   // merged mesh: per-vertex foot (plants are small)
	if (push > 0.0) {
		VERTEX += inverse(mat3(MODEL_MATRIX)) * (pet_push(pb) * push * vh * vh);
	}
}

void fragment() {
	vec4 c = texture(albedo_tex, UV);
	if (c.a < 0.5) {
		discard;
	}
	float foot = smoothstep(0.0, 0.22, vh);
	ALBEDO = c.rgb * shade * (0.45 + 0.55 * foot);
	ROUGHNESS = 1.0;
	NORMAL = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
}
