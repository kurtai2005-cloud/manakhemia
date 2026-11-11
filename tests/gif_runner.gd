extends Node
## M1b 玩法預覽：viewport 逐幀出圖，再交 ffmpeg 轉 GIF。
## GODOT_M1B_GIF=hunt|work|collect|care|bubbles ；GODOT_M1B_FRAME_DIR=...

const FPS := 15
const SECS := 8.0

var _dir := "/tmp/m1b-gif-frames"
var _feat := "hunt"
var _main: Node
var _frame := 0
var _did1 := false
var _did2 := false
var _did3 := false


func _ready() -> void:
	_feat = str(OS.get_environment("GODOT_M1B_GIF"))
	if _feat == "":
		_feat = str(OS.get_environment("GODOT_M1A_GIF"))
	if _feat == "":
		_feat = "hunt"
	var d := str(OS.get_environment("GODOT_M1B_FRAME_DIR"))
	if d == "":
		d = str(OS.get_environment("GODOT_M1A_FRAME_DIR"))
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
	print("=== M1b gif ", _feat, " → ", _dir, " ===")
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
		"work":
			if _main.has_method("qa_overview"):
				_main.qa_overview()
		"collect":
			if _main.has_method("qa_overview"):
				_main.qa_overview()
			if CollectionSystem:
				CollectionSystem.add_shards(25, "old")
				CollectionSystem.notify("collection", true)
		"hunt":
			if _main.has_method("qa_overview"):
				_main.qa_overview()
		_:
			if _main.has_method("qa_overview"):
				_main.qa_overview()


func _tick_events(t: float) -> void:
	match _feat:
		"hunt":
			if t >= 0.4 and not _did1:
				_did1 = true
				if _main.has_method("start_hunt"):
					_main.start_hunt()
			if t >= 2.0 and HuntSystem:
				# 壓縮觀看：跳去撥草／撲
				HuntSystem.watch_elapsed = float(GameData.m1b.get("hunt", {}).get("watch_sec", 18)) * 0.2
			if t >= 5.5 and HuntSystem:
				HuntSystem.watch_elapsed = float(GameData.m1b.get("hunt", {}).get("watch_sec", 18)) * 0.7
		"work":
			if t >= 0.5 and not _did1:
				_did1 = true
				if _main.has_method("one_tap_dispatch"):
					_main.one_tap_dispatch()
			if t >= 2.0 and _main.has_method("qa_follow_pet"):
				_main.qa_follow_pet()
			if t >= 5.5 and WorkSystem and not _did2:
				_did2 = true
				for b in WorkSystem.buildings():
					WorkSystem.site(str(b.get("id", "")))["status"] = WorkSystem.ST_READY
					WorkSystem.site(str(b.get("id", "")))["watch"] = 99.0
				if _main.has_method("_sync_work_glow"):
					_main._sync_work_glow()
		"collect":
			if t >= 0.6 and not _did1:
				_did1 = true
				if CollectionSystem:
					CollectionSystem.buy("rug_leaf")
					CollectionSystem.place_recommended()
				if _main.has_method("refresh_furniture"):
					_main.refresh_furniture()
			if t >= 2.5 and not _did2:
				_did2 = true
				var hud: Node = _main.get("hud")
				if hud and hud.has_method("_toggle_book"):
					hud._toggle_book()
		"care":
			if t >= 1.0 and not _did1:
				_did1 = true
				if _main.has_method("qa_follow_pet"):
					_main.qa_follow_pet()
				var w: Walker = _main.pet if _main.get("pet") else null
				if _main.has_method("hand_feed"):
					_main.hand_feed(w, "meal")
			if t >= 3.5 and not _did2 and Sim:
				_did2 = true
				Sim.clean_all()
			if t >= 5.5 and not _did3:
				_did3 = true
				var w2: Walker = _main.pet if _main.get("pet") else null
				if _main.has_method("hand_pat"):
					_main.hand_pat(w2)
		"bubbles":
			if t >= 2.0 and _main.has_method("qa_follow_pet"):
				_main.qa_follow_pet()
