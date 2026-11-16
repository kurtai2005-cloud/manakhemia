// v6.4 leafy silhouette card (original): camera-facing (CPU-oriented), alpha-scissor (no blending →
// cheap on Mobile), lit with the normal of the leaf ball it sits on (INSTANCE_CUSTOM.xyz),
// per-instance value in COLOR.a (normal packed in COLOR.rgb; INSTANCE_CUSTOM is unreliable on Compatibility). Same haze model as texel_lit.gdshader.
shader_type spatial;
render_mode cull_disabled, diffuse_lambert_wrap, specular_disabled;
uniform vec3 backlight_col : source_color = vec3(0.55, 0.62, 0.16);
uniform sampler2D albedo_tex : source_color, filter_nearest;
uniform vec4 haze : source_color = vec4(1.0, 0.86, 0.62, 1.0);
uniform float haze_amt : hint_range(0.0, 1.0) = 0.0;
varying vec3 ball_n;
varying vec3 tint;
// v6.13 lower mid: same warm sunlit lift zone as clump_card.gdshader (set per day by art_depth.gd)
uniform vec4 warm_zone = vec4(5.0, -40.0, 190.0, 135.0);
uniform vec3 warm_gain = vec3(1.0);
uniform vec3 warm_add = vec3(0.0);   // v6.14 see clump_card (Mobile: linear gain reads weak → warm add)
varying float wz_k;

void vertex() {
	// cards are pre-oriented to the (near-static) camera on the CPU; no MODELVIEW tricks so
	// MultiMesh instance transforms work identically on Compatibility and Mobile.
	ball_n = (VIEW_MATRIX * vec4(normalize(COLOR.rgb * 2.0 - 1.0), 0.0)).xyz;
	tint = vec3(COLOR.a * 1.5);
	vec3 pb = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	vec2 zd = (pb.xz - warm_zone.xy) / warm_zone.zw;
	wz_k = (1.0 - smoothstep(0.6, 1.0, length(zd))) * (0.55 + 0.45 * (1.0 - UV.y)) * step(pb.y, 90.0);
}

void fragment() {
	vec4 c = texture(albedo_tex, UV);
	ALBEDO = c.rgb * tint * (1.0 - haze_amt) * mix(vec3(1.0), warm_gain, wz_k);
	ALBEDO += warm_add * wz_k * smoothstep(0.005, 0.06, dot(ALBEDO, vec3(0.30, 0.59, 0.11)));
	EMISSION = haze.rgb * haze_amt * 0.6;
	ALPHA = c.a;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	ROUGHNESS = 1.0;
	NORMAL = normalize(ball_n);
	BACKLIGHT = backlight_col;  // sun-through-leaves translucency on the rim clumps
}
