// v6.11: born inside cloud gaps (sky cloud mask occlusion + break glow, see fragment).
// v6.10 soft god-ray card (original). Kurt 12:10: 天上中間個光仲係好生硬 — the v6.9 shafts were
// one flat strip texture each: straight hard edges, constant width, so they read as pasted bands.
// Now every card holds 3 sub-beams with a gaussian cross-profile (no edge anywhere), each with
// its own width that widens away from the sun, its own slow sway and its own brightness that
// varies along the beam; passing clouds (shared global cloud field) and leaves crossing the
// beam (shared wind) modulate it, so the light lives while the camera pans. Additive, unshaded.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
uniform vec4 tint : source_color = vec4(1.0, 0.80, 0.48, 1.0);
uniform float energy = 1.0;
uniform float alpha = 0.3;
uniform float seed = 0.0;
global uniform sampler2D cloud_tex : filter_linear, repeat_enable;
// v6.11 (Kurt: shafts must emerge FROM the clouds): the painted sky's cloud mask, looked up with
// exactly the sky dome's view-direction mapping (shaders/sky_dome.gdshader) so the beam knows
// whether the sky right behind it is a cloud body or a gap.
uniform sampler2D sky_cloud : filter_linear, repeat_disable;
uniform float cloud_occl = 0.92;
uniform float break_boost = 1.25;   // v6.12: 0.9 → 1.25 (birth in the cloud gap reads on the phone)
global uniform vec2 cloud_off;
varying vec3 wp;

float h1(float n) { return fract(sin(n * 127.1 + seed * 311.7) * 43758.5453); }
float vn(float x) { float i = floor(x); float f = fract(x); f = f * f * (3.0 - 2.0 * f); return mix(h1(i), h1(i + 1.0), f); }

float swind(float t, float ph) { return sin(t * 1.15 + ph) * 0.7 + sin(t * 2.7 + ph * 1.9) * 0.3; }
vec2 sky_uv(vec3 d) {
	float az = degrees(atan(d.x, -d.z)) + TIME * 0.25 + 0.6 * swind(TIME * 0.05, 0.0);
	az = mod(az + 180.0, 360.0) - 180.0;
	float u = abs(az) <= 100.0 ? (az + 100.0) / 200.0 : 1.0 - (az > 0.0 ? az - 100.0 : az + 260.0) / 160.0;
	float e = degrees(asin(clamp(d.y, -1.0, 1.0)));
	return vec2(clamp(u, 0.002, 0.998), clamp(1.0 - (e + 4.0) / 28.0, 0.004, 0.996));
}

void vertex() { wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }

void fragment() {
	float t = TIME;
	float x = UV.x;
	float al = UV.y;                       // 0 = sun end, 1 = floor end
	float m = 0.0;
	for (int k = 0; k < 3; k++) {
		float fk = float(k);
		float c = 0.5 + 0.30 * (h1(fk + 1.0) - 0.5) + 0.05 * sin(t * 0.11 + fk * 2.1 + al * 1.7);
		float wk = (0.09 + 0.09 * h1(fk + 7.0)) * (0.55 + 0.9 * al) * (1.0 + 0.22 * sin(t * 0.19 + fk * 1.3));
		float ik = 0.35 + 0.65 * vn(al * 2.6 + t * 0.045 + fk * 9.0 + seed * 3.0);
		float dx = (x - c) / wk;
		m += ik * exp(-dx * dx);
	}
	m *= smoothstep(0.0, 0.22, x) * smoothstep(1.0, 0.78, x);
	// v6.11: the beam is born in a cloud break — no start line: above the break it is hidden in
	// the cloud body (occluded by the sky's own cloud mask), brightest right under the break,
	// then a long soft fade toward the floor.
	float sc = texture(sky_cloud, sky_uv(normalize(wp - CAMERA_POSITION_WORLD))).r;
	float top = 1.0 - smoothstep(0.10, 0.50, al);           // upper part of the beam
	m *= smoothstep(0.0, 0.30, al) * (1.0 - smoothstep(0.40, 1.0, al));
	m *= 1.0 - cloud_occl * sc * top;                        // fades INTO the cloud volume
	m *= 1.0 + break_boost * (1.0 - sc) * top * smoothstep(0.02, 0.22, al);   // glow at the break
	m = m / (1.0 + 0.6 * m);   // soft shoulder: overlapping beams never clip into a hard core
	// leaves crossing the beam, and the cloud over the beam's path
	m *= 0.80 + 0.20 * vn(al * 9.0 - t * 0.6 + seed * 5.0);
	vec2 g = wp.xz - vec2(-0.645, -0.453) * (wp.y / 0.616);
	float cl = texture(cloud_tex, (g - cloud_off) / 560.0).r;
	m *= 1.0 - 0.75 * cl;
	float dith = (fract(sin(dot(FRAGCOORD.xy, vec2(12.9898, 78.233))) * 43758.5453) - 0.5) / 255.0;
	ALBEDO = max(tint.rgb * energy * m * alpha + dith, vec3(0.0));
}
