// v6.7 foliage clump card (original): CPU-oriented camera-facing quad, atlas cell picked per
// instance (COLOR.a < 1 → explicit cell (a·cells² − 0.5), else hashed from INSTANCE_ID), one
// MultiMesh = one draw per layer, alpha-scissor, light baked per instance in COLOR.rgb, scene
// light level via light_mul (night ≈ 0.3 blue). Unshaded → identical in Low / High.
// v6.7: gentle wind sway (top of the card moves, phase per instance) — same wind() as
// tuft / near_lawn / ground_dapple so leaves and the moving leaf-light stay in sync.
shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled;
uniform sampler2D atlas : source_color, filter_nearest;
uniform float cells = 2.0;
uniform vec3 light_mul = vec3(1.0);
uniform vec4 haze : source_color = vec4(0.93, 0.80, 0.56, 1.0);
uniform float haze_amt : hint_range(0.0, 1.0) = 0.0;
uniform float sway = 0.0;     // fraction of card width at the top edge
varying vec3 tint;
// v6.11 aerial haze by camera distance (concept: the far garden / forest melts into gold haze).
// Per vertex (one varying), no new pass. Near / mid garden untouched (< aer_d0).
uniform vec3 aer_col : source_color = vec3(0.95, 0.80, 0.52);
uniform float aer_amt = 0.30;   // v6.12: 0.52 → 0.40 (upper mid read too hazy-bright vs concept)
uniform float aer_d0 = 330.0;
uniform float aer_d1 = 760.0;
varying float aer_k;

float h1(float n) { return fract(sin(n * 12.9898) * 43758.5453); }
float wind(float t, float ph) { return sin(t * 1.15 + ph) * 0.7 + sin(t * 2.7 + ph * 1.9) * 0.3; }

// v6.9 pet bend (Kurt: grass / bushes / flowers bend away from 團絨 and spring back).
// pet_pos_ws = 遊程's prop_bump.gd feed; pet_lag_ws = spring-damped lag (art_depth.gd).
global uniform vec3 pet_pos_ws;
global uniform vec3 pet_lag_ws;
uniform float push = 0.0;      // wu of bend at the tip (0 = off)
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
uniform float foot_y = -1.0;   // v6.9 bake tool: >0 → white footprint below this height
varying float wy_v;
uniform float cloud_recv = 1.0;
// v6.13 (Kurt: lower mid — lift the hedge / bed strip itself, warmer): warm sunlit lift for the
// leaf clumps around the clearing (elliptical zone on xz), stronger on the upper part of each card.
uniform vec4 warm_zone = vec4(5.0, -40.0, 190.0, 135.0);   // centre x, z, radius x, z
uniform vec3 warm_gain = vec3(1.0);                      // set by art_depth.gd (day only)
// v6.14 hedge diagnosis: on Mobile the gain is a LINEAR multiply before Filmic → a ×1.62 gain reads only
// ≈ ×1.25 on screen, and a multiply on a dark saturated green stays green (PC 52/79/16 → 67/93/15).
// The box (gl_compatibility) showed ≈ twice the lift. Fix: a warm sunlit ADD (gold, scaled by the
// card's own value so the gaps stay dark) on top of the gain → the strip reads warm on Mobile.
uniform vec3 warm_add = vec3(0.0);
varying float wz_k;
void vertex() {
	float id = float(INSTANCE_ID);
	float cell = floor(h1(id + 0.5) * cells * cells);
	if (COLOR.a < 0.995) {
		cell = floor(COLOR.a * cells * cells);
	}
	vec2 off = vec2(mod(cell, cells), floor(cell / cells)) / cells;
	vec2 uv = UV;
	if (h1(id * 1.7 + 3.1) > 0.5) uv.x = 1.0 - uv.x;
	UV = off + uv / cells;
	tint = COLOR.rgb * 1.6;
	float ph = h1(id * 0.37 + 9.1) * 6.2832;
	float top = 1.0 - uv.y;     // 0 at the bottom edge, 1 at the top
	VERTEX.x += sway * wind(TIME, ph) * top;
	VERTEX.y += sway * 0.25 * wind(TIME * 1.3, ph + 1.7) * top;
	vec3 pb = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	cl_k = 1.0 - cloud_amt * cloud_recv * cloud_at(pb);
	wy_v = (MODEL_MATRIX * vec4(VERTEX, 1.0)).y;
	aer_k = aer_amt * smoothstep(aer_d0, aer_d1, length(pb - CAMERA_POSITION_WORLD));
	vec2 zd = (pb.xz - warm_zone.xy) / warm_zone.zw;
	wz_k = (1.0 - smoothstep(0.6, 1.0, length(zd))) * (0.55 + 0.45 * top) * step(pb.y, 90.0);
	if (push > 0.0) {
		VERTEX += inverse(mat3(MODEL_MATRIX)) * (pet_push(pb) * push * top);
	}
}

void fragment() {
	vec4 c = texture(atlas, UV);
	if (c.a < 0.5) discard;
	if (foot_y > 0.0) {
		if (wy_v > foot_y) discard;
		ALBEDO = vec3(0.0);
		EMISSION = vec3(1.0);
	} else {
		vec3 col = c.rgb * tint * light_mul * cl_k * mix(vec3(1.0), warm_gain, wz_k);
		col += warm_add * light_mul * wz_k * smoothstep(0.005, 0.06, dot(col, vec3(0.30, 0.59, 0.11)));
		ALBEDO = mix(mix(col, haze.rgb * light_mul, haze_amt), aer_col * light_mul, aer_k);
	}
}
