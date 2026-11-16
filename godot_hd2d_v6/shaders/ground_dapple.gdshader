// v6.7 moving leaf-light on the ground (original). One blended overlay plane just above the
// lawn (render_priority −1, before the other transparents; depth-tested, so props / pet / tufts
// sit on top). Two scrolling copies of dapple_leaf.png drift with the SAME wind() as the
// clump / tuft sway, so the light moves when the leaves move:
//   • in the sun: soft leaf-shadow patches pass over the lawn;
//   • in shade (baked tree shadow, wide mask): warm sun flecks open and close;
//   • outside the 256 wu baked ground: the wide bake's tree shadows (softened) are drawn here,
//     so the outer lawn is no longer shadowless.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_back, shadows_disabled, fog_disabled;
uniform sampler2D dapple : filter_linear, repeat_enable;
uniform sampler2D wide_mask : filter_linear, repeat_disable;   // 1 = sun, 0 = shade (x,z ±half)
uniform float wide_half = 320.0;
uniform float inner_half = 128.0;
uniform float tile = 96.0;
uniform vec2 wind_dir = vec2(0.80, 0.60);
uniform float speed = 1.15;   // vc25: 2.4 + opposing second layer read as sharp flutter; baked tree shade (st) stays world-fixed
uniform float fleck_amt = 0.17;   // v6.9: fewer round sun-spots (Kurt: nothing pasted on)
uniform float shade_amt = 0.20;
uniform float static_amt = 0.26;   // v6.8: lighter outer-lawn tree shade (golden-green, not mush)
uniform vec3 fleck_col : source_color = vec3(0.96, 0.78, 0.38);
uniform vec3 shade_col : source_color = vec3(0.05, 0.07, 0.03);
uniform float day = 1.0;
// v6.10 (Kurt: 最遠d鏡無影 — the farthest view had no shadows): far shade is no longer faded
// out with camera distance. Instead it follows aerial perspective: lifted and tinted toward
// the gold-green haze. The painted backdrop forest (inward cylinder r 462) also casts: a ray
// from the lawn toward the sun (38°) meets the ring; if it passes below the painted treeline
// height there, the lawn is in the forest's shade (closed form, no loop, no extra draw).
uniform sampler2D ring_h : filter_linear, repeat_enable;   // painted treeline height / 400 by ring u
uniform float ring_r = 462.0;
uniform float ring_yaw = 3.14159265;
uniform float ring_h_scale = 0.55;     // painted trees stand far behind the cylinder → shorter reach
uniform float ring_amt = 0.30;
uniform vec3 haze_col : source_color = vec3(0.36, 0.33, 0.17);
uniform float far0 = 280.0;
uniform float far1 = 620.0;
varying vec3 w;

// v6.9 one cloud field for the whole scene (project.godot shader_globals, art_depth.gd feeds
// cloud_off): a point p is under the same cloud as the ground point p − SUN·(p.y/SUN.y).
global uniform sampler2D cloud_tex : filter_linear, repeat_enable;
global uniform vec2 cloud_off;
global uniform float cloud_amt;
float cloud_at(vec3 p) {
	vec2 g = p.xz - vec2(-0.645, -0.453) * (p.y / 0.616);
	return texture(cloud_tex, (g - cloud_off) / 560.0).r;
}
float wind(float t, float ph) { return sin(t * 1.15 + ph) * 0.7 + sin(t * 2.7 + ph * 1.9) * 0.3; }

void vertex() {
	w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float t = TIME;
	vec2 drift = wind_dir * (t * speed + 0.65 * wind(t, 0.0));
	vec4 a = texture(dapple, (w.xz + drift) / tile);
	vec4 b = texture(dapple, (w.xz * 0.71 - drift * 0.25 + vec2(37.0, 11.0)) / (tile * 1.35));
	vec2 muv = (w.xz + vec2(wide_half)) / (2.0 * wide_half);
	float sun = 1.0;
	if (muv.x > 0.0 && muv.x < 1.0 && muv.y > 0.0 && muv.y < 1.0) {
		sun = texture(wide_mask, muv).r;
	}
	// painted-forest shade (backdrop ring)
	vec2 u2 = normalize(vec2(-0.645, -0.453));
	float pu = dot(w.xz, u2);
	float tr = -pu + sqrt(max(pu * pu - (dot(w.xz, w.xz) - ring_r * ring_r), 0.0));
	vec2 hitp = w.xz + u2 * tr;
	float ang = atan(hitp.x, hitp.y);   // CylinderMesh: local (sin 2πu, cos 2πu), then rotated by ring_yaw
	float ru = fract((ang - ring_yaw) / 6.2831853 + 2.0);
	float rh = texture(ring_h, vec2(ru, 0.5)).r * 400.0 * ring_h_scale;
	float ray_y = tr * 0.7813;   // tan(38°)
	float pen = 10.0 + 0.10 * tr;
	float ring_sh = 1.0 - smoothstep(rh - pen, rh + pen, ray_y);
	ring_sh *= 0.75 + 0.25 * clamp(a.g * 0.9 + b.g * 0.6, 0.0, 1.0);   // leafy breakup
	vec2 q = abs(w.xz) - vec2(inner_half - 10.0);
	float outer = clamp(max(q.x, q.y) / 10.0, 0.0, 1.0);   // 0 on the baked inner ground
	float fl = clamp(a.r * 0.8 + b.r * 0.5, 0.0, 1.0) * (1.0 - sun) * fleck_amt * day;
	float sh = clamp(a.g * 0.7 + b.g * 0.5, 0.0, 1.0) * sun * shade_amt;
	float dcam = length(w.xz - CAMERA_POSITION_WORLD.xz);
	float far = smoothstep(far0, far1, dcam);
	float st = max((1.0 - sun) * outer * static_amt, ring_sh * ring_amt * outer);
	st *= 1.0 - 0.20 * far;   // aerial perspective: far shade is lighter
	// v6.9: a passing cloud closes the sun flecks, softens the leaf shade and dims the lawn
	float cl = cloud_at(w) * day;
	fl *= 1.0 - cl;
	sh *= 1.0 - 0.7 * cl;
	float da = max(sh, st) + cl * cloud_amt * (1.0 - st);
	float al = clamp(fl + da, 0.0, 0.85);
	// fade with distance so the far lawn / backdrop seam is untouched
	float dc = length(w.xz - CAMERA_POSITION_WORLD.xz);
	da = max(sh, st) + cl * cloud_amt * (1.0 - st);
	// v6.7 r2: flecks were big yellow blobs right under the lens (perspective) → thin them near the camera
	fl *= mix(0.25, 1.0, smoothstep(60.0, 170.0, dc));
	al = clamp(fl + da, 0.0, 0.85);
	// v6.10: only the moving flecks / leaf shade fade with distance; static shade stays
	float near_dyn = 1.0 - smoothstep(360.0, 480.0, dc);
	fl *= near_dyn;
	sh *= near_dyn;
	da = max(sh, st) + cl * cloud_amt * (1.0 - st);
	al = clamp(fl + da, 0.0, 0.85);
	if (al < 0.004) {
		discard;
	}
	vec3 scol = mix(shade_col, haze_col, far);
	ALBEDO = (fleck_col * fl + scol * da) / max(fl + da, 1e-3);
	ALPHA = al;
}
