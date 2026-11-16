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
	# m1a follow_pet_min_frac. The opening panorama is not passed through here.
	if need <= 0.001 or measured <= 0.001 or measured >= need - 0.002:
		return 1.0
	return clampf(measured / need, 0.35, 1.0)


static func zoomed_along(far_cam: Vector3, subject: Vector3, scale: float) -> Vector3:
	# Closer on the ray from the pet to the opening camera. Heading stays.
	# The opening panorama is not passed through here.
	var s := clampf(scale, 0.35, 1.0)
	return subject + (far_cam - subject) * s
