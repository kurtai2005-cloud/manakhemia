// Texel-snapped lighting for pixel textures.
// Technique (not copied from a specific repo): snap light evaluation to the
// centre of the current texel using screen-space derivatives, as used in
// t3ssel8r-style pixel 3D and described for Godot by Jettelly / David Holland.
// Written for 微光小圃. MIT-licensed technique, our own shader text.
shader_type spatial;
render_mode cull_back, diffuse_lambert, specular_disabled;

uniform sampler2D albedo_tex : source_color, filter_nearest, repeat_enable;
uniform vec2 uv_scale = vec2(1.0, 1.0);
uniform float roughness_val : hint_range(0.0, 1.0) = 1.0;
uniform float alpha_cut : hint_range(0.0, 1.0) = 0.0;
uniform bool flip_v = false;
uniform sampler2D normal_tex : hint_normal, filter_nearest, repeat_enable;
uniform bool use_normal = false;
uniform float normal_depth = 1.0;
uniform float lawn_gain = 0.0;          // v6: sunlit-lawn albedo lift (0 = off)
uniform vec3 lawn_center = vec3(10.0, 0.0, 30.0);
uniform vec2 lawn_radius = vec2(170.0, 120.0);
uniform vec4 lawn_tint : source_color = vec4(1.0, 0.86, 0.52, 1.0);
uniform vec3 pool_edge = vec3(1.0);   // v6.14 light pooling: clearing edges / tree shade cooler + darker (concept vignette toward 團絨 + cottage)
uniform vec2 pool_r = vec2(0.55, 1.25);
uniform vec3 pool_core = vec3(1.0);
uniform vec2 pool_off = vec2(0.0);   // v6.15: pool centre shifted toward 團絨 / cottage (world wu)
// v6.15 baked warm-gold sun patches (tools/sun_gold_v6_15.py, from the engine's wide sun bake; ground only)
uniform sampler2D gold_tex : filter_linear, repeat_disable;
uniform float gold_half = 450.0;
uniform float gold_amt = 0.0;
uniform vec3 gold_gain = vec3(1.0);   // v6.14 lit centre warmer / brighter
varying vec3 v_world;

void vertex() {
	v_world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}
uniform vec4 haze : source_color = vec4(1.0, 0.86, 0.62, 1.0);
uniform float haze_amt : hint_range(0.0, 1.0) = 0.0;

uniform float rim_amt : hint_range(0.0, 1.0) = 0.0; // 0.3 tried in r4: bushes went lime
// v0.6.18-pilot vc27: night sky ≈ irradiance × albedo (no constant RGB floor, no camera band)
uniform float night_toe_gain = 0.0;
uniform vec3 night_sky_rgb = vec3(0.70, 0.92, 1.00);
// vc27: past the 256 bake, night radiance follows near_macro (the wide ground already
// bound for the near lawn) instead of the repeating outer tile. 0 leaves the bake path.
uniform sampler2D night_macro : source_color, filter_linear, repeat_disable;
uniform float night_macro_on = 0.0;
uniform vec4 night_region = vec4(-340.0, -120.0, 340.0, 330.0);
// Ground beyond the macro (behind the garden) uses the outer grass tile, not black.
uniform sampler2D night_outer : source_color, filter_nearest, repeat_enable;
uniform float night_outer_on = 0.0;
uniform vec2 night_outer_scale = vec2(2.5, 1.5625);
uniform vec4 night_outer_plane = vec4(0.0, -80.0, 1280.0, 800.0); // origin x,z and size x,z
uniform float night_own_grass = 0.0; // 1 on GroundOuter: ALBEDO is already that tile

void fragment() {
	vec2 raw = UV;
	if (flip_v) { raw.y = 1.0 - raw.y; }
	vec2 uv = raw * uv_scale;
	ivec2 tsz = textureSize(albedo_tex, 0);
	vec2 tex_sz = vec2(tsz);
	vec2 uv_c = (floor(uv * tex_sz) + vec2(0.5)) / tex_sz;
	vec4 col = texture(albedo_tex, uv_c);
	ALBEDO = col.rgb * (1.0 - haze_amt);
	if (lawn_gain > 0.0) {
		vec2 d = (v_world.xz - lawn_center.xz) / lawn_radius;
		float k = 1.0 - smoothstep(0.35, 1.0, length(d));
		vec3 lifted = mix(ALBEDO, ALBEDO * lawn_tint.rgb * 1.9, 0.6);
		ALBEDO = mix(ALBEDO, lifted, k * lawn_gain);
		vec2 pd = (v_world.xz - lawn_center.xz - pool_off) / lawn_radius;
		ALBEDO *= mix(pool_core, vec3(1.0), smoothstep(0.08, 0.62, length(pd))) * mix(vec3(1.0), pool_edge, smoothstep(pool_r.x, pool_r.y, length(pd)));
	}
	if (gold_amt > 0.0) {
		float gg = texture(gold_tex, (v_world.xz + vec2(gold_half)) / (2.0 * gold_half)).r;
		ALBEDO *= mix(vec3(1.0), gold_gain, gg * gold_amt);
	}
	vec3 em = haze.rgb * haze_amt * 0.6;
	if (night_toe_gain > 0.0) {
		// Inside the bake, emit this fragment's albedo. Across the last 8 wu mix to the
		// wide macro where that macro exists. Beyond the macro (the ground behind the
		// garden) emit the outer grass tile at the same gain. Do not zero it.
		vec3 night_alb = ALBEDO;
		vec2 edge = abs(v_world.xz) - vec2(120.0);
		float outside = smoothstep(0.0, 8.0, max(edge.x, edge.y));
		vec2 muv = (v_world.xz - night_region.xy) / (night_region.zw - night_region.xy);
		bool macro_ok = night_macro_on > 0.0 && all(greaterThanEqual(muv, vec2(0.0))) && all(lessThanEqual(muv, vec2(1.0)));
		if (macro_ok && outside > 0.0) {
			vec3 mac = texture(night_macro, muv).rgb;
			night_alb = mix(ALBEDO, mac, outside);
		} else if (!macro_ok && night_own_grass < 0.5 && night_outer_on > 0.0 && outside > 0.0) {
			vec2 ouv = (v_world.xz - night_outer_plane.xy) / night_outer_plane.zw + vec2(0.5);
			ouv *= night_outer_scale;
			vec2 osz = vec2(textureSize(night_outer, 0));
			vec2 ouv_c = (floor(ouv * osz) + vec2(0.5)) / osz;
			night_alb = mix(ALBEDO, texture(night_outer, ouv_c).rgb, outside);
		}
		em += night_alb * night_sky_rgb * night_toe_gain;
	}
	EMISSION = em;
	ROUGHNESS = roughness_val;
	RIM = rim_amt;
	RIM_TINT = 0.6;
	METALLIC = 0.0;
	if (alpha_cut > 0.0) {
		ALPHA = col.a;
		ALPHA_SCISSOR_THRESHOLD = alpha_cut;
	}

	// Move lighting/shadow sample to the texel centre.
	vec2 off = uv_c - uv;
	vec2 du = dFdx(uv);
	vec2 dv = dFdy(uv);
	float det = du.x * dv.y - du.y * dv.x;
	if (abs(det) > 1e-8) {
		vec2 s = vec2(
			( dv.y * off.x - dv.x * off.y) / det,
			(-du.y * off.x + du.x * off.y) / det
		);
		LIGHT_VERTEX = VERTEX + dFdx(VERTEX) * s.x + dFdy(VERTEX) * s.y;
		NORMAL = normalize(NORMAL + dFdx(NORMAL) * s.x + dFdy(NORMAL) * s.y);
	}
	if (use_normal) {
		NORMAL_MAP = texture(normal_tex, uv_c).rgb;
		NORMAL_MAP_DEPTH = normal_depth;
	}
}
