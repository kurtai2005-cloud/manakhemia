// v6.8 colour blade tile; v6.7 r3 near-camera lawn (camera-following; macro covers the whole follow range)
// v6.7 near-camera lawn (original shader text; texel-snapped lighting technique as in
// texel_lit.gdshader). Replaces the 1–2 px/wu ground texels in the bottom of a portrait frame
// with: smooth LINEAR macro colour of the real ground (bake + outer lawn, 2 px/wu, pre-blurred)
// × a fine 4 px/wu blade-detail tile. Lit (receives High live shadows), dithered far-edge fade
// into the regular ground (opaque pass, no blending). 1 draw.
shader_type spatial;
render_mode cull_back, diffuse_lambert, specular_disabled;

uniform sampler2D macro_tex : source_color, filter_linear, repeat_disable;
uniform sampler2D detail_tex : filter_nearest, repeat_enable;
uniform sampler2D blade_tex : source_color, filter_nearest, repeat_enable;   // v6.8 colour blades
uniform vec3 macro_ref = vec3(0.235, 0.29, 0.115);   // v6.8: ≈ blade-tile mean ×1.1 → value follows the real ground
uniform float hue_keep = 0.06;   // v6.13: 0.20 → 0.06 (the olive ground macro browned the blades)                         // how much macro hue survives (vs value only)
uniform float shade_floor = 0.48;   // v6.12: was 0.66 — it clamped object shadows (0.46–0.62) to the tree-shade level                      // v6.8: shade never darker than this × the blade colour
uniform vec4 region = vec4(-340.0, -120.0, 340.0, 330.0);   // x0, z0, x1, z1 (macro extent)
uniform float tile = 64.0;
uniform float fade_len = 24.0;
uniform float near_d = 122.0;   // r3: full detail within this horizontal distance of the camera (any yaw)
uniform float detail_amt = 1.0;
uniform float lawn_gain = 0.0;
// v6.10 r2b: Low without a realtime sun — baked mover shade (fg plants, props), after the floor
uniform sampler2D mover_tex : filter_linear, repeat_disable;   // v6.12: stored as a DISPLAY ratio → decoded with pow 2.2 below (a linear read lost ~half its contrast: 0.50 showed as 0.73)
uniform float mover_amt = 0.0;
uniform vec3 lawn_center = vec3(10.0, 0.0, 30.0);
uniform vec2 lawn_radius = vec2(170.0, 120.0);
uniform vec4 lawn_tint : source_color = vec4(1.0, 0.86, 0.52, 1.0);
uniform vec3 pool_edge = vec3(1.0);   // v6.14 light pooling (edges cooler / darker)
uniform vec2 pool_r = vec2(0.55, 1.25);
uniform vec3 pool_core = vec3(1.0);
uniform vec2 pool_off = vec2(0.0);   // v6.15: pool centre shifted toward 團絨 / cottage (world wu)   // v6.14 lit centre warmer / brighter
uniform vec3 gold_gain = vec3(1.0);   // v6.14 warm golden patches where the sun breaks through the dapple
uniform sampler2D gold_tex : filter_linear, repeat_disable;
uniform float gold_half = 450.0;
uniform float gold_amt = 0.0;
uniform vec3 fg_warm = vec3(1.0);   // v6.16 bottom band warmer (concept warm 68/61/29 bottom)
uniform vec2 fg_warm_d = vec2(90.0, 210.0);
uniform float fg_warm_lit = 0.58;   // v0.6.18: vr window for FG warm (macro stays bright in bake shade — chroma gate below)
uniform float fg_night_toe = 0.0;   // art_depth sets 1 at night: cool readable foreground (POOL_GAIN only tints mid pools)
uniform float night_toe_gain = 0.0;   // vc27: sky × albedo (art_depth; HD2D_NIGHT_TOE)
uniform vec3 night_sky_rgb = vec3(0.70, 0.92, 1.00);
// Same bake GroundInner samples. PlaneMesh UV: world xz [-128,128] → 0..1.
uniform sampler2D ground_tex : source_color, filter_nearest, repeat_disable;
uniform vec3 blade_mean = vec3(0.0544, 0.0841, 0.0150);   // linear mean of lawn_blades_v614.png
uniform float fg_dim = 0.86;    // v6.11: foreground lawn a touch darker (concept: dark-warm bottom, bright mid)
uniform float fg_d0 = 70.0;
uniform float fg_hi_cut = 0.55;
uniform float fg_d1 = 190.0;
varying vec3 v_world;
varying float v_fgk;   // v6.11 fragment → light
uniform float fg_sh_lift = 0.45;   // v6.11 High: near-camera live shadow smudges lifted (lighter, soft)

void vertex() {
	v_world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

float bayer4(vec2 p) {
	ivec2 q = ivec2(mod(p, 4.0));
	int i = q.x + q.y * 4;
	const float m[16] = float[](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
	return (m[i] + 0.5) / 16.0;
}

void fragment() {
	vec2 uv = v_world.xz / tile;
	vec2 tex_sz = vec2(textureSize(detail_tex, 0));
	vec2 uv_c = (floor(uv * tex_sz) + vec2(0.5)) / tex_sz;
	float d = texture(detail_tex, uv_c).r * 2.0;
	vec2 wc = uv_c * tile;  // texel-centre world xz → macro sampled per fine texel (crisp grain)
	vec2 muv = (wc - region.xy) / (region.zw - region.xy);
	vec4 m = texture(macro_tex, muv);
	// v6.8: the blade tile is the lawn's colour; the macro only shades it (bake shadows, lawn
	// lift) — mostly by value, a little by hue — so no blurry brown-yellow mush at the bottom.
	vec3 bl = texture(blade_tex, uv_c).rgb;
	vec3 lw = vec3(0.30, 0.59, 0.11);
	float vr = dot(m.rgb, lw) / dot(macro_ref, lw);
	vec3 ratio = mix(vec3(vr), m.rgb / macro_ref, hue_keep);
	// shade floor: the lawn under the trees stays golden-green (concept), never brown-black mush
	ratio = clamp(ratio, vec3(0.0), vec3(1.6));
	ratio = max(ratio, vec3(shade_floor)) * mix(vec3(1.0), vec3(0.90, 1.03, 0.96), 1.0 - clamp(vr, 0.0, 1.0));   // v6.13: shade cool green-olive (was warm 1.04/1.06/0.92 → brown)
	// v6.11 calmer foreground: compress only the lit-dapple highlights (yellow blotches) near the
	// camera; shadows (per-object hierarchy) are untouched.
	float fgk = 1.0 - smoothstep(fg_d0, fg_d1 + 40.0, distance(v_world.xz, (INV_VIEW_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xz));
	v_fgk = fgk;
	vec3 hi = max(ratio - vec3(0.92), vec3(0.0));
	ratio -= hi * fg_hi_cut * fgk;
	vec3 alb = bl * ratio * mix(1.0, 0.5 + 0.5 * d, detail_amt * 0.18);   // v6.10: 0.35 → 0.24, v6.11: 0.18 (calmer, concept)
	if (lawn_gain > 0.0) {
		vec2 dd = (wc - lawn_center.xz) / lawn_radius;
		float k = (1.0 - smoothstep(0.35, 1.0, length(dd))) * m.a;
		vec3 lifted = mix(alb, alb * lawn_tint.rgb * 1.9, 0.6);
		alb = mix(alb, lifted, k * lawn_gain);
		vec2 pd = (wc - lawn_center.xz - pool_off) / lawn_radius;
		alb *= mix(pool_core, vec3(1.0), smoothstep(0.08, 0.62, length(pd))) * mix(vec3(1.0), pool_edge, smoothstep(pool_r.x, pool_r.y, length(pd)));
	}
	// v6.15: BAKED warm-gold sun patches (canopy gaps + lit tongues between the tree shadows; soft ≈4 wu
	// edges) — tools/sun_gold_v6_15.py from the engine's wide sun bake; replaces the v6.14 sine field
	float gk = texture(gold_tex, (wc + vec2(gold_half)) / (2.0 * gold_half)).r * gold_amt * smoothstep(0.62, 0.95, vr);
	alb *= mix(vec3(1.0), gold_gain, gk);
	// v6.10 (bottom lawn dark / busy vs the concept: blue 5 vs 24, p5 6 vs 16, micro std 23 vs 17):
	// calmer blade contrast around the local colour, lifted toe and a cool sky-fill in the darks.
	float lum = dot(alb, lw);
	alb = mix(vec3(lum) * (bl / max(dot(bl, lw), 1e-3)), alb, 0.70);   // v6.11: 0.80 → 0.70
	// v6.10 r2 (phone-aspect vs concept bottom: concept R>G, B 28, p5 19; ours G≥R, B 17, p5 6):
	// a touch warmer and a warm-neutral toe so the darkest blades read as lit grass, not holes.
	if (mover_amt > 0.0) {
		float mv = mix(1.0, pow(texture(mover_tex, muv).r, 2.2), mover_amt);
		alb *= mv * mix(vec3(1.0), vec3(0.86, 1.00, 0.96), 1.0 - mv);   // v6.13: cool green-olive interior (was blue-violet)
	}
	float shade = 1.0 - smoothstep(0.38, 0.82, vr);
	alb = alb * vec3(0.98, 1.0, 0.96) * 0.94 + vec3(0.0020, 0.0036, 0.0068) * (1.0 + 0.55 * shade);   // v0.6.18: cool shade toe only (no global RGB repaint)
	float fgd = distance(v_world.xz, (INV_VIEW_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xz);
	alb *= mix(fg_dim, 1.0, smoothstep(fg_d0, fg_d1, fgd));
	float fl = dot(alb, lw);
	alb = mix(alb, vec3(fl) * vec3(0.88, 1.0, 0.82), (0.08 + 0.10 * shade) * fgk);
	float yel = max(m.g - m.r * 0.88, 0.0);
	float warm_k = (1.0 - smoothstep(fg_warm_d.x, fg_warm_d.y, fgd))
		* smoothstep(fg_warm_lit, 0.84, vr)
		* (1.0 - smoothstep(0.038, 0.11, yel))
		* smoothstep(0.085, 0.165, m.b);
	alb *= mix(vec3(1.0), fg_warm, warm_k);   // v0.6.18: golden patches stay on gold_tex; skip FG on lush yellow-green macro
	vec3 em = vec3(0.0);
	if (fg_night_toe > 0.0 && night_toe_gain > 0.0) {
		// Inside the 256 bake, use the same base as GroundInner so the camera disk
		// does not cover it with a darker blade composite. Past the bake, keep the
		// wide macro (already continuous through the foreground, z to 330).
		// No coverage hole and no clamped bake-edge texel. Blend the last 8 wu.
		vec2 guv = (v_world.xz + vec2(128.0)) / 256.0;
		bool bake_ok = all(greaterThanEqual(guv, vec2(0.0))) && all(lessThanEqual(guv, vec2(1.0)));
		bool macro_ok = all(greaterThanEqual(muv, vec2(0.0))) && all(lessThanEqual(muv, vec2(1.0)));
		vec2 edge = abs(v_world.xz) - vec2(120.0);
		float bake_w = 1.0 - smoothstep(0.0, 8.0, max(edge.x, edge.y));
		if (bake_ok || macro_ok) {
			vec3 base = macro_ok ? m.rgb : vec3(0.0);
			if (bake_ok && bake_w > 0.0) {
				vec2 gsz = vec2(textureSize(ground_tex, 0));
				vec2 guv_c = (floor(guv * gsz) + vec2(0.5)) / gsz;
				vec3 bake = texture(ground_tex, guv_c).rgb;
				if (lawn_gain > 0.0) {
					vec2 gd = (v_world.xz - lawn_center.xz) / lawn_radius;
					float gk = 1.0 - smoothstep(0.35, 1.0, length(gd));
					vec3 glift = mix(bake, bake * lawn_tint.rgb * 1.9, 0.6);
					bake = mix(bake, glift, gk * lawn_gain);
					vec2 gpd = (v_world.xz - lawn_center.xz - pool_off) / lawn_radius;
					bake *= mix(pool_core, vec3(1.0), smoothstep(0.08, 0.62, length(gpd))) * mix(vec3(1.0), pool_edge, smoothstep(pool_r.x, pool_r.y, length(gpd)));
				}
				base = macro_ok ? mix(m.rgb, bake, bake_w) : bake;
			}
			alb = base * (bl / max(blade_mean, vec3(1e-3)));
		}
		em = alb * night_sky_rgb * night_toe_gain;
	}
	ALBEDO = alb;
	EMISSION = em;
	ROUGHNESS = 1.0;
	METALLIC = 0.0;
	// r3: dithered fade by horizontal distance from the camera (plane follows the camera, so
	// the near band holds for every pet position / yaw) → no seam, no alpha blending
	float dc = length(v_world.xz - CAMERA_POSITION_WORLD.xz);
	float f = clamp((near_d + fade_len - dc) / fade_len, 0.0, 1.0);
	// v6.10 r2: interleaved-gradient noise instead of the 4×4 Bayer (its grid read as a dotted
	// screen on the phone where the near lawn hands over to the ground)
	float ign = fract(52.9829189 * fract(dot(FRAGCOORD.xy, vec2(0.06711056, 0.00583715))));
	if (f < ign) {
		discard;
	}
	vec2 off = uv_c - uv;
	vec2 du = dFdx(uv);
	vec2 dv = dFdy(uv);
	float det = du.x * dv.y - du.y * dv.x;
	if (abs(det) > 1e-8) {
		vec2 s = vec2((dv.y * off.x - dv.x * off.y) / det, (-du.y * off.x + du.x * off.y) / det);
		LIGHT_VERTEX = VERTEX + dFdx(VERTEX) * s.x + dFdy(VERTEX) * s.y;
	}
}

// v6.11 (High bottom foreground: tuft / fg-plant live shadows read as dark DOF-like smudges):
// standard Lambert, but within the foreground band the directional shadow is lifted toward
// light (shape kept, depth ×(1 − 0.45)). Same cost as the default light pass.
void light() {
	float att = ATTENUATION;
	if (LIGHT_IS_DIRECTIONAL) {
		att = mix(att, 1.0, fg_sh_lift * v_fgk * (1.0 - att) * 1.0);
	}
	DIFFUSE_LIGHT += clamp(dot(NORMAL, LIGHT), 0.0, 1.0) * att * LIGHT_COLOR / PI;
}
