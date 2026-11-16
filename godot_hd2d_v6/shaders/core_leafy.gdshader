// v6.7 canopy / bush core (original): the dark mass behind the clump cards. Phone check (0.6.6)
// showed the old flat unshaded spheres as smooth dark discs whenever the camera moved. Now:
// leaf-textured (world-locked pattern on the camera plane, 1 texel ≈ px wu), darker underside,
// and a LEAFY silhouette: near grazing angles only leaf-covered texels survive (alpha-scissor
// style discard), so the outline is broken leaves, never a polygon edge. Unshaded, 1 draw.
shader_type spatial;
render_mode unshaded, cull_back, shadows_disabled;
uniform sampler2D leaf_tile : filter_nearest, repeat_enable;
uniform vec3 col : source_color = vec3(0.12, 0.15, 0.055);
uniform vec3 light_mul = vec3(1.0);
uniform float px = 0.7;
uniform float rim_cut = 0.55;
varying vec3 wpos;
varying vec3 wn;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 n = normalize(wn);
	vec3 v = normalize(CAMERA_POSITION_WORLD - wpos);
	float ndv = clamp(dot(n, v), 0.0, 1.0);
	vec3 cr = INV_VIEW_MATRIX[0].xyz;
	vec3 cu = INV_VIEW_MATRIX[1].xyz;
	vec2 p = vec2(dot(wpos, cr), -dot(wpos, cu)) / (px * 64.0);
	vec2 ts = vec2(64.0);
	p = (floor(p * ts) + 0.5) / ts;
	vec4 t = texture(leaf_tile, p);
	// leafy silhouette: the closer to grazing, the more leaf coverage is needed to survive
	float need = smoothstep(rim_cut, 0.05, ndv);
	if (t.g < need * 0.98 || ndv < 0.06) {
		discard;
	}
	float under = smoothstep(0.2, -0.7, n.y);
	vec3 c = col * (0.35 + 1.55 * t.r)  /* v6.8: more leaf contrast, no smooth dark ball */ * (1.0 - 0.45 * under) * (0.9 + 0.35 * max(n.y, 0.0));
	ALBEDO = c * light_mul;
}
