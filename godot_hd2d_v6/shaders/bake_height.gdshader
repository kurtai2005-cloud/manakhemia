// v6.9 bake tool only (HD2D_BAKE_HEIGHT=1): top-down caster height, R = y / 400 wu.
// HD2D_BAKE_FOOT=1 sets clip_y → only the parts touching the ground (footprints for contact AO).
// Used by tools/bake_ground_v6_9.py for contact-hardening penumbrae and footprint contact AO.
shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled, fog_disabled;
uniform float clip_y = 100000.0;
varying float hy;
void vertex() { hy = (MODEL_MATRIX * vec4(VERTEX, 1.0)).y; }
void fragment() {
	if (hy > clip_y) { discard; }
	ALBEDO = clip_y < 1000.0 ? vec3(1.0) : vec3(clamp(hy / 400.0, 0.0, 1.0));
}
