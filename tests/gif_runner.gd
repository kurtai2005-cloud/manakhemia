extends Node
## M1a 玩法預覽：用 viewport 逐幀出圖，再交 ffmpeg 轉 GIF。
## 環境：GODOT_M1A_GIF=family|follow|bubbles|care ；GODOT_M1A_FRAME_DIR=...

const FPS := 15
const SECS := 8.0

var _dir := "/tmp/m1a-gif-frames"
var _feat := "family"
var _main: Node
var _frame := 0
var _followed := false
var _fed := false
var _cleaned := false
var _patted := false
var _fam2 := false


func _ready() -> void:
	_feat = str(OS.get_environment("GODOT_M1A_GIF"))
	if _feat == "":
		_feat = "family"
	var d := str(OS.get_environment("GODOT_M1A_FRAME_DIR"))
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
	print("=== M1a gif ", _feat, " → ", _dir, " ===")
	OS.set_environment("GODOT_M1A_DEMO", "1")
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
	if _main.has_method("set_rest_look"):
		_main.set_rest_look(true)
	if TimeService:
		TimeService.use_fake(TimeService.local_wall_ms(12.0, 0.0))
	_setup_feat()
	for i in range(4):
		await get_tree().process_frame
	var total := int(SECS * float(FPS))
	for i in range(total):
		var t := float(i) / float(FPS)
		_tick_events(t)
		await get_tree().process_frame
		await RenderingServer.frame_post_draw
		var vp := get_viewport()
		if vp:
			var img := vp.get_texture().get_image()
			if img:
				img.save_png("%s/%s_%04d.png" % [_dir, _feat, _frame])
				_frame += 1
	print("GIF_FRAMES ", _frame, " feat=", _feat)
	get_tree().quit(0)


func _setup_feat() -> void:
	match _feat:
		"follow":
			if _main.has_method("qa_overview"):
				_main.qa_overview()
		"bubbles":
			if _main.has_method("qa_overview"):
				_main.qa_overview()
			if _main.has_method("qa_force_needs"):
				_main.qa_force_needs(18.0, 88.0, 88.0, 88.0)
		"care":
			if _main.has_method("qa_overview"):
				_main.qa_overview()
			if Sim:
				var n: Dictionary = Sim.state.get("needs", {})
				n["hunger"] = 35.0
				n["mood"] = 40.0
				Sim.state["needs"] = n
				Sim.state["poops"] = 2
				Sim.state["poop_age"] = [1.0, 2.0]
				Sim.state_changed.emit()
		_:
			if _main.has_method("qa_overview"):
				_main.qa_overview()
			if _main.has_method("qa_family"):
				_main.qa_family("play_together")


func _tick_events(t: float) -> void:
	if _feat == "follow" and t >= 2.0 and not _followed:
		_followed = true
		if _main.has_method("qa_follow_pet"):
			_main.qa_follow_pet()
	elif _feat == "care":
		if t >= 1.2 and not _fed and Sim:
			_fed = true
			Sim.feed("meal")
		elif t >= 3.2 and not _cleaned and Sim:
			_cleaned = true
			Sim.clean_all()
		elif t >= 5.0 and not _patted and Sim:
			_patted = true
			Sim.pat()
			if _main.has_method("pet_all_react"):
				_main.pet_all_react()
	elif _feat == "family":
		if t >= 3.5 and not _fam2 and _main.has_method("qa_family"):
			_fam2 = true
			_main.qa_family("walk_together")
