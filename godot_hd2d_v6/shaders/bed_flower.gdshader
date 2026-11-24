// Flower-bed seedling cards (bed.glb): wood frame / soil stay still, cards above
// stem_y bend away from 團絨 and spring back. pet_push() matches shaders/tuft.gdshader.
shader_type spatial;
render_mode cull_disabled, diffuse_lambert, specular_disabled;
uniform sampler2D albedo_tex : source_color, filter_nearest;
uniform float shade = 1.0;
uniform float stem_y = 6.0;  // local Y of the soil / frame top; cards go up to ~29
uniform float push = 7.0;
uniform float push_r0 = 8.0;
uniform float push_r1 = 30.0;
global uniform vec3 pet_pos_ws;
global uniform vec3 pet_lag_ws;
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
// v6.13 Low (no live sun shadow): baked shade ON the bed (pickets / lamp / cottage / trees), from a
// receiver plane at the soil top (tools/bedtop_shade_v6_13.py). Cards fade out of it with height.
uniform sampler2D bedtop_tex : filter_linear, repeat_disable;
uniform float bedtop_amt = 0.0;
varying vec3 v_w;
varying float v_ly;
varying float v_up;
uniform float idle_sway = 0.9;   // v6.11: idle breeze (wu at the flower head), same wind() as tufts / leaves
float wind(float t, float ph) { return sin(t * 1.15 + ph) * 0.7 + sin(t * 2.7 + ph * 1.9) * 0.3; }
// v6.14 (Kurt: picket shadows hidden by the bed plants): the back-row cards (local −z, toward the
// fence) are trimmed so the picket shade on the soil reads; front rows untouched.
uniform float back_trim = 0.62;
uniform float back_z = -1.0;
void vertex() {
	if (VERTEX.y > stem_y) {
		float bk = smoothstep(back_z, back_z - 4.0, VERTEX.z);
		VERTEX.y = stem_y + (VERTEX.y - stem_y) * mix(1.0, back_trim, bk);
	}
	v_ly = VERTEX.y;
	v_up = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz).y;
	float top = smoothstep(stem_y, stem_y + 18.0, VERTEX.y);
	if (idle_sway > 0.0 && top > 0.0) {
		vec3 wf = (MODEL_MATRIX * vec4(VERTEX.x, 0.0, VERTEX.z, 1.0)).xyz;
		float ph = wf.x * 0.13 + wf.z * 0.07;
		VERTEX += inverse(mat3(MODEL_MATRIX)) * (vec3(wind(TIME, ph), 0.0, 0.35 * wind(TIME * 1.3, ph + 1.7)) * idle_sway * top * top);
	}
	if (push > 0.0 && top > 0.0) {
		// Per-stem foot so a long bed only bends the flowers near 團絨.
		vec3 foot = (MODEL_MATRIX * vec4(VERTEX.x, 0.0, VERTEX.z, 1.0)).xyz;
		VERTEX += inverse(mat3(MODEL_MATRIX)) * (pet_push(foot) * push * top * top);
	}
	v_w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}
void fragment() {
	vec4 c = texture(albedo_tex, UV);
	ALBEDO = c.rgb * shade;
	if (bedtop_amt > 0.0) {
		float b = pow(texture(bedtop_tex, (v_w.xz + 128.0) / 256.0).r, 2.2);   // display ratio → linear
		float card = smoothstep(stem_y + 0.5, stem_y + 2.0, v_ly);
		float wgt = mix(smoothstep(0.45, 0.85, v_up), 0.55 * (1.0 - smoothstep(stem_y, stem_y + 16.0, v_ly)), card);   // soil / frame TOP only; cards fade with height
		b = mix(1.0, b, bedtop_amt * wgt);
		ALBEDO *= b * mix(vec3(1.0), vec3(0.90, 0.97, 1.04), 1.0 - b);
	}
	ALPHA = c.a;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	ROUGHNESS = 1.0;
}
