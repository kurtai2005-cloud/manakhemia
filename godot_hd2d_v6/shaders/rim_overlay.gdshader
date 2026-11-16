// Golden back-light rim, drawn as a material_overlay (additive) on 3D props.
// Fresnel edge × facing-the-sun, so only sun-side silhouettes glow.
// Original shader for 微光小圃 test.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_back, shadows_disabled, fog_disabled;
uniform vec4 rim_color : source_color = vec4(1.0, 0.76, 0.40, 1.0);
uniform float amt = 0.45;
uniform vec3 to_sun = vec3(-0.80, 0.33, -0.56);
uniform float power = 2.5;
void fragment() {
	vec3 L = normalize((VIEW_MATRIX * vec4(normalize(to_sun), 0.0)).xyz);
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), power);
	float facing = clamp(dot(NORMAL, L) * 0.6 + 0.4, 0.0, 1.0);
	ALBEDO = rim_color.rgb * amt * fres * facing * facing;
}
