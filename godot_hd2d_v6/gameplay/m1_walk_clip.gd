extends RefCounted
## r4 walk candidate. Presentation only.
## Manual speed stays capture.WALK_SPEED (48). Autonomous speed stays
## m1_roam.SPEED (20) times the personality multiplier. This type never
## chooses a speed. It only consumes an XZ step the pet already achieved.
## Zero distance (idle, care hold, blocked) does not advance the phase
## and does not play a walk frame.
## Side art faces right. flip_h mirrors it for screen-left.
## A stopped side facing uses side_idle, which is the contact frame.
## Front and back are the supplied projections. They do not lock a Z foot.

const FRAME_COUNT := 6
const STRIDE_WU := 12.0
const WU_PER_FRAME := 2.0
const FRAME_PX := 64
## Image boundary after the last opaque row. Row 62 occupies boundaries 62..63.
## Row 63 is empty on every r4 frame. 0 is the top edge.
const SOLE_BOTTOM_BOUNDARY := 63
## Node stays at y=29. This pixel offset lifts only the quad so boundary 63 is at world Y=0.
const GROUNDED_OFFSET_Y := 2.0
const FACINGS: PackedStringArray = ["front", "back", "side"]
const ROOT := "res://art/pet/r4/"

var facing := "front"
var flip_h := false
var phase_wu := 0.0
var moving := false


func advance(delta: Vector2, view_right: Vector2, view_away: Vector2) -> void:
	var dist := delta.length()
	if dist <= 0.0001:
		moving = false
		return
	moving = true
	phase_wu += dist
	_face(delta, view_right, view_away)


func frame_index() -> int:
	var n := int(floor(phase_wu / WU_PER_FRAME))
	var m := n % FRAME_COUNT
	if m < 0:
		m += FRAME_COUNT
	return m


func clip_name() -> String:
	if moving:
		return facing + "_walk"
	return facing + "_idle"


func texture_path() -> String:
	if moving:
		return ROOT + "pet_tuanrong_radiant_%s_walk_%02d.png" % [facing, frame_index() + 1]
	return ROOT + "pet_tuanrong_radiant_%s_idle_01.png" % facing


func state() -> Dictionary:
	return {
		"facing": facing,
		"flip_h": flip_h,
		"phase_wu": phase_wu,
		"moving": moving,
		"frame": frame_index() if moving else -1,
		"clip": clip_name(),
		"path": texture_path(),
		# Side sheet is the one the art owner locked on X at sample frames.
		# Front and back stay projections. Neither case is a continuous lock.
		"side_foot_identity": facing == "side",
		"z_lock": false,
		"continuous_lock": false,
	}


static func sole_boundary_world_y(node_y: float, offset_y: float) -> float:
	# Godot 4.7.2 SpriteBase3D, axis Z, centered: local Y = offset.y + frame/2 - image_boundary.
	return node_y + offset_y + float(FRAME_PX) * 0.5 - float(SOLE_BOTTOM_BOUNDARY)


static func row_center_world_y(node_y: float, offset_y: float, row: int) -> float:
	return node_y + offset_y + float(FRAME_PX) * 0.5 - (float(row) + 0.5)


static func row_edge_world_y(node_y: float, offset_y: float, boundary: int) -> float:
	return node_y + offset_y + float(FRAME_PX) * 0.5 - float(boundary)


static func frame_paths() -> PackedStringArray:
	var out: PackedStringArray = []
	for face in FACINGS:
		out.append(ROOT + "pet_tuanrong_radiant_%s_idle_01.png" % face)
		for i in FRAME_COUNT:
			out.append(ROOT + "pet_tuanrong_radiant_%s_walk_%02d.png" % [face, i + 1])
	return out


func _face(delta: Vector2, view_right: Vector2, view_away: Vector2) -> void:
	var right := view_right
	var away := view_away
	if right.length_squared() < 0.00000001:
		right = Vector2(1, 0)
	else:
		right = right.normalized()
	if away.length_squared() < 0.00000001:
		away = Vector2(0, -1)
	else:
		away = away.normalized()
	var lateral := delta.dot(right)
	var depth := delta.dot(away)
	if absf(lateral) > absf(depth):
		facing = "side"
		flip_h = lateral < 0.0
	elif absf(depth) > absf(lateral):
		facing = "back" if depth > 0.0 else "front"
		flip_h = false
	# Equal components keep the facing already on screen.
