extends Node
## Cycle the pet through idle/walk and every live action. Used for before/after GIFs.
## GODOT_ANIM_FRAME_DIR=...  (required)

const FPS := 12
const HOLD := 0.42

var _dir := "/tmp/m1d-anim-frames"
var _frame := 0
var walker: Walker
var cam: Camera3D


func _ready() -> void:
	var d := str(OS.get_environment("GODOT_ANIM_FRAME_DIR"))
	if d != "":
		_dir = d
	DirAccess.make_dir_recursive_absolute(_dir)
	var da := DirAccess.open(_dir)
	if da:
		da.list_dir_begin()
		var fn := da.get_next()
		while fn != "":
			if fn.ends_with(".png"):
				da.remove(fn)
			fn = da.get_next()
		da.list_dir_end()
	var win := get_window()
	if win:
		win.size = Vector2i(280, 360)
		win.content_scale_size = Vector2i(280, 360)
		win.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
		win.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_EXPAND
	print("=== M1d anim cycle → ", _dir, " ===")
	_build()
	await get_tree().process_frame
	await get_tree().process_frame
	var clips: Array = _clip_list()
	print("clips ", clips)
	for item in clips:
		var name := str(item[0])
		var kind := str(item[1])
		_start_clip(name, kind)
		var steps := maxi(3, int(HOLD * float(FPS)))
		for i in range(steps):
			if walker:
				walker._anim(1.0 / float(FPS))
			await get_tree().process_frame
			await RenderingServer.frame_post_draw
			_snap()
	print("ANIM_FRAMES ", _frame)
	get_tree().quit(0)


func _build() -> void:
	var world := Node3D.new()
	world.name = "AnimStage"
	add_child(world)
	# ground
	var ground := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(400, 400)
	ground.mesh = plane
	ground.rotation_degrees.x = 0
	# PlaneMesh is XY; rotate to XZ
	ground.rotation_degrees.x = -90
	ground.position.y = 0.0
	var gmat := StandardMaterial3D.new()
	gmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	gmat.albedo_color = Color(0.45, 0.72, 0.42)
	ground.material_override = gmat
	world.add_child(ground)
	# darker strip in front so feet vs grass are obvious, plus a bright foot rail at y=0
	var rail := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(90, 0.6, 2.0)
	rail.mesh = box
	rail.position = Vector3(0, 0.3, 4.0)
	var rmat := StandardMaterial3D.new()
	rmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	rmat.albedo_color = Color(0.95, 0.25, 0.2)
	rail.material_override = rmat
	world.add_child(rail)

	walker = Walker.new()
	walker.name = "Pet"
	walker.radius = 10.0
	walker.speed = 0.0
	walker.brain_driven = true
	walker.use_nav = false
	walker.pause_t = 1.0e9
	walker.moving = false
	world.add_child(walker)
	walker.position = Vector3(0, 0, 0)
	walker.setup(_load_dir4(), 1.0, Vector2(32, 61), Vector2(64, 64))
	walker.character = "tuanrong"
	walker.body_size = "L"
	walker.set_process(false)
	walker.set_physics_process(false)

	cam = Camera3D.new()
	cam.position = Vector3(0, 30, 150)
	cam.look_at(Vector3(0, 28, 0))
	cam.fov = 36
	world.add_child(cam)
	cam.current = true

	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-50, 30, 0)
	light.light_energy = 0.9
	world.add_child(light)


func _load_dir4() -> Dictionary:
	# same path as Main._load_dir4
	var DIR4 := "res://art/garden3d/dir4/"
	var doc: Dictionary = {}
	if Engine.has_singleton("GardenLoader") or true:
		if ResourceLoader.exists(DIR4 + "atlas_radiant_dir4.json") or FileAccess.file_exists(DIR4 + "atlas_radiant_dir4.json"):
			var raw := FileAccess.get_file_as_string(DIR4 + "atlas_radiant_dir4.json")
			var p: Variant = JSON.parse_string(raw)
			if p is Dictionary:
				doc = p
	var atlas: Texture2D = load(DIR4 + "atlas_radiant_dir4.png")
	var out := {}
	var frames: Dictionary = doc.get("frames", {})
	for name in frames.keys():
		var info: Dictionary = frames[name]
		var fr: Dictionary = info.get("frame", {})
		var at := AtlasTexture.new()
		at.atlas = atlas
		at.region = Rect2(float(fr.get("x", 0)), float(fr.get("y", 0)), float(fr.get("w", 64)), float(fr.get("h", 64)))
		at.filter_clip = true
		var clip := str(name).substr(0, name.rfind("_"))
		if not out.has(clip):
			out[clip] = []
		out[clip].append({"name": str(name), "tex": at})
	var sorted_out := {}
	for clip in out.keys():
		var arr: Array = out[clip]
		arr.sort_custom(func(a, b): return str(a["name"]) < str(b["name"]))
		var texs: Array = []
		for it in arr:
			texs.append(it["tex"])
		sorted_out[clip] = texs
	return sorted_out


func _clip_list() -> Array:
	# [name, kind]  kind=idle|walk|live
	var out: Array = [
		["front_idle", "idle"],
		["front_walk", "walk"],
		["side_walk", "walk"],
		["back_idle", "idle"],
	]
	var live := [
		"scratch", "sneeze", "sniff", "idle_quiet",
		"eat", "yawn", "fall_asleep", "sleep_loop", "wake",
		"sunbathe", "nuzzle", "rush", "walk_happy", "walk_drag",
		"play", "cheer_jump", "pounce", "cheer", "part_grass", "carry_fruit",
	]
	for n in live:
		if ArtImporter and ArtImporter.frames_of(n, "L", "tuanrong").size():
			out.append([n, "live"])
		elif ArtImporter and ArtImporter.frames_of(n, "L").size():
			out.append([n, "live"])
	return out


func _start_clip(name: String, kind: String) -> void:
	if walker == null:
		return
	walker.live_clip = ""
	walker.live_frames = []
	if walker.has_method("stop_live"):
		walker.stop_live()
	if kind == "walk":
		walker.moving = true
		walker.dir = "side" if name.begins_with("side") else ("back" if name.begins_with("back") else "front")
		walker.frame_i = 0
		walker.frame_t = 0.0
		walker._anim(0.0)
	elif kind == "idle":
		walker.moving = false
		walker.dir = "back" if name.begins_with("back") else "front"
		walker.frame_i = 0
		walker.frame_t = 0.0
		walker._anim(0.0)
	else:
		walker.moving = false
		walker.dir = "front"
		var ok := walker.play_live_clip(name, true)
		if not ok:
			print("skip ", name)
			walker._anim(0.0)


func _snap() -> void:
	var vp := get_viewport()
	if vp == null:
		return
	var img: Image = vp.get_texture().get_image()
	if img:
		# do not flip_y (Godot 4 OpenGL already upright)
		img.save_png("%s/anim_%04d.png" % [_dir, _frame])
		_frame += 1
