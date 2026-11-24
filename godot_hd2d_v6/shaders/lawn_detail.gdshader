// v6.6 near-camera lawn detail (original): fine dark grass-blade grain (alpha blend; a
// multiply blend went black in High on Compatibility) over the bottom-third
// lawn (4 px/wu vs the ground's 1–2 px/wu), world-space tiled, faded at the far edge and sides.
// Strokes only darken a little → baked shadows / night stay correct. 1 draw.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
uniform sampler2D detail : filter_nearest, repeat_enable;
uniform float tile = 64.0;
uniform float strength = 1.0;
varying vec3 wp;

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 d = texture(detail, wp.xz / tile).rgb;
	float f = smoothstep(0.0, 0.35, UV.y) * smoothstep(0.0, 0.10, UV.x) * smoothstep(1.0, 0.90, UV.x);
	ALBEDO = vec3(0.07, 0.10, 0.035);
	ALPHA = clamp((1.0 - d.r) * 2.6, 0.0, 1.0) * f * strength;
}
