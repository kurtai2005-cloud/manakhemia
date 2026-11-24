extends SceneTree

func _initialize() -> void:
	DisplayServer.window_set_size(Vector2i(540, 1140))
	var main: Node = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	for _i in range(180):
		await process_frame
		if main.get_node_or_null("Phase1Hud") != null:
			break
	var p1: Node = root.get_node("Phase1")
	var hud: Phase1Hud = main.get_node("Phase1Hud")
	DirAccess.make_dir_recursive_absolute("/opt/cursor/artifacts/r13")
	await _shot("/opt/cursor/artifacts/r13/r13_shot1_home.png")
	p1.go_zone("zone_workshop")
	await _wait_ms(1800)
	await _shot("/opt/cursor/artifacts/r13/r13_shot2_workshop.png")
	p1.go_zone("prairie_edge")
	await _wait_ms(1800)
	await _shot("/opt/cursor/artifacts/r13/r13_shot3_prairie.png")
	p1.go_zone("garden")
	await _wait_ms(1800)
	p1.open_feed()
	await process_frame
	await _shot("/opt/cursor/artifacts/r13/r13_shot4_feed_row.png")
	p1.feed("dew")
	await _wait_ms(900)
	await _shot("/opt/cursor/artifacts/r13/r13_shot5_feed_action.png")
	p1.train("力量")
	await _wait_ms(900)
	await _shot("/opt/cursor/artifacts/r13/r13_shot6_train_action.png")
	p1.clean()
	await _wait_ms(900)
	await _shot("/opt/cursor/artifacts/r13/r13_shot7_clean_action.png")
	p1.open_info()
	await process_frame
	await _shot("/opt/cursor/artifacts/r13/r13_shot8_info.png")
	hud.set_collapsed(true)
	hud.apply_layout()
	await process_frame
	await _shot("/opt/cursor/artifacts/r13/r13_shot9_collapsed.png")
	print("R13_SHOTS_DONE")
	quit(0)


func _wait_ms(ms: int) -> void:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < ms:
		await process_frame


func _shot(path: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	if img == null:
		print("SHOT_EMPTY ", path)
		return
	if img.get_width() != 540 or img.get_height() != 1140:
		var copy := img.duplicate()
		copy.resize(540, 1140, Image.INTERPOLATE_NEAREST)
		img = copy
	img.save_png(path)
	print("SHOT ", path)
