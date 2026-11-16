extends Node
## Root-owned pet presentation and door approach.
## Does not instance capture.tscn, does not tick m1_roam, and does not save.
## The Walker remains the only body. Main remains the only camera and input.

const WalkClip := preload("res://godot_hd2d_v6/gameplay/m1_walk_clip.gd")

var active := false
var approaching := false
var arrived := false
var blocked_stop := false
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
		var use := str(path).replace("res://art/", "res://godot_hd2d_v6/art/")
		var tex := _load_png(use)
		if tex != null:
			_tex[str(path)] = tex
	if walker:
		walker.add_child(coat)


func _load_png(res_path: String) -> Texture2D:
	# The root project skips godot_hd2d_v6/ because that folder has its own
	# project.godot, so the imported Texture2D remap does not resolve here.
	# The PNG bytes are still on disk. This reads them without editing 675.
	var f := FileAccess.open(res_path, FileAccess.READ)
	if f == null:
		f = FileAccess.open(ProjectSettings.globalize_path(res_path), FileAccess.READ)
	if f == null:
		push_warning("hd2d presentation missing " + res_path)
		return null
	var img := Image.new()
	var err := img.load_png_from_buffer(f.get_buffer(f.get_length()))
	f.close()
	if err != OK:
		return null
	return ImageTexture.create_from_image(img)


func set_active(on: bool) -> void:
	active = on
	if coat:
		coat.visible = on
	if walker and walker.sprite:
		walker.sprite.visible = not on
	if on:
		_have_last = false
	else:
		_release_brain()
		approaching = false


func begin_approach() -> bool:
	return begin_approach_to(Hd2dDoor.exterior_anchor())


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
