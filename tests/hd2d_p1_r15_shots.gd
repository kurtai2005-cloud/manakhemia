extends SceneTree
## Same-angle zone stills plus a frame strip of the door walk and the four-zone path.

const OUT := "/opt/cursor/artifacts/vc27_r15"
const FRAMES := "/tmp/r15_frames"
var _grab := false
var _frame := 0
var _approach_saved := false


func _initialize() -> void:
	DisplayServer.window_set_size(Vector2i(540, 1140))
	DirAccess.make_dir_recursive_absolute(OUT)
	DirAccess.make_dir_recursive_absolute(FRAMES)
	var main: Node = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	for _i in range(220):
		await process_frame
		if main.get_node_or_null("Phase1Hud") != null:
			break
	var p1: Node = root.get_node("Phase1")
	if bool(main.get("in_interior")):
		main.exit_house(true)
		await process_frame
	var sim: Node = root.get_node("Sim")
	var state: Dictionary = sim.get("state")
	state["phase1_inside"] = false
	sim.set("state", state)
	if p1.hud.modal and p1.hud.modal.visible:
		p1.close_modal()
	await process_frame
	_view(main, Vector3(12, 58, -26))
	await _still(OUT + "/r15_home.png")
	_view(main, Vector3(-410, 58, 20))
	await _still(OUT + "/r15_farm.png")
	_view(main, Vector3(410, 58, 20))
	await _still(OUT + "/r15_workshop.png")
	_view(main, Vector3(240, 58, -680))
	await _still(OUT + "/r15_prairie.png")
	var pet: Node3D = main.get("pet")
	pet.global_position = Vector3(0, 0, 30)
	_view(main, Vector3(40, 58, 10))
	_grab = true
	main.request_house_enter()
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 9000 and not bool(main.get("in_interior")):
		await _tick()
		if Time.get_ticks_msec() - start > 1200 and not _approach_saved:
			_approach_saved = true
			await _still(OUT + "/r15_door_approach.png")
	await _ms(500)
	await _still(OUT + "/r15_door_inside.png")
	main.request_house_exit()
	start = Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 6000 and bool(main.get("in_interior")):
		await _tick()
	await _ms(700)
	_view(main, Vector3(94, 58, -10))
	await _still(OUT + "/r15_door_outside.png")
	for look in [Vector3(12, 58, -26), Vector3(-410, 58, 20), Vector3(410, 58, 20), Vector3(240, 58, -680)]:
		var from: Vector3 = main.phase1_to
		var began := Time.get_ticks_msec()
		main.phase1_glide_to(look)
		while Time.get_ticks_msec() - began < 1600:
			await _tick()
		main.phase1_t = 1.0
		main.phase1_to = look
		main._place_cam(0.0)
		await _tick()
	_grab = false
	print("R15_FRAMES=", _frame)
	print("R15_SHOTS_DONE inside=", main.get("in_interior"), " pet=", pet.global_position)
	quit(0)


func _view(main: Node, look: Vector3) -> void:
	main.phase1_on = true
	main.phase1_from = look
	main.phase1_to = look
	main.phase1_t = 1.0
	main.follow_walker = null
	main._place_cam(0.0)


func _tick() -> void:
	await process_frame
	if not _grab:
		return
	if _frame % 2 != 0:
		_frame += 1
		return
	var img := root.get_viewport().get_texture().get_image()
	if img == null:
		return
	img.save_png(FRAMES + "/f%04d.png" % (_frame / 2))
	_frame += 1


func _still(path: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	if img == null:
		print("SHOT_EMPTY ", path)
		return
	if img.get_width() != 540 or img.get_height() != 1140:
		img = img.duplicate()
		img.resize(540, 1140, Image.INTERPOLATE_NEAREST)
	img.save_png(path)
	print("SHOT ", path)


func _ms(ms: int) -> void:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < ms:
		await _tick()
