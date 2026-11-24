extends SceneTree

func _initialize() -> void:
	DisplayServer.window_set_size(Vector2i(540, 1140))
	var main: Node = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	for _i in range(180):
		await process_frame
		if main.get_node_or_null("Phase1Hud") != null:
			break
	await _shot("/opt/cursor/artifacts/p1_shot1_garden_clean.png")
	root.get_node("Phase1").go_zone("zone_farm")
	for _i in range(40):
		await process_frame
	print("LOOK ", main.follow_pos)
	await _shot("/opt/cursor/artifacts/p1_shot2_map_farm.png")
	root.get_node("Phase1").go_zone("zone_workshop")
	for _i in range(40):
		await process_frame
	await _shot("/opt/cursor/artifacts/p1_shot3_map_workshop.png")
	root.get_node("Phase1").go_zone("garden")
	for _i in range(40):
		await process_frame
	root.get_node("Phase1").open_feed()
	root.get_node("Phase1").feed("dew")
	root.get_node("Phase1").open_feed()
	await process_frame
	await _shot("/opt/cursor/artifacts/p1_shot4_feed_action.png")
	root.get_node("Phase1").idle_hour()
	await process_frame
	await _shot("/opt/cursor/artifacts/p1_shot5_offline_modal.png")
	root.get_node("Phase1").close_modal()
	root.get_node("Phase1").go_zone("prairie_edge")
	for _i in range(40):
		await process_frame
	await _shot("/opt/cursor/artifacts/p1_shot6_map_prairie.png")
	print("P1_SHOTS_DONE")
	quit(0)


func _shot(path: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	if img == null:
		print("SHOT_EMPTY ", path)
		return
	if img.get_width() != 540 or img.get_height() != 1140:
		img = img.duplicate()
		var canvas := Image.create(540, 1140, false, Image.FORMAT_RGBA8)
		canvas.fill(Color(0.53, 0.74, 0.88))
		var copy := img.duplicate()
		copy.resize(540, 1140, Image.INTERPOLATE_BILINEAR)
		canvas.blit_rect(copy, Rect2i(0, 0, 540, 1140), Vector2i.ZERO)
		img = canvas
	img.save_png(path)
	print("SHOT ", path, " ", img.get_width(), "x", img.get_height())
