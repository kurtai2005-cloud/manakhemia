extends SceneTree
## CLI capture for the room1 review fixture.
## Headless with ROOM1_GRAB=1 fails. It does not write a stand-in image.

var review: Node
var phase := "build"
var shot_i := 0
var shots: Array = []
var out_dir := ""
var grab := false


func _initialize() -> void:
	OS.set_environment("ROOM1_CAPTURE", "1")
	var udir := OS.get_user_data_dir()
	print("room1 user_dir=", udir)
	if OS.get_environment("ROOM1_REQUIRE_ISOLATED") == "1" and udir.find("room1_review_") < 0:
		print("FAIL user dir is not an isolated room1 review profile")
		quit(2)
		return
	grab = OS.get_environment("ROOM1_GRAB") == "1"
	out_dir = OS.get_environment("ROOM1_OUT")
	if grab and out_dir == "":
		print("FAIL ROOM1_OUT is required when grabbing")
		quit(1)
		return
	var packed := load("res://scenes/room1_review.tscn") as PackedScene
	if packed == null:
		print("FAIL room1 review scene missing")
		quit(1)
		return
	review = packed.instantiate()
	root.add_child(review)
	process_frame.connect(_on_frame)


func _on_frame() -> void:
	if phase == "build":
		if not review.has_method("build"):
			print("FAIL room1 review script did not load")
			quit(1)
			return
		var err: String = review.call("build")
		if err != "":
			print("FAIL ", err)
			_write_state(false)
			quit(1)
			return
		if not grab:
			if not _viewport_ok():
				print("FAIL viewport actual ", review.call("viewport_size"), " want 1080x2280")
				_write_state(false)
				quit(1)
				return
			_write_state(false)
			print("room1 load ok png_written=false renderer=", RenderingServer.get_current_rendering_method(), " viewport=", review.call("viewport_size"))
			quit(0)
			return
		if _display_blocked():
			print("FAIL display is headless; refusing to claim a review PNG")
			print("viewport_requested=1080x2280 viewport_actual=", review.call("viewport_size"))
			_write_state(false)
			quit(1)
			return
		if not _viewport_ok():
			print("FAIL viewport actual ", review.call("viewport_size"), " want 1080x2280")
			_write_state(false)
			quit(1)
			return
		shots = review.call("shot_plan")
		phase = "apply"
		return
	if phase == "apply":
		review.call("apply_shot", shots[shot_i])
		phase = "grab"
		return
	if phase == "grab":
		var img: Image = review.call("grab_image")
		var shot: Dictionary = shots[shot_i]
		var path := out_dir.path_join(str(shot["file"]))
		if not _viewport_ok():
			print("FAIL viewport drifted ", review.call("viewport_size"))
			_write_state(false)
			quit(1)
			return
		if not _png_ok(img, path):
			print("FAIL png ", shot["file"])
			_write_state(false)
			quit(1)
			return
		shot["png_written"] = true
		shot["png"] = path
		shots[shot_i] = shot
		shot_i += 1
		if shot_i >= shots.size():
			_write_state(true)
			print("room1 review pngs=", shot_i, " renderer=", RenderingServer.get_current_rendering_method())
			quit(0)
			return
		phase = "apply"


func _display_blocked() -> bool:
	return DisplayServer.get_name() == "headless" or OS.has_feature("headless")


func _viewport_ok() -> bool:
	var vp: Vector2i = review.call("viewport_size")
	return vp.x == 1080 and vp.y == 2280


func _png_ok(img: Image, path: String) -> bool:
	if img == null or img.is_empty():
		return false
	if img.get_width() != 1080 or img.get_height() != 2280:
		return false
	var dir := path.get_base_dir()
	if dir != "" and not DirAccess.dir_exists_absolute(dir):
		DirAccess.make_dir_recursive_absolute(dir)
	if img.save_png(path) != OK:
		return false
	var back := Image.new()
	if back.load(path) != OK:
		return false
	return back.get_width() == 1080 and back.get_height() == 2280 and not back.is_empty()


func _write_state(wrote_png: bool) -> void:
	var body: Dictionary = review.get("info")
	var vp: Vector2i = review.call("viewport_size")
	body["viewport_actual"] = [vp.x, vp.y]
	body["viewport_requested"] = [1080, 2280]
	body["viewport_configured"] = vp != Vector2i.ZERO
	body["grab_attempted"] = grab
	body["grab_rejected"] = grab and not wrote_png
	body["grab_rejected_before_viewport_configure"] = false
	body["renderer_actual"] = RenderingServer.get_current_rendering_method()
	body["driver"] = RenderingServer.get_current_rendering_driver_name()
	body["headless"] = _display_blocked()
	body["png_written"] = wrote_png
	body["shots"] = shots if shots.size() > 0 else review.call("shot_plan")
	if not wrote_png:
		for shot in body["shots"]:
			shot["png_written"] = false
			shot["png"] = ""
	var text := JSON.stringify(body, "\t")
	print("room1 state ", text)
	if out_dir == "":
		return
	DirAccess.make_dir_recursive_absolute(out_dir)
	var file := FileAccess.open(out_dir.path_join("room1_review_state.json"), FileAccess.WRITE)
	if file:
		file.store_string(text + "\n")
		file.close()
