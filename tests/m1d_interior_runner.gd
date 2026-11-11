extends Node
## M1d preview GIFs：花園外觀、進出過渡、室內寵物（含 face-kit 照顧 clip）。
## GODOT_M1D_GIF=garden|enter_exit|interior   GODOT_M1D_FRAME_DIR=...

const FPS := 12

var _dir := "/tmp/m1d-int-frames"
var _feat := "garden"
var _main: Node
var _frame := 0


func _ready() -> void:
	_feat = str(OS.get_environment("GODOT_M1D_GIF"))
	if _feat == "":
		_feat = "garden"
	var d := str(OS.get_environment("GODOT_M1D_FRAME_DIR"))
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
	print("=== M1d interior gif ", _feat, " → ", _dir, " ===")
	QualitySettings.set_tier(QualitySettings.Tier.LOW)
	var packed: PackedScene = load("res://scenes/Main.tscn")
	if packed == null:
		printerr("FAIL Main.tscn")
		get_tree().quit(1)
		return
	_main = packed.instantiate()
	add_child(_main)
	await get_tree().process_frame
	await get_tree().process_frame
	if _main.has_method("set_shot_size"):
		_main.set_shot_size(390, 844)
	if TimeService:
		TimeService.use_fake(TimeService.local_wall_ms(12.0, 0.0))
	if _main.has_method("set_time_of_day"):
		_main.set_time_of_day("day")
	if CollectionSystem:
		if CollectionSystem.stardust() < 40:
			CollectionSystem.add_shards(40, "old")
		if not CollectionSystem.is_owned("rug_leaf"):
			CollectionSystem.buy("rug_leaf")
		if not CollectionSystem.is_owned("wall_shoes"):
			CollectionSystem.buy("wall_shoes")
		CollectionSystem.place("bed_leaf", "bed")
		CollectionSystem.place("rug_leaf", "rug")
		CollectionSystem.place("wall_shoes", "wall")
		if _main.has_method("refresh_furniture"):
			_main.refresh_furniture()
	match _feat:
		"garden":
			await _run_garden()
		"enter_exit":
			await _run_enter_exit()
		"interior":
			await _run_interior()
		"kid_walk":
			await _run_kid_walk()
		_:
			await _run_garden()
	print("GIF_FRAMES ", _frame, " feat=", _feat)
	get_tree().quit(0)


func _run_garden() -> void:
	if _main.has_method("set_rest_look"):
		_main.set_rest_look(true)
	if _main.has_method("qa_overview"):
		_main.qa_overview()
	if _main.has_method("qa_place_pet"):
		_main.qa_place_pet("default")
	# 花園外觀要見到屋同寵物；播 yawn 顯示 face-kit
	var pet: Walker = _main.get("pet")
	if pet:
		pet.brain_driven = false
		pet.pause_t = 0.2
	for i in range(8):
		await get_tree().process_frame
	var total := int(4.0 * float(FPS))
	for i in range(total):
		var t := float(i) / float(FPS)
		if t >= 1.2 and pet and pet.live_clip != "yawn" and pet.has_method("play_live_clip"):
			pet.play_live_clip("yawn")
		await _snap()


func _run_enter_exit() -> void:
	if _main.has_method("set_rest_look"):
		_main.set_rest_look(true)
	if _main.has_method("qa_overview"):
		_main.qa_overview()
	if _main.has_method("qa_place_pet"):
		_main.qa_place_pet("default")
	for i in range(6):
		await get_tree().process_frame
	var entered := false
	var exited := false
	# 入場約 1.1s，停留，出場 0.8s，再停留
	var total := int(5.5 * float(FPS))
	for i in range(total):
		var t := float(i) / float(FPS)
		if t >= 0.4 and not entered and _main.has_method("enter_house"):
			entered = true
			if _main.has_method("set_rest_look"):
				_main.set_rest_look(false)
			_main.enter_house(false, _main.get("pet"))
		if t >= 3.2 and not exited and _main.has_method("exit_house"):
			exited = true
			_main.exit_house(false)
		var pet: Walker = _main.get("pet")
		if pet and _main.get("in_interior") and t >= 1.8 and t < 3.0:
			if pet.live_clip == "" and pet.has_method("play_live_clip"):
				pet.play_live_clip("eat")
		await _snap()


func _run_interior() -> void:
	if _main.has_method("qa_overview"):
		_main.qa_overview()
	if _main.has_method("enter_house"):
		_main.enter_house(true, _main.get("pet"))
	for i in range(6):
		await get_tree().process_frame
	var pet: Walker = _main.get("pet")
	if pet:
		pet.in_interior = true
		pet.brain_driven = false
		if _main.get("interior_room") and pet.has_method("go_to"):
			pet.go_to(_main.interior_room.walk_point(_main.rng if _main.get("rng") else RandomNumberGenerator.new()))
	var total := int(5.0 * float(FPS))
	var did_eat := false
	var did_yawn := false
	for i in range(total):
		var t := float(i) / float(FPS)
		if pet and t >= 1.6 and not did_eat:
			did_eat = true
			if pet.has_method("play_live_clip"):
				pet.play_live_clip("eat")
		if pet and t >= 3.3 and not did_yawn:
			did_yawn = true
			if pet.has_method("play_live_clip"):
				pet.play_live_clip("yawn")
		if pet and t >= 0.3 and t < 1.5 and not pet.moving and _main.get("interior_room"):
			pet.go_to(_main.interior_room.walk_point(_main.rng if _main.get("rng") else RandomNumberGenerator.new()))
		await _snap()


func _run_kid_walk() -> void:
	# 細佬連續行 ≥10 秒，確認唔會變成團絨、腳唔會沉地
	if _main.has_method("set_rest_look"):
		_main.set_rest_look(true)
	if _main.has_method("qa_overview"):
		_main.qa_overview()
	var pet: Walker = _main.get("pet")
	var kid: Walker = _main.get("kid")
	var visitor: Walker = _main.get("visitor")
	if pet:
		pet.brain_driven = false
		pet.park()
		pet.visible = false
	if visitor:
		visitor.brain_driven = false
		visitor.park()
		visitor.visible = false
	if kid == null:
		printerr("FAIL no kid")
		return
	kid.brain_driven = false
	kid.walk_bob = false
	kid.stop_live()
	kid.speed = 20.0
	kid.global_position = Vector3(-20, 0, 70)
	kid.visible = true
	if _main.has_method("set_cam_follow"):
		_main.set_cam_follow(kid)
	if _main.has_method("set_rest_look"):
		_main.set_rest_look(true)
	var points: Array = [
		Vector3(40, 0, 70),
		Vector3(-30, 0, 80),
		Vector3(35, 0, 55),
		Vector3(-25, 0, 75),
		Vector3(45, 0, 65),
	]
	var pi := 0
	kid.go_to(points[0])
	var total := int(10.5 * float(FPS))
	for i in range(total):
		if not kid.moving and kid.live_clip == "":
			pi = (pi + 1) % points.size()
			kid.go_to(points[pi])
		# 若中途變咗團絨圖，仍然影低，報告時會見到
		await _snap()


func _snap() -> void:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var vp := get_viewport()
	if vp:
		var img := vp.get_texture().get_image()
		if img:
			img.save_png("%s/%s_%04d.png" % [_dir, _feat, _frame])
			_frame += 1
