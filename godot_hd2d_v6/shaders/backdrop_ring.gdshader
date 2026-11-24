// v6.8: forest band only, sky cut out. v6.7 360° backdrop (original): the pre-blurred painted forest (backdrop_ring.png, seamless)
// wrapped on an inward-facing cylinder around the whole garden, so no camera yaw / pet
// position ever sees an edge-on board or the end of the world. Unshaded, no fog (the paint
// already carries its haze), LINEAR (out of focus), seam placed behind the camera.
shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled, fog_disabled;
uniform sampler2D tex : source_color, filter_linear, repeat_enable;
uniform float repeats = 1.0;
uniform vec3 light_mul = vec3(1.0);
// v6.11 (concept: the far forest dissolves into bright gold haze): warm aerial mist, stronger at
// the treeline base; same draw, 2 ALU ops.
uniform vec3 haze_col : source_color = vec3(0.93, 0.78, 0.50);
uniform float haze_amt = 0.0;

float bayer4(vec2 p) {
	ivec2 q = ivec2(mod(p, 4.0));
	int i = q.x + q.y * 4;
	const float m[16] = float[](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
	return (m[i] + 0.5) / 16.0;
}

void fragment() {
	vec2 uv = vec2(UV.x * repeats, UV.y);
	vec4 t = texture(tex, uv);
	// v6.8: the painted sky is cut out (treeline alpha) → the sky dome shows above the forest;
	// dithered cut in the opaque pass (no sorting against rays / haze)
	if (t.a < bayer4(FRAGCOORD.xy)) {
		discard;
	}
	float hz = haze_amt * (0.55 + 0.45 * smoothstep(0.35, 1.0, UV.y));
	ALBEDO = mix(t.rgb, haze_col, hz) * light_mul;
}
