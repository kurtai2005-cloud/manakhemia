// v6.8 sky (original shader): one continuous painted sky on an inward sphere riding with the
// camera. Mapped by view direction: azimuth 0 = forward (−Z); the image spans −100°..+100°
// (warm glow upper-left, where the sun is), the back 160° repeats it mirrored so the wrap is
// continuous (fold at ±100°, outside any ±45° yaw). Elevation −4°..+30° → image bottom..top;
// above that it eases into the image's top colour. Clouds drift slowly with the shared wind.
shader_type spatial;
render_mode unshaded, cull_front, shadows_disabled, fog_disabled;
uniform sampler2D tex : source_color, filter_linear, repeat_disable;
uniform vec3 light_mul = vec3(1.0);
uniform float e0 = -4.0;
uniform float e1 = 24.0;
uniform float drift = 0.25;   // degrees per second
uniform float glow_amt = 0.30;
uniform float ray_amt = 0.26;   // v6.10 r2: r1 rays barely read on PC
uniform vec3 sun_col : source_color = vec3(1.0, 0.80, 0.46);
global uniform sampler2D cloud_tex : filter_linear, repeat_enable;
uniform sampler2D sky_cloud : filter_linear, repeat_disable;   // v6.11 R cloud body, G sun-facing edge
uniform float rim_amt = 0.60;
uniform float break_amt = 0.10;
global uniform vec2 cloud_off;
varying vec3 wpos;

// v6.10 (Kurt 12:10: the light in the middle of the sky is still stiff): the sun glow and the
// crepuscular rays now live IN the sky at infinity, around the real sun direction (38°,
// back-left — the same vector as the light and the bake). Glow = smooth double falloff (no
// edge, no band); rays = soft angular noise around the sun axis, varying width / strength,
// drifting with the shared cloud field; dithered so the gradient never bands.
float sh1(float n) { return fract(sin(n * 91.7) * 43758.5453); }
float svn(float x) { float i = floor(x); float f = fract(x); f = f * f * (3.0 - 2.0 * f); return mix(sh1(i), sh1(i + 1.0), f); }

float wind(float t, float ph) { return sin(t * 1.15 + ph) * 0.7 + sin(t * 2.7 + ph * 1.9) * 0.3; }

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 d = normalize(wpos - CAMERA_POSITION_WORLD);
	float az = degrees(atan(d.x, -d.z)) + TIME * drift + 0.6 * wind(TIME * 0.05, 0.0);
	az = mod(az + 180.0, 360.0) - 180.0;
	float u;
	if (abs(az) <= 100.0) {
		u = (az + 100.0) / 200.0;
	} else {
		float a2 = az > 0.0 ? az - 100.0 : az + 260.0;
		u = 1.0 - a2 / 160.0;
	}
	float e = degrees(asin(clamp(d.y, -1.0, 1.0)));
	float v = clamp(1.0 - (e - e0) / (e1 - e0), 0.0, 1.0);
	vec3 c = texture(tex, vec2(clamp(u, 0.002, 0.998), clamp(v, 0.004, 0.996))).rgb;
	vec3 S = normalize(vec3(-0.645, 0.616, -0.453));
	float gang = sqrt(max(2.0 - 2.0 * dot(d, S), 0.0));     // chord ≈ radians from the sun (cheaper than acos)
	vec3 t1 = normalize(cross(S, vec3(0.0, 1.0, 0.0)));
	vec3 t2 = cross(t1, S);
	float clock = atan(dot(d, t2), dot(d, t1));
	float glow = 0.55 * exp(-gang * gang / 0.18) + 0.45 * exp(-gang / 0.75);
	float cl = texture(cloud_tex, vec2(clock * 0.35, gang * 0.25) + cloud_off / 900.0).r;
	float r1 = svn(clock * 11.0 + TIME * 0.018);
	float r2 = svn(clock * 27.0 - TIME * 0.031 + 17.0);
	float rays = smoothstep(0.30, 0.95, 0.62 * r1 + 0.38 * r2) * (1.0 - 0.8 * cl);
	rays *= smoothstep(0.05, 0.30, gang) * exp(-gang / 0.95);
	float lum = dot(c, vec3(0.3, 0.55, 0.15));
	float lift = (glow * glow_amt + rays * ray_amt) * (1.15 - lum);   // stronger in the darker gaps
	c += sun_col * lift;
	// v6.11 (Kurt: cloud edges rim-lit, brightest at the cloud break): golden rim on the
	// sun-facing cloud edges, strongest toward the sun; open gaps near the sun glow a little.
	vec2 ck = texture(sky_cloud, vec2(clamp(u, 0.002, 0.998), clamp(v, 0.004, 0.996))).rg;
	float near_sun = 0.35 + 0.65 * exp(-gang / 0.9);
	c += sun_col * (ck.g * rim_amt * near_sun + (1.0 - ck.r) * break_amt * glow);
	c = mix(c, c * vec3(1.03, 0.99, 0.90) + vec3(0.02, 0.015, 0.0), clamp(1.0 - e / 10.0, 0.0, 1.0) * 0.5);  // warm gold haze at the horizon
	c += (fract(sin(dot(FRAGCOORD.xy, vec2(12.9898, 78.233))) * 43758.5453) - 0.5) / 255.0;
	ALBEDO = c * light_mul;
}
