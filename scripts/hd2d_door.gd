extends RefCounted
class_name Hd2dDoor
## Measured 675 cottage door, plus a derived exterior goal.
## Cottage glb has no node transform. capture.gd places it at (82.5, 0, -72), yaw 0, scale 1.
## Local axes match world axes. The front wall is local z = 22 (world z = -50).
## The front plane has no triangles for x 3.5..19.5, y 0..48. A panel at local z = 19 closes it.
## That is a recess, not a passage. The threshold stays blocked.

const COTTAGE_WORLD := Vector3(82.5, 0.0, -72.0)
const OPEN_X0 := 3.5
const OPEN_X1 := 19.5
const OPEN_Y0 := 0.0
const OPEN_Y1 := 48.0
const OPEN_Z := 22.0
const RECESS_Z := 19.0
const OUTWARD := Vector3(0.0, 0.0, 1.0)

## H1 and 675 objects.json cottage footprint. pad is applied by Footprints.
const FOOT_X0 := 53.0
const FOOT_X1 := 112.0
const FOOT_Z0 := -94.0
const FOOT_Z1 := -50.0
const FOOT_PAD := 4.0
const WALKER_RADIUS := 10.0
## Walker NavigationAgent3D.target_desired_distance. A goal can be declared
## reached this far short of the point, on the approach from +Z.
const TARGET_DESIRED := 6.0
## Strict root block is z <= -36 at the door x. Candidate z = -30 can stop
## on that line. This 0.5 wu margin is an engineering stand for the route
## test, not the art-locked exterior anchor. The baked root mesh ends north
## of this stand, so a NavigationAgent goal has to snap onto the mesh.
## That snap is not a new anchor.
const ARRIVE_MARGIN := 0.5

const BLOCK_X := 47.0
const BLOCK_Z := -100.0
const BLOCK_W := 72.0
const BLOCK_H := 60.0
const PROP_R := 10.0


static func opening_center_local() -> Vector3:
	return Vector3((OPEN_X0 + OPEN_X1) * 0.5, (OPEN_Y0 + OPEN_Y1) * 0.5, OPEN_Z)


static func threshold_local() -> Vector3:
	return Vector3((OPEN_X0 + OPEN_X1) * 0.5, OPEN_Y0, OPEN_Z)


static func threshold_world() -> Vector3:
	return COTTAGE_WORLD + threshold_local()


static func opening_center_world() -> Vector3:
	return COTTAGE_WORLD + opening_center_local()


static func root_block_z() -> float:
	# Footprints: blocked while z - radius <= padded z1, i.e. z <= z1 + pad + radius.
	return FOOT_Z1 + FOOT_PAD + WALKER_RADIUS


static func exterior_anchor() -> Vector3:
	# Approaching from +Z, the agent may stop TARGET_DESIRED short of the goal.
	# Goal z must be greater than root_block_z + TARGET_DESIRED.
	var z := root_block_z() + TARGET_DESIRED + ARRIVE_MARGIN
	return Vector3(threshold_world().x, 0.0, z)


static func root_blocked(x: float, z: float, radius: float = WALKER_RADIUS) -> bool:
	var x0 := FOOT_X0 - FOOT_PAD
	var x1 := FOOT_X1 + FOOT_PAD
	var z0 := FOOT_Z0 - FOOT_PAD
	var z1 := FOOT_Z1 + FOOT_PAD
	return x + radius >= x0 and x - radius <= x1 and z + radius >= z0 and z - radius <= z1


static func pilot_blocked(p: Vector2, props: PackedVector2Array) -> bool:
	var rect := Rect2(BLOCK_X, BLOCK_Z, BLOCK_W, BLOCK_H)
	if rect.has_point(p):
		return true
	for q in props:
		if p.distance_to(q) < PROP_R:
			return true
	return false


static func pilot_props() -> PackedVector2Array:
	# Same points m1_roam._load_garden hardcodes. The route test matches the source text.
	return PackedVector2Array([
		Vector2(-72.5, 22), Vector2(71, 24), Vector2(-39, 42), Vector2(35, 22),
		Vector2(-81, 70), Vector2(81, 54), Vector2(49, 22), Vector2(22, 18),
		Vector2(-24, 28), Vector2(48, 48), Vector2(18, 8), Vector2(-15, 35),
		Vector2(30, -20),
	])
