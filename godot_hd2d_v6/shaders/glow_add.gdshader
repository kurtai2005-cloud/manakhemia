// Additive HDR glow for dust motes (billboard, soft dot) and light-shaft cards.
// Original shader for 微光小圃 test.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform vec4 tint : source_color = vec4(1.0, 0.85, 0.55, 1.0);
uniform float energy = 2.0;
uniform float alpha = 1.0;
uniform int mask_mode = 0; // 0 = soft dot, 1 = shaft (fade both ends, soft edges)
uniform bool billboard = false;

void vertex() {
	if (billboard) {
		float s = length(MODEL_MATRIX[0].xyz);
		MODELVIEW_MATRIX = VIEW_MATRIX * mat4(
			vec4(INV_VIEW_MATRIX[0].xyz * s, 0.0),
			vec4(INV_VIEW_MATRIX[1].xyz * s, 0.0),
			vec4(INV_VIEW_MATRIX[2].xyz * s, 0.0),
			MODEL_MATRIX[3]);
	}
}

void fragment() {
	float m;
	if (mask_mode == 0) {
		float d = length(UV - vec2(0.5)) * 2.0;
		m = clamp(1.0 - d, 0.0, 1.0);
		m = m * m;
	} else {
		float across = 1.0 - abs(UV.x - 0.5) * 2.0;
		float along = smoothstep(0.0, 0.35, UV.y) * smoothstep(1.0, 0.55, UV.y);
		m = smoothstep(0.0, 1.0, across) * along;
	}
	ALBEDO = tint.rgb * energy * m * alpha;
}
