extends Node
## 短跑：只出 m1a-care／m1a-family，避免同一次長煙測 OOM。

func _ready() -> void:
	# 等 root 完成 add_child，先至可以再掛 Main
	_boot()


func _boot() -> void:
	await get_tree().process_frame
	var d := str(OS.get_environment("GODOT_SHOT_DIR"))
	if d == "":
		d = "/home/box/keep/godot/M1a"
	DirAccess.make_dir_recursive_absolute(d)
	print("shots: start")
	QualitySettings.set_tier(QualitySettings.Tier.LOW)
	var packed: PackedScene = load("res://scenes/Main.tscn")
	if packed == null:
		printerr("FAIL Main.tscn")
		get_tree().quit(1)
		return
	var main: Node = packed.instantiate()
	print("shots: instanced")
	get_tree().root.add_child(main)
	print("shots: added")
	await get_tree().process_frame
	await get_tree().process_frame
	if main.has_method("set_shot_size"):
		main.set_shot_size(390, 844)
	if main.has_method("set_rest_look"):
		main.set_rest_look(true)
	if TimeService:
		TimeService.use_fake(TimeService.local_wall_ms(12.0, 0.0))
	if main.has_method("qa_overview"):
		main.qa_overview()
	if Sim:
		var n: Dictionary = Sim.state.get("needs", {})
		n["hunger"] = 40.0
		n["mood"] = 50.0
		Sim.state["needs"] = n
		Sim.state["poops"] = 2
		Sim.state["poop_age"] = [1.0, 2.0]
		Sim.state_changed.emit()
		Sim.feed("meal")
		Sim.pat()
		Sim.clean_all()
	for i in range(8):
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var vp := get_viewport()
	var img := vp.get_texture().get_image()
	if img:
		img.save_png("%s/m1a-care.png" % d)
		print("screenshot m1a-care ", img.get_width(), "x", img.get_height(), " ", img.get_data_size())
	if main.has_method("qa_overview"):
		main.qa_overview()
	if main.has_method("qa_family"):
		main.qa_family("walk_together")
	for i in range(8):
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	img = vp.get_texture().get_image()
	if img:
		img.save_png("%s/m1a-family.png" % d)
		print("screenshot m1a-family ", img.get_width(), "x", img.get_height(), " ", img.get_data_size())
	print("M1A_SHOTS_OK")
	get_tree().quit(0)
