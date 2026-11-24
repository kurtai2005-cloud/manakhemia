// v6.10 團絨 projected shadow for Low (original). Low drops the live sun-shadow pass (phone
// 47→60 fps target) — but every object must still cast, and the pet's shadow must move with it
// and follow the light. The pet sprite's own alpha is projected along the real sun vector
// (travel (0.645,-0.616,0.453), 38°) onto a sheared ground quad, so the shadow keeps its true
// silhouette (ears, body) and length. Contact-hardening: crisp and deep at the feet, wider and
// lighter toward the far end; a passing cloud (shared field) softens it. 1 draw, no shadow map.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
uniform sampler2D pet_tex : filter_linear, repeat_disable;
uniform vec3 shade_col : source_color = vec3(0.10, 0.11, 0.19);
uniform float opacity = 0.58;
uniform float foot_v = 0.97;      // texture row of the feet (0 top … 1 bottom)
global uniform sampler2D cloud_tex : filter_linear, repeat_enable;
global uniform vec2 cloud_off;
global uniform float cloud_amt;
varying vec3 wp;

void vertex() { wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }

void fragment() {
	float far = clamp((foot_v - UV.y) / foot_v, 0.0, 1.0);     // 0 at the feet → 1 at the head's shadow
	float r = mix(0.6, 4.0, far) / 64.0;
	float a = texture(pet_tex, UV).a * 0.2;
	for (int i = 0; i < 8; i++) {
		float an = float(i) * 0.785398;
		a += texture(pet_tex, UV + vec2(cos(an), sin(an)) * r).a * 0.1;
	}
	float below = smoothstep(foot_v + 0.03, foot_v - 0.01, UV.y);   // nothing in front of the feet
	vec2 g = wp.xz;
	float cl = texture(cloud_tex, (g - cloud_off) / 560.0).r * (cloud_amt > 0.0 ? 1.0 : 0.0);
	float al = opacity * a * mix(1.0, 0.55, far) * below * (1.0 - 0.55 * cl);
	if (al < 0.004) { discard; }
	ALBEDO = shade_col;
	ALPHA = al;
}
