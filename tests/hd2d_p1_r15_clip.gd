extends SceneTree
## Real enter/exit input, one simulation step per rendered frame.
## Software render is slow; time_scale keeps each step near 1/20s.
## Not a phone frame-rate measurement, and frames are not interpolated.

const OUT := "/tmp/r15_clip"
const STEP := 0.05
var _n := 0
var _grab := false
var _last_us := 0


func _initialize() -> void:
	DisplayServer.window_set_size(Vector2i(540, 1140))
	DirAccess.make_dir_recursive_absolute(OUT)
	var main: Node = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	for _i in range(220):
		await process_frame
		if main.get_node_or_null("Phase1Hud") != null:
			break
	var p1: Node = root.get_node("Phase1")
	if p1.hud.modal and p1.hud.modal.visible:
		p1.close_modal()
	if bool(main.get("in_interior")):
		main.exit_house(true)
		await process_frame
	var pet: Node3D = main.get("pet")
	pet.global_position = Vector3(20, 0, 36)
	if main.has_method("phase1_follow"):
		main.phase1_follow(pet)
	main._place_cam(0.0)
	_scale_log(pet, "YARD")
	_grab = true
	_last_us = Time.get_ticks_usec()
	Engine.time_scale = 1.0
	await _steps(8)
	main.request_house_enter()
	var guard := 0
	while guard < 400 and not bool(main.get("in_interior")):
		await _steps(1)
		guard += 1
	_scale_log(pet, "INSIDE")
	await _steps(14)
	main.request_house_exit()
	guard = 0
	while guard < 240 and bool(main.get("in_interior")):
		await _steps(1)
		guard += 1
	_scale_log(pet, "OUTSIDE")
	await _steps(10)
	_grab = false
	Engine.time_scale = 1.0
	print("CLIP_FRAMES=", _n, " inside=", main.get("in_interior"), " step=", STEP)
	quit(0)


func _scale_log(pet: Node3D, tag: String) -> void:
	var coat := pet.get_node_or_null("Hd2dCoat") as Sprite3D
	var px := coat.pixel_size if coat else -1.0
	print("PET_SCALE ", tag, " node=", pet.scale, " pixel_size=", px, " pos=", pet.global_position)


func _steps(count: int) -> void:
	for _i in count:
		await _tick()


func _tick() -> void:
	await process_frame
	var now := Time.get_ticks_usec()
	var wall := maxf(float(now - _last_us) / 1000000.0, 0.016)
	_last_us = now
	# Next rendered frame advances about one short simulation step.
	Engine.time_scale = clampf(STEP / wall, 0.01, 1.0)
	if not _grab:
		return
	var img := root.get_viewport().get_texture().get_image()
	if img == null:
		return
	if img.get_width() != 540 or img.get_height() != 1140:
		img = img.duplicate()
		img.resize(540, 1140, Image.INTERPOLATE_NEAREST)
	img.save_png(OUT + "/f%04d.png" % _n)
	_n += 1
