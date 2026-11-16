extends RefCounted
## Observation camera on top of the vc27 opening offset.
## Translation only. No yaw and no legacy 5° sway.


static func desired(base: Vector3, origin: Vector3, pet_xz: Vector3, overview: bool) -> Vector3:
	if overview:
		return base
	return base + Vector3(pet_xz.x - origin.x, 0.0, pet_xz.z - origin.z)


static func keeps_height(base: Vector3, got: Vector3) -> bool:
	return is_equal_approx(got.y, base.y)
