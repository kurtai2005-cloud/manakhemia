extends RefCounted
## Observation camera on top of the vc27 opening offset.
## Translation only. No yaw and no legacy 5° sway.


static func desired(base: Vector3, origin: Vector3, pet_xz: Vector3, overview: bool) -> Vector3:
	if overview:
		return base
	return base + Vector3(pet_xz.x - origin.x, 0.0, pet_xz.z - origin.z)


static func keeps_height(base: Vector3, got: Vector3) -> bool:
	return is_equal_approx(got.y, base.y)


static func zoom_scale(measured: float, need: float) -> float:
	# Distance ratio from the 54-unit box. Not applied to the opening camera.
	if need <= 0.0 or measured <= 0.0 or measured >= need:
		return 1.0
	return clampf(measured / need, 0.35, 1.0)


static func zoomed_along(far_cam: Vector3, subject: Vector3, scale: float) -> Vector3:
	# Closer on the ray from the pet to the opening camera. Heading stays.
	var s := clampf(scale, 0.35, 1.0)
	return subject + (far_cam - subject) * s


static func accept_follow(measured: float, need: float) -> bool:
	# Exact line. 0.199 does not pass a 0.20 requirement.
	return need <= 0.0 or measured >= need


static func portrait_box_fraction(cam_pos: Vector3, orient_from: Vector3, orient_to: Vector3, pet: Vector3, viewport: Vector2, hfov_deg: float, box_h: float) -> float:
	# KEEP_WIDTH unproject. Orientation stays the opening view; cam_pos may be closer.
	if viewport.y < 1.0 or viewport.x < 1.0:
		return 0.0
	var back := (orient_from - orient_to).normalized()
	var x_axis := Vector3.UP.cross(back).normalized()
	var y_axis := back.cross(x_axis)
	var half_h := deg_to_rad(hfov_deg) * 0.5
	var tan_v := tan(half_h) * (viewport.y / viewport.x)
	var top := pet + Vector3(0, box_h * 0.5, 0)
	var bot := pet + Vector3(0, -box_h * 0.5, 0)
	var sy_top := _screen_y(cam_pos, y_axis, back, top, viewport.y, tan_v)
	var sy_bot := _screen_y(cam_pos, y_axis, back, bot, viewport.y, tan_v)
	return absf(sy_bot - sy_top) / viewport.y


static func _screen_y(cam_pos: Vector3, y_axis: Vector3, back: Vector3, world: Vector3, height: float, tan_v: float) -> float:
	var d := world - cam_pos
	var cy := d.dot(y_axis)
	var cz := d.dot(back)
	var ny := (cy / -cz) / tan_v
	return (0.5 - ny * 0.5) * height


static func approached(start: Vector3, goal: Vector3, damping: float, t: float) -> Vector3:
	var u := 1.0 - exp(-damping * t)
	return start.lerp(goal, u)
