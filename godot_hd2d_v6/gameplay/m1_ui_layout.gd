extends RefCounted
## art r1.1 layout. Source pixels stay 32 / 40 / 48.
## 540-wide reference uses ×2 Nearest and a 96px touch pad.
## 1080-wide uses ×4 and a 192px touch pad.
## Positions use the live viewport, so a 1080×1920 window does not
## place the 540×1140 row at y=2064.

const REF_W := 540.0

const CARE_IDS: PackedStringArray = ["feed", "water", "poop", "pat"]


static func layout_scale(viewport_w: float) -> int:
	if viewport_w <= 1.0:
		return 1
	return maxi(1, int(round(viewport_w / REF_W)))


static func tex_mul(layout: int) -> int:
	return 2 * maxi(layout, 1)


static func button_display(layout: int) -> int:
	return 40 * tex_mul(layout)


static func button_touch(layout: int) -> int:
	return 96 * maxi(layout, 1)


static func bubble_display(layout: int) -> int:
	return 48 * tex_mul(layout)


static func care_row(viewport: Vector2, layout: int) -> Dictionary:
	var disp := button_display(layout)
	var touch := button_touch(layout)
	var gap := 8 * layout
	var inset_b := 28 * layout
	var total := disp * CARE_IDS.size() + gap * (CARE_IDS.size() - 1)
	var x0 := int(round((viewport.x - float(total)) * 0.5))
	var y := int(round(viewport.y - float(inset_b + disp)))
	var pad := int(round(float(touch - disp) * 0.5))
	var slots: Array = []
	for i in CARE_IDS.size():
		var dx := x0 + i * (disp + gap)
		slots.append({
			"id": CARE_IDS[i],
			"display": Vector2(dx, y),
			"touch": Vector2(dx - pad, y - pad),
		})
	return {
		"display": disp,
		"touch": touch,
		"slots": slots,
	}


static func admire_slot(viewport: Vector2, layout: int) -> Dictionary:
	var disp := button_display(layout)
	var touch := button_touch(layout)
	var pad := int(round(float(touch - disp) * 0.5))
	var x := int(round(viewport.x - float(24 * layout + disp)))
	var y := 28 * layout
	return {
		"display": Vector2(x, y),
		"touch": Vector2(x - pad, y - pad),
		"size_display": disp,
		"size_touch": touch,
	}


static func effect(id: String) -> String:
	match id:
		"feed":
			return "feed"
		"pat":
			return "pat"
		"poop":
			return "clean_one"
		"water":
			return "none"
		"admire":
			return "appreciate"
	return "none"


static func blocks_ground(shown: bool, alpha: float) -> bool:
	return shown and alpha > 0.2


static func debug_chrome_visible(dev_on: bool) -> bool:
	# Quality, tone, the large developer toggle, and the FPS line.
	# The small developer entry stays up either way.
	return dev_on


static func bubble_top_left(head_px: Vector2, size_px: float) -> Vector2:
	# Bottom-center of the bubble sits on the pet head. No sideways bias.
	return Vector2(head_px.x - size_px * 0.5, head_px.y - size_px)


static func bubble_shown(has_need: bool, appreciate: bool, alpha: float) -> bool:
	# SPEC: appreciate hides the bubble. The 3s fade uses modulate and
	# drops the bubble once the panel is essentially gone.
	return has_need and (not appreciate) and alpha > 0.05
