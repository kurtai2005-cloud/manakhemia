// Screen grade for High only: warm vignette + soft top-left sun leak.
// Original shader for 微光小圃 test.
shader_type canvas_item;
uniform vec4 vignette_color : source_color = vec4(0.08, 0.07, 0.05, 1.0);
uniform float vignette_strength = 0.65;
uniform vec4 leak_color : source_color = vec4(1.0, 0.86, 0.62, 1.0);
uniform float leak_strength = 0.08;
uniform vec2 leak_pos = vec2(0.18, -0.05);

void fragment() {
	vec2 uv = SCREEN_UV;
	vec2 c = (uv - vec2(0.5)) * vec2(1.25, 1.0);
	float v = smoothstep(0.35, 0.95, length(c)) * vignette_strength;
	float l = clamp(1.0 - length((uv - leak_pos) * vec2(1.0, 1.4)) / 0.75, 0.0, 1.0);
	l = l * l * leak_strength;
	// premultiplied-ish: darken edges, add leak
	vec3 col = mix(leak_color.rgb, vignette_color.rgb, v / max(v + l, 1e-4));
	COLOR = vec4(col, clamp(v + l, 0.0, 0.85));
}
