extends SceneTree

func _initialize() -> void:
	DisplayServer.window_set_size(Vector2i(540, 1140))
	var main: Node = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	for _i in range(180):
		await process_frame
		if main.get_node_or_null("Phase1Hud") != null:
			break
	var p1 := root.get_node("Phase1")
	await _shot("/opt/cursor/artifacts/p1r12_shot1_garden_ui.png")
	p1.open_feed()
	p1.feed("dew")
	await _mid()
	await _shot("/opt/cursor/artifacts/p1r12_shot2_feed_action.png")
	p1.clean()
	await _mid()
	await _shot("/opt/cursor/artifacts/p1r12_shot3_clean_action.png")
	p1.pat()
	await _mid()
	await _shot("/opt/cursor/artifacts/p1r12_shot4_pat_action.png")
	p1.train("力量")
	await _mid()
	await _shot("/opt/cursor/artifacts/p1r12_shot5_train_action.png")
	p1.go_zone("zone_farm")
	await _travel()
	p1.world.tap_bed(3)
	await _mid()
	await _shot("/opt/cursor/artifacts/p1r12_shot6_farm_action.png")
	p1.go_zone("zone_workshop")
	await _travel()
	p1.act_stove()
	await _mid()
	await _shot("/opt/cursor/artifacts/p1r12_shot7_workshop_action.png")
	p1.go_zone("prairie_edge")
	await _travel()
	p1.act_forage()
	await _mid()
	await _shot("/opt/cursor/artifacts/p1r12_shot8_prairie_action.png")
	p1.go_zone("garden")
	await _travel()
	p1.close_modal()
	p1.idle_hour()
	await process_frame
	await _shot("/opt/cursor/artifacts/p1r12_shot9_offline_modal.png")
	print("P1_SHOTS_DONE")
	quit(0)


func _mid() -> void:
	await _wait_ms(900)


func _travel() -> void:
	await _wait_ms(1800)


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
		copy.resize(540, 1140, Image.INTERPOLATE_BILINEAR)
		img = copy
	img.save_png(path)
	print("SHOT ", path, " ", img.get_width(), "x", img.get_height())
