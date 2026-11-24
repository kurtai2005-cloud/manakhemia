extends SceneTree
## One continuous 19:9 software capture: door approach, entry, exit, then the
## camera travels across the farm and workshop. Not a phone frame-rate proof.

const OUT := "/tmp/r15_clip"
var _n := 0
var _grab := false


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
	pet.global_position = Vector3(8, 0, 48)
	if main.has_method("phase1_follow"):
		main.phase1_follow(pet)
	main._place_cam(0.0)
	_grab = true
	await _ms(350)
	main.request_house_enter()
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 12000 and not bool(main.get("in_interior")):
		await _tick()
	await _ms(800)
	main.request_house_exit()
	start = Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 8000 and bool(main.get("in_interior")):
		await _tick()
	await _ms(500)
	for look in [Vector3(12, 58, -26), Vector3(-180, 58, 10), Vector3(-410, 58, 20), Vector3(80, 58, 16), Vector3(410, 58, 20)]:
		var began := Time.get_ticks_msec()
		main.phase1_glide_to(look)
		while Time.get_ticks_msec() - began < 1600:
			await _tick()
	_grab = false
	print("CLIP_FRAMES=", _n, " inside=", main.get("in_interior"))
	quit(0)


func _tick() -> void:
	await process_frame
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


func _ms(ms: int) -> void:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < ms:
		await _tick()
