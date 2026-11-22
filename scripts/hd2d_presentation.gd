extends Node
## Root-owned pet presentation and door approach.
## Does not instance capture.tscn, does not tick m1_roam, and does not save.
## The Walker remains the only body. Main remains the only camera and input.

const WalkClip := preload("res://godot_hd2d_v6/gameplay/m1_walk_clip.gd")
const Assets := preload("res://scripts/hd2d_assets.gd")

var active := false
var approaching := false
var arrived := false
var blocked_stop := false
var nav_snapped := false
var requested_goal := Vector3.ZERO
var main: Node3D
var walker: Walker
var clip: RefCounted
var coat: Sprite3D
var goal := Vector3.ZERO
var _last := Vector2.ZERO
var _have_last := false
var _tex: Dictionary = {}
var _tree_on := true
var _brain: Node
var _care_id := ""
var _care_elapsed := 0.0
var _care_tex: Dictionary = {}
var _blob_y := 0.08

## Completion is one authored pass. CLIPS "next" is not followed.
## nuzzle's atlas loop flag is not an endless pat: one cycle, then idle or walk.
const CARE := {
	"eat": {"frames": 4, "fps": 8.0, "repeats": 1, "priority": 5, "interruptible": false},
	"nuzzle": {"frames": 6, "fps": 6.0, "repeats": 1, "priority": 4, "interruptible": true},
	"emo_happy": {"frames": 2, "fps": 4.0, "repeats": 4, "priority": 4, "interruptible": true},
	"emo_surprised": {"frames": 2, "fps": 6.0, "repeats": 1, "priority": 4, "interruptible": false},
}
const CARE_DIR := "res://tools/care_frame_review/frames/"


func setup(host: Node3D, body: Walker) -> void:
	main = host
	walker = body
	name = "Hd2dPresentation"
	process_priority = 20
	clip = WalkClip.new()
	coat = Sprite3D.new()
	coat.name = "Hd2dCoat"
	coat.pixel_size = 1.0
	coat.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	coat.alpha_cut = SpriteBase3D.ALPHA_CUT_OPAQUE_PREPASS
	coat.alpha_scissor_threshold = 0.5
	coat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	coat.shaded = true
	coat.double_sided = true
	coat.centered = true
	coat.position = Vector3(0.0, 29.0, 0.0)
	coat.offset = Vector2(0.0, WalkClip.GROUNDED_OFFSET_Y)
	coat.visible = false
	for path in WalkClip.frame_paths():
		var tex := Assets.load_texture(str(path))
		if tex != null:
			_tex[str(path)] = tex
	if walker:
		walker.add_child(coat)


func set_active(on: bool) -> void:
	active = on
	if coat:
		coat.visible = on
	if walker and walker.sprite:
		walker.sprite.visible = not on
	_set_face_sprites_visible(not on)
	var blob := walker.get_node_or_null("BlobShadow") if walker else null
	if blob:
		if on:
			_blob_y = blob.position.y
			blob.position.y = 0.25
		else:
			blob.position.y = _blob_y
	if on:
		_have_last = false
	else:
		_care_id = ""
		_release_brain()
		approaching = false


func begin_approach() -> bool:
	var requested := Hd2dDoor.exterior_anchor()
	requested_goal = requested
	nav_snapped = false
	var point := requested
	# The engineering stand can sit off the baked mesh. NavigationAgent only
	# paths to a point on the mesh. Snap to that closest point, and refuse
	# a snap that would cross the closed-door block line.
	if walker and walker.use_nav and walker.agent:
		var closest: Vector3 = NavigationServer3D.map_get_closest_point(walker.agent.get_navigation_map(), requested)
		closest.y = 0.0
		var gap := Vector2(closest.x, closest.z).distance_to(Vector2(requested.x, requested.z))
		if gap > 30.0 or closest.z <= Hd2dDoor.root_block_z():
			blocked_stop = true
			approaching = false
			arrived = false
			return false
		if gap > 0.05:
			nav_snapped = true
		point = closest
	return begin_approach_to(point)


func begin_approach_to(point: Vector3) -> bool:
	if walker == null:
		return false
	point.y = 0.0
	if not _stand_clear(point.x, point.z):
		blocked_stop = true
		approaching = false
		arrived = false
		return false
	blocked_stop = false
	arrived = false
	approaching = true
	goal = point
	_hold_brain()
	walker.pause_t = 0.0
	walker.go_to(point)
	return true


func cancel_approach() -> void:
	approaching = false
	arrived = false
	if walker:
		walker.pause_t = 30.0
		walker.go_to(walker.global_position)
	_release_brain()


func commit_enter() -> bool:
	if main == null or walker == null or not arrived:
		return false
	if not _stand_clear(walker.global_position.x, walker.global_position.z):
		return false
	approaching = false
	if main.has_method("enter_house"):
		main.enter_house(true)
	return bool(main.get("in_interior"))


func commit_exit() -> bool:
	if main == null or not bool(main.get("in_interior")):
		return false
	if main.has_method("exit_house"):
		main.exit_house(true)
	arrived = false
	approaching = false
	_release_brain()
	return not bool(main.get("in_interior"))


func _process(_dt: float) -> void:
	if not active or walker == null or coat == null:
		return
	_set_face_sprites_visible(false)
	var now := Vector2(walker.global_position.x, walker.global_position.z)
	if not _have_last:
		_last = now
		_have_last = true
	else:
		var view_right := Vector2(1.0, 0.0)
		var view_away := Vector2(0.0, -1.0)
		if main and main.get("cam") is Camera3D:
			var cam := main.get("cam") as Camera3D
			var right := cam.global_transform.basis.x
			var forward := -cam.global_transform.basis.z
			view_right = Vector2(right.x, right.z)
			view_away = Vector2(forward.x, forward.z)
			if view_right.length() > 0.001:
				view_right = view_right.normalized()
			if view_away.length() > 0.001:
				view_away = view_away.normalized()
		clip.advance(now - _last, view_right, view_away)
		_last = now
	if _care_id != "":
		_tick_care(_dt)
		return
	var mapped: String = str(clip.texture_path())
	var tex: Texture2D = _tex.get(mapped)
	if tex != null:
		coat.texture = tex
	coat.flip_h = bool(clip.flip_h)
	if not approaching:
		return
	if not _stand_clear(now.x, now.y):
		approaching = false
		arrived = false
		blocked_stop = true
		walker.pause_t = 30.0
		walker.go_to(walker.global_position)
		return
	if now.distance_to(Vector2(goal.x, goal.z)) <= Hd2dDoor.TARGET_DESIRED:
		approaching = false
		arrived = true
		walker.pause_t = 30.0


func _stand_clear(x: float, z: float) -> bool:
	if Hd2dDoor.root_blocked(x, z, Hd2dDoor.WALKER_RADIUS):
		return false
	if Hd2dDoor.pilot_blocked(Vector2(x, z), Hd2dDoor.pilot_props()):
		return false
	if walker and walker.feet and walker.feet.blocked(x, z, walker.radius):
		return false
	return true


func care_active() -> bool:
	return _care_id != ""


func care_id() -> String:
	return _care_id


func play_care(id: String) -> bool:
	if not CARE.has(id):
		push_error("unknown care clip " + id)
		return false
	if _care_id != "":
		var current: Dictionary = CARE[_care_id]
		var incoming: Dictionary = CARE[id]
		if int(incoming["priority"]) < int(current["priority"]):
			return false
		if not bool(current["interruptible"]) and int(incoming["priority"]) <= int(current["priority"]):
			return false
	if _care_tex.is_empty():
		var missing := _load_care_frames()
		if missing != "":
			push_error(missing)
			return false
	_care_id = id
	_care_elapsed = 0.0
	_show_care_frame(0)
	return true


func cancel_care() -> void:
	_care_id = ""
	_care_elapsed = 0.0


func _load_care_frames() -> String:
	for id in CARE.keys():
		var spec: Dictionary = CARE[id]
		var count := int(spec["frames"])
		for i in count:
			var path := CARE_DIR + "%s_%02d.png" % [id, i + 1]
			if not FileAccess.file_exists(path):
				return "care frame missing " + path
			var image := Image.new()
			if image.load(path) != OK:
				return "care frame failed to load " + path
			if image.get_width() != 64 or image.get_height() != 64:
				return "care frame is not 64x64 " + path
			var tex := ImageTexture.create_from_image(image)
			_care_tex["%s_%02d" % [id, i + 1]] = tex
	return ""


func _tick_care(dt: float) -> void:
	var spec: Dictionary = CARE[_care_id]
	var frame_len := 1.0 / float(spec["fps"])
	var total := int(spec["frames"]) * int(spec["repeats"]) * frame_len
	_care_elapsed += dt
	if _care_elapsed >= total:
		_care_id = ""
		_care_elapsed = 0.0
		var mapped: String = str(clip.texture_path())
		var tex: Texture2D = _tex.get(mapped)
		if tex != null:
			coat.texture = tex
		coat.flip_h = bool(clip.flip_h)
		return
	var index := int(floor(_care_elapsed / frame_len)) % int(spec["frames"])
	_show_care_frame(index)


func _show_care_frame(index: int) -> void:
	var key := "%s_%02d" % [_care_id, index + 1]
	var tex: Texture2D = _care_tex.get(key)
	if tex != null:
		coat.texture = tex
	coat.flip_h = false


func _set_face_sprites_visible(show: bool) -> void:
	if walker == null:
		return
	for child in walker.get_children():
		if str(child.name).begins_with("Face_"):
			child.visible = show


func _hold_brain() -> void:
	_brain = walker.get_node_or_null("PetBrain") if walker else null
	if _brain == null:
		return
	var tree: Node = _brain.get("tree")
	if tree:
		_tree_on = bool(tree.get("enabled"))
		tree.set("enabled", false)
	_brain.set("busy", true)


func _release_brain() -> void:
	if _brain == null:
		return
	var tree: Node = _brain.get("tree")
	if tree:
		tree.set("enabled", _tree_on)
	_brain.set("busy", false)
	_brain = null
