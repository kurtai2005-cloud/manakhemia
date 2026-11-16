extends Node
## M1 observation + care on the vc27 pilot.
## UI art is gameplay/ui_r1 (art r1.1), used as supplied. Nearest, integer scale.
## The fourth control is the palm pat button and calls Sim.pat. It is not play.
## Water stays on the disabled art and does not change needs.
## Approved scene art, shaders, and art_depth are not edited here.

const Rules := preload("res://gameplay/m1_input_rules.gd")
const Gesture := preload("res://gameplay/m1_gesture.gd")
const Fade := preload("res://gameplay/m1_ui_fade.gd")
const Layout := preload("res://gameplay/m1_ui_layout.gd")
const M1ProfileRun := preload("res://gameplay/m1_profile_run.gd")

const UI_ROOT := "res://gameplay/ui_r1/assets/"

var host: Node = null
var pets: Array[Node3D] = []
var origins: Dictionary = {}
var selected: Node3D = null
var overview := false
var observe_close := false
var gesture
var fade
var _ui_ready := false
var _layer: CanvasLayer
var _fade_root: Control
var _bubble: TextureRect
var _hits: Dictionary = {}
var _pressed_id := ""
var _tex_cache: Dictionary = {}
var _poop_root: Node3D
var _poops: Array[Sprite3D] = []


func bind_host(p_host: Node) -> void:
	host = p_host
	gesture = Gesture.new()
	fade = Fade.new()
	fade.fade_sec = _fade_sec()
	_motion = OS.get_environment("HD2D_MOTION_RUN") == "1"
	var pet: Node3D = host.get("_pet") as Node3D
	if pet:
		_register(pet, host.get("_pet_origin_xz") as Vector3)
		selected = pet
	var phase := OS.get_environment("HD2D_PROFILE_PHASE")
	if phase == "verify":
		_build_ui()
		_apply_layout()
		_ui_ready = true
		M1ProfileRun.verify_and_quit(self)
		return
	if phase == "seed":
		M1ProfileRun.seed_fixture()
	elif phase == "visual":
		M1ProfileRun.visual_fixture(self)
	elif Sim:
		# Same boot as mainline Main._ready: a new egg save becomes sprout so
		# feed/pat are reachable, and one poop is placed so clean can be tried.
		if str(Sim.state.get("stage", "egg")) == "egg" and Sim.has_method("force_stage"):
			Sim.force_stage("sprout")
		if int(Sim.state.get("poops", 0)) == 0 and Sim.has_method("add_poop"):
			Sim.add_poop()
	_build_ui()
	_apply_layout()
	_build_poops()
	if Sim and Sim.has_signal("poops_changed"):
		Sim.poops_changed.connect(func(_n): _sync_poops())
	_sync_poops()
	_ui_ready = true


func camera_overview() -> bool:
	return overview


func follow_close() -> bool:
	return observe_close and not overview


func follow_subject() -> Node3D:
	if selected and is_instance_valid(selected):
		return selected
	return host.get("_pet") as Node3D if host else null


func subject_origin(subject: Node3D) -> Vector3:
	if subject and origins.has(subject):
		return origins[subject]
	if host:
		return host.get("_pet_origin_xz") as Vector3
	return Vector3.ZERO


func handle_event(event: InputEvent) -> void:
	if not _ui_ready:
		return
	if fade.appreciate and _is_press(event):
		# Admire hides every control, including itself. The next press only exits.
		fade.toggle_appreciate()
		fade.note_input()
		_apply_fade()
		return
	if event is InputEventScreenTouch:
		var st := event as InputEventScreenTouch
		if st.pressed:
			fade.note_input()
			gesture.down(st.position)
		else:
			_dispatch(gesture.up(st.position), st.position)
	elif event is InputEventScreenDrag:
		var drag := event as InputEventScreenDrag
		fade.note_input()
		_dispatch(gesture.move(drag.position), drag.position)
	elif event is InputEventMouseButton and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		var mb := event as InputEventMouseButton
		if mb.pressed:
			fade.note_input()
			gesture.down(mb.position)
		else:
			_dispatch(gesture.up(mb.position), mb.position)
	elif event is InputEventMouseMotion and gesture.pressed:
		var mm := event as InputEventMouseMotion
		_dispatch(gesture.move(mm.position), mm.position)


func _process(dt: float) -> void:
	if not _ui_ready:
		return
	_hold_roam()
	var kind: String = gesture.tick(dt)
	if kind != "":
		_dispatch(kind, gesture.last)
	fade.tick(dt)
	_apply_layout()
	_apply_fade()
	_sync_buttons()
	_sync_bubble()
	_maybe_ui_shots(dt)
	_maybe_motion(dt)
	if OS.get_environment("HD2D_PROFILE_PHASE") == "seed":
		M1ProfileRun.tick_seed(self, dt)
	elif OS.get_environment("HD2D_PROFILE_PHASE") == "visual":
		M1ProfileRun.tick_visual(self, dt)


func _dispatch(kind: String, screen_pos: Vector2) -> void:
	if kind == "":
		return
	var over := _pet_at(screen_pos) != null
	var poops := int(Sim.state.get("poops", 0)) if Sim else 0
	var act := Rules.action(kind, over, overview, poops, pets.size())
	match act:
		"follow":
			var pet := _pet_at(screen_pos)
			if pet == null and selected:
				pet = selected
			_enter_follow(pet)
		"overview":
			overview = true
			observe_close = false
		"walk":
			if host and host.has_method("_try_walk_tap"):
				host.call("_try_walk_tap", screen_pos)
		"clean_all":
			if Sim:
				Sim.clean_all()
		"cycle":
			_cycle(gesture.swipe_dir())
		"ignore":
			pass


func _hold_roam() -> void:
	# Care presses and appreciate pause stepping. They do not drop the target.
	# Follow / overview never come through here.
	if host == null:
		return
	var roam = host.get("_roam")
	if roam == null or not roam.has_method("set_care_hold"):
		return
	var down := gesture != null and bool(gesture.pressed)
	roam.set_care_hold(fade.appreciate or _pressed_id != "" or down)


func _enter_follow(pet: Node3D) -> void:
	if pet == null:
		return
	selected = pet
	overview = false
	observe_close = true


func _cycle(dir: float) -> void:
	if pets.size() < 2 or selected == null:
		return
	var i := pets.find(selected)
	if i < 0:
		i = 0
	var step := 1 if dir >= 0.0 else -1
	var n := pets.size()
	selected = pets[(i + step + n) % n]
	overview = false
	observe_close = true


func _register(pet: Node3D, origin: Vector3) -> void:
	if pets.find(pet) < 0:
		pets.append(pet)
	origins[pet] = origin


func _pet_at(screen_pos: Vector2) -> Node3D:
	var cam: Camera3D = host.get("_camera") as Camera3D if host else null
	if cam == null:
		return null
	var vp := cam.get_viewport().get_visible_rect().size
	var best: Node3D = null
	var best_d := 1.0e9
	for pet in pets:
		if pet == null or not is_instance_valid(pet):
			continue
		if cam.is_position_behind(pet.global_position):
			continue
		var sp := cam.unproject_position(pet.global_position)
		var d := sp.distance_to(screen_pos)
		var top := cam.unproject_position(pet.global_position + Vector3(0, 27, 0))
		var bot := cam.unproject_position(pet.global_position + Vector3(0, -27, 0))
		var rad := maxf(48.0, absf(bot.y - top.y) * 0.65)
		if d <= rad and d < best_d and sp.x >= -8.0 and sp.y >= -8.0 and sp.x <= vp.x + 8.0 and sp.y <= vp.y + 8.0:
			best = pet
			best_d = d
	return best


func _fade_sec() -> float:
	if GameData and GameData.m1a is Dictionary:
		return float((GameData.m1a as Dictionary).get("observe_ui_fade_sec", 3.0))
	return 3.0


func _want_threshold() -> float:
	if GameData and GameData.m1a is Dictionary:
		var b: Dictionary = (GameData.m1a as Dictionary).get("bubbles", {})
		return float(b.get("want_threshold", 70.0))
	return 70.0


func _is_press(event: InputEvent) -> bool:
	if event is InputEventScreenTouch:
		return (event as InputEventScreenTouch).pressed
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		return mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT
	return false


func _build_ui() -> void:
	_layer = CanvasLayer.new()
	_layer.name = "M1CareUi"
	_layer.layer = 30
	add_child(_layer)
	_fade_root = Control.new()
	_fade_root.name = "FadeRoot"
	_fade_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_fade_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_layer.add_child(_fade_root)
	for id in ["feed", "water", "poop", "pat", "admire"]:
		_hits[id] = _make_hit(id)
		_fade_root.add_child(_hits[id]["root"])
	_bubble = TextureRect.new()
	_bubble.name = "NeedBubble"
	_bubble.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_bubble.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_bubble.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_bubble.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_bubble.visible = false
	_layer.add_child(_bubble)
	if host and host.get_viewport():
		var vp := host.get_viewport()
		if not vp.size_changed.is_connected(_apply_layout):
			vp.size_changed.connect(_apply_layout)


func _make_hit(id: String) -> Dictionary:
	var root := Control.new()
	root.name = "Hit_%s" % id
	root.mouse_filter = Control.MOUSE_FILTER_STOP
	root.focus_mode = Control.FOCUS_NONE
	root.gui_input.connect(_on_hit_input.bind(id))
	var icon := TextureRect.new()
	icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	icon.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	root.add_child(icon)
	return {"root": root, "icon": icon}


func _apply_layout() -> void:
	if _fade_root == null:
		return
	var vp := _viewport_size()
	var layout := Layout.layout_scale(vp.x)
	var row: Dictionary = Layout.care_row(vp, layout)
	var disp := int(row["display"])
	var touch := int(row["touch"])
	for slot in row["slots"]:
		_place_hit(str(slot["id"]), slot["touch"], touch, slot["display"], disp)
	var admire: Dictionary = Layout.admire_slot(vp, layout)
	_place_hit("admire", admire["touch"], int(admire["size_touch"]), admire["display"], int(admire["size_display"]))
	var bubble := Layout.bubble_display(layout)
	if _bubble:
		_bubble.custom_minimum_size = Vector2(bubble, bubble)
		_bubble.size = Vector2(bubble, bubble)


func _place_hit(id: String, touch_pos: Vector2, touch: int, display_pos: Vector2, disp: int) -> void:
	var hit: Dictionary = _hits[id]
	var root: Control = hit["root"]
	var icon: TextureRect = hit["icon"]
	root.position = touch_pos
	root.size = Vector2(touch, touch)
	root.custom_minimum_size = Vector2(touch, touch)
	icon.position = display_pos - touch_pos
	icon.size = Vector2(disp, disp)
	icon.custom_minimum_size = Vector2(disp, disp)


func _viewport_size() -> Vector2:
	if host and host.get_viewport():
		return host.get_viewport().get_visible_rect().size
	return Vector2(1080, 1920)


func _on_hit_input(event: InputEvent, id: String) -> void:
	var press := false
	var release := false
	if event is InputEventMouseButton and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		press = (event as InputEventMouseButton).pressed
		release = not press
	elif event is InputEventScreenTouch:
		press = (event as InputEventScreenTouch).pressed
		release = not press
	else:
		return
	get_viewport().set_input_as_handled()
	if press:
		fade.note_input()
		if _allowed(id):
			_pressed_id = id
		_refresh_hit(id)
		return
	if release:
		var fire := _pressed_id == id and _allowed(id)
		if _pressed_id == id:
			_pressed_id = ""
		_refresh_hit(id)
		if fire:
			_run(id)


func _allowed(id: String) -> bool:
	if id == "water":
		return false
	if id == "admire":
		return true
	if Sim == null:
		return false
	var egg := str(Sim.state.get("stage", "egg")) == "egg"
	var sleeping := bool(Sim.state.get("sleeping", false))
	var hunger := float((Sim.state.get("needs", {}) as Dictionary).get("hunger", 100))
	var full := hunger >= float(Sim.FEED_REFUSE_AT)
	var poops := int(Sim.state.get("poops", 0))
	match id:
		"feed":
			return not egg and not sleeping and not full
		"pat":
			return not egg
		"poop":
			return poops > 0
	return false


func _run(id: String) -> void:
	fade.note_input()
	match Layout.effect(id):
		"feed":
			if Sim:
				Sim.feed("meal")
		"pat":
			if Sim:
				Sim.pat()
		"clean_one":
			if Sim and int(Sim.state.get("poops", 0)) > 0:
				Sim.clean_one()
		"appreciate":
			fade.toggle_appreciate()
			_apply_fade()
		"none":
			pass


func _tex(state_id: String, visual: String) -> Texture2D:
	var folder := "buttons/btn_admire_" if state_id == "admire" else "buttons/btn_care_%s_" % state_id
	return _tex_file(UI_ROOT + folder + visual + ".png")


func _tex_file(path: String) -> Texture2D:
	# Same PNG bytes as the file on disk. Cached so a care refresh does not
	# reopen the file every frame. load_png_from_buffer does not go through
	# the imported-resource path, which is what prints the export warning.
	if _tex_cache.has(path):
		return _tex_cache[path]
	if not FileAccess.file_exists(path):
		return null
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return null
	var img := Image.new()
	var err := img.load_png_from_buffer(f.get_buffer(f.get_length()))
	f.close()
	if err != OK:
		return null
	var tex := ImageTexture.create_from_image(img)
	_tex_cache[path] = tex
	return tex


func _refresh_hit(id: String) -> void:
	if not _hits.has(id):
		return
	var visual := "disabled"
	if _allowed(id):
		visual = "pressed" if _pressed_id == id else "normal"
	var icon: TextureRect = _hits[id]["icon"]
	icon.texture = _tex(id, visual)


func _sync_buttons() -> void:
	for id in _hits.keys():
		_refresh_hit(str(id))


func _apply_fade() -> void:
	if _fade_root == null:
		return
	var hidden: bool = fade.appreciate
	var alpha := float(fade.alpha)
	_fade_root.visible = not hidden
	_fade_root.modulate = Color(1, 1, 1, alpha)
	var take: bool = Layout.blocks_ground(not hidden, alpha)
	for id in _hits.keys():
		var root: Control = _hits[id]["root"]
		root.mouse_filter = Control.MOUSE_FILTER_STOP if take else Control.MOUSE_FILTER_IGNORE
	if _bubble:
		_bubble.modulate = Color(1, 1, 1, 0.0 if hidden else alpha)


func _sync_bubble() -> void:
	if _bubble == null or Sim == null or host == null:
		return
	if fade.appreciate:
		_bubble.visible = false
		return
	var id := _need_id()
	if id == "":
		_bubble.visible = false
		return
	var tex := _tex_file(UI_ROOT + "bubbles/bubble_%s.png" % id)
	_bubble.texture = tex
	_bubble.visible = tex != null and Layout.bubble_shown(id != "", fade.appreciate, float(fade.alpha))
	if not _bubble.visible:
		return
	var cam: Camera3D = host.get("_camera") as Camera3D
	var pet := follow_subject()
	if cam == null or pet == null:
		_bubble.visible = false
		return
	if cam.is_position_behind(pet.global_position):
		_bubble.visible = false
		return
	var layout := Layout.layout_scale(_viewport_size().x)
	var size := float(Layout.bubble_display(layout))
	# Head is the top of the visible sprite. The bubble's bottom-center
	# stays on that projected point, so walk and follow cannot leave a gap.
	var head := cam.unproject_position(pet.global_position + Vector3(0, 27, 0))
	_bubble.position = Layout.bubble_top_left(head, size)
	_bubble.size = Vector2(size, size)


func bubble_fits_at(world_xz: Vector2) -> bool:
	# Same head offset and bubble rect as _sync_bubble. Does not move anything.
	var cam: Camera3D = host.get("_camera") as Camera3D if host else null
	var pet: Node3D = host.get("_pet") as Node3D if host else null
	if cam == null or pet == null:
		return false
	var stand := Vector3(world_xz.x, pet.global_position.y, world_xz.y)
	if cam.is_position_behind(stand):
		return false
	var vp := _viewport_size()
	var size := float(Layout.bubble_display(Layout.layout_scale(vp.x)))
	var head := cam.unproject_position(stand + Vector3(0, 27, 0))
	var tl := Layout.bubble_top_left(head, size)
	if tl.x < 0.0 or tl.y < 0.0 or tl.x + size > vp.x or tl.y + size > vp.y:
		return false
	var ground := cam.unproject_position(Vector3(world_xz.x, 0.0, world_xz.y))
	return ground.x >= 0.0 and ground.y >= 0.0 and ground.x <= vp.x and ground.y <= vp.y


func _need_id() -> String:
	if Sim == null:
		return ""
	var care: Dictionary = Sim.state.get("needs", {})
	var wants := {
		"need_eat": 100.0 - float(care.get("hunger", 100)),
		"need_play": 100.0 - float(care.get("mood", 100)),
		"need_sleep": 100.0 - float(care.get("energy", 100)),
		"need_pet": 100.0 - float(care.get("mood", 100)) * 0.5 - float(care.get("clean", 100)) * 0.5,
	}
	if float(care.get("clean", 100)) <= 30.0:
		wants["need_pet"] = maxf(float(wants["need_pet"]), 100.0 - float(care.get("clean", 100)))
	var best := ""
	var best_v := _want_threshold() - 0.01
	for k in wants.keys():
		if float(wants[k]) > best_v:
			best_v = float(wants[k])
			best = str(k)
	return best


func _pet_box_wu() -> float:
	# The same 54-unit box capture.gd measures. Not a new pet scale.
	if host:
		var sc = host.get_script()
		if sc is GDScript and (sc as GDScript).get_script_constant_map().has("PET_VISIBLE_H"):
			return float((sc as GDScript).get_script_constant_map()["PET_VISIBLE_H"])
	return 54.0


func _build_poops() -> void:
	_poop_root = Node3D.new()
	_poop_root.name = "M1Poops"
	if host:
		host.add_child(_poop_root)


func _sync_poops() -> void:
	if _poop_root == null or Sim == null:
		return
	var n := int(Sim.state.get("poops", 0))
	var pet := host.get("_pet") as Node3D if host else null
	var base := pet.global_position if pet else Vector3.ZERO
	var tex := _tex_file(UI_ROOT + "icons/icon_care_poop_32.png")
	while _poops.size() < n:
		var spr := Sprite3D.new()
		spr.texture = tex
		var icon_px := 32.0
		if tex:
			icon_px = float(tex.get_height())
		var box := _pet_box_wu()
		var marker: Dictionary = Layout.poop_marker(box, icon_px)
		spr.pixel_size = float(marker["pixel_size"])
		spr.centered = true
		spr.offset = Vector2.ZERO
		spr.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
		spr.shaded = false
		spr.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
		spr.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
		var i := _poops.size()
		var ang := TAU * float(i) / 5.0
		spr.position = Vector3(base.x + cos(ang) * 22.0, float(marker["center_y"]), base.z + sin(ang) * 22.0)
		_poop_root.add_child(spr)
		_poops.append(spr)
	while _poops.size() > n:
		var last: Sprite3D = _poops.pop_back()
		if last:
			last.queue_free()


var _shot_t := 0.0
var _shot_i := 0
var _motion := false
var _motion_t := 0.0
var _motion_n := 0
var _hold_until := -1.0
var _hold_pos := Vector2.ZERO


func _maybe_motion(dt: float) -> void:
	# Deterministic input for a GPU reviewer. Real viewport events only.
	# This does not call Sim.feed / pat / clean_one itself.
	if not _motion or host == null:
		return
	_motion_t += dt
	if _hold_until >= 0.0 and _motion_t >= _hold_until:
		_pointer(_hold_pos, false)
		_hold_until = -1.0
		print("motion release longpress t=", snapped(_motion_t, 0.01))
	_motion_shot()
	var mark := _motion_n
	if mark == 0 and _motion_t >= 0.4:
		_log_chrome("day_idle")
		_log_brown("day_idle")
		_motion_n = 1
	elif mark == 1 and _motion_t >= 0.7:
		_pointer(_ground_point(), true)
		_pointer(_ground_point(), false)
		print("motion tap empty (leave follow or walk)")
		_motion_n = 2
	elif mark == 2 and _motion_t >= 1.1:
		_pointer(_ground_point(), true)
		_pointer(_ground_point(), false)
		print("motion tap empty again")
		_motion_n = 3
	elif mark == 3 and _motion_t >= 2.2:
		_log_brown("while_walking")
		_pointer(_pet_point(), true)
		_pointer(_pet_point(), false)
		print("motion tap pet")
		_motion_n = 4
	elif mark == 4 and _motion_t >= 3.0:
		_log_brown("during_follow")
		_pointer(_ground_point(), true)
		_pointer(_ground_point(), false)
		print("motion tap empty return")
		_motion_n = 5
	elif mark == 5 and _motion_t >= 3.4:
		var feed_at := _button_center(0)
		_pointer(feed_at, true)
		_pointer(feed_at, false)
		print("motion tap feed button hunger_now=", _hunger_now())
		_motion_n = 6
	elif mark == 6 and _motion_t >= 3.8:
		var pat_at := _button_center(3)
		_pointer(pat_at, true)
		_pointer(pat_at, false)
		print("motion tap pat button hunger_now=", _hunger_now(), " poops=", _poop_count())
		_motion_n = 7
	elif mark == 7 and _motion_t >= 4.2:
		_hold_pos = _ground_point()
		_pointer(_hold_pos, true)
		_hold_until = _motion_t + 0.6
		print("motion longpress down")
		_motion_n = 8
	elif mark == 8 and _motion_t >= 5.2:
		var a := Vector2(180, 420)
		var b := Vector2(280, 424)
		_pointer(a, true)
		_motion_move(b)
		_pointer(b, false)
		print("motion swipe")
		_motion_n = 9
	elif mark == 9 and _motion_t >= 9.0:
		_log_chrome("after_fade")
		var admire := _admire_center()
		_pointer(admire, true)
		_pointer(admire, false)
		print("motion tap appreciate")
		_motion_n = 10
	elif mark == 10 and _motion_t >= 9.4:
		_key_n()
		print("motion night key")
		_motion_n = 11
	elif mark == 11 and _motion_t >= 10.0:
		_log_chrome("night")
		_log_brown("night")
		print("motion done")
		get_tree().quit(0)


func _motion_shot() -> void:
	var every := 0.25
	var slot := int(_motion_t / every)
	if slot == _motion_saved_slot:
		return
	_motion_saved_slot = slot
	_save_view("m%02d" % slot)


var _motion_saved_slot := -1


func _pointer(pos: Vector2, pressed: bool) -> void:
	var ev := InputEventMouseButton.new()
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.pressed = pressed
	ev.position = pos
	ev.global_position = pos
	var vp := get_viewport()
	if vp:
		vp.push_input(ev)


func _motion_move(pos: Vector2) -> void:
	var ev := InputEventMouseMotion.new()
	ev.position = pos
	ev.global_position = pos
	ev.relative = Vector2(40, 0)
	var vp := get_viewport()
	if vp:
		vp.push_input(ev)


func _key_n() -> void:
	var ev := InputEventKey.new()
	ev.keycode = KEY_N
	ev.pressed = true
	var vp := get_viewport()
	if vp:
		vp.push_input(ev)


func _pet_point() -> Vector2:
	var cam: Camera3D = host.get("_camera") as Camera3D
	var pet: Node3D = host.get("_pet") as Node3D
	if cam == null or pet == null:
		return Vector2(270, 570)
	return cam.unproject_position(pet.global_position)


func _ground_point() -> Vector2:
	var vp := _viewport_size()
	return Vector2(vp.x * 0.50, vp.y * 0.42)


func _button_center(index: int) -> Vector2:
	var row: Dictionary = Layout.care_row(_viewport_size(), Layout.layout_scale(_viewport_size().x))
	var slot: Dictionary = (row["slots"] as Array)[index]
	var disp: Vector2 = slot["display"]
	var size := float(row["display"])
	return disp + Vector2(size * 0.5, size * 0.5)


func _admire_center() -> Vector2:
	var slot: Dictionary = Layout.admire_slot(_viewport_size(), Layout.layout_scale(_viewport_size().x))
	var disp: Vector2 = slot["display"]
	var size := float(slot["size_display"])
	return disp + Vector2(size * 0.5, size * 0.5)


func _log_chrome(tag: String) -> void:
	var q := host.find_child("QualityBtn", true, false)
	var g := host.find_child("GradeBtn", true, false)
	var d := host.find_child("DevToggle", true, false)
	var e := host.find_child("DevEntry", true, false)
	var fps := host.find_child("FpsLabel", true, false)
	print("motion chrome ", tag,
		" quality=", q.visible if q else "missing",
		" grade=", g.visible if g else "missing",
		" dev_toggle=", d.visible if d else "missing",
		" entry=", e.visible if e else "missing",
		" fps=", fps.visible if fps else "missing")


func _hunger_now() -> float:
	if Sim == null:
		return -1.0
	return float((Sim.state.get("needs", {}) as Dictionary).get("hunger", -1))


func _poop_count() -> int:
	if Sim == null:
		return -1
	return int(Sim.state.get("poops", -1))


func _log_brown(tag: String) -> void:
	var pet: Node3D = host.get("_pet") as Node3D
	var px := pet.global_position if pet else Vector3.ZERO
	var bits := ""
	for spr in _poops:
		if spr:
			bits += " poop=%s" % spr.global_position
	print("motion brown ", tag, " pet=", px, bits)


func _maybe_ui_shots(dt: float) -> void:
	# Opt-in frame dump for a machine that can actually rasterize.
	# Does not move the camera or change quality.
	if OS.get_environment("HD2D_UI_SHOT") != "1":
		return
	_shot_t += dt
	if _shot_i == 0 and _shot_t >= 0.35:
		if Sim:
			var needs: Dictionary = Sim.state.get("needs", {})
			needs["hunger"] = 20.0
			Sim.state["needs"] = needs
		_save_view("01_observe")
		_shot_i = 1
	elif _shot_i == 1 and _shot_t >= 0.7:
		if Sim:
			Sim.feed("meal")
		_sync_buttons()
		_sync_bubble()
		_save_view("02_feed")
		_shot_i = 2
	elif _shot_i == 2 and _shot_t >= 1.05:
		if Sim:
			Sim.pat()
		_sync_buttons()
		_save_view("03_pat")
		_shot_i = 3
	elif _shot_i == 3 and _shot_t >= 1.4:
		if Sim and int(Sim.state.get("poops", 0)) > 0:
			Sim.clean_one()
		_sync_buttons()
		_sync_poops()
		_save_view("04_clean")
		_shot_i = 4
	elif _shot_i == 4 and _shot_t >= 1.7:
		get_tree().quit(0)


func _save_view(stem: String) -> void:
	var out := OS.get_environment("HD2D_UI_OUT")
	if out == "":
		out = "/tmp/vc27_ui_shot"
	DirAccess.make_dir_recursive_absolute(out)
	var vp := get_viewport()
	if vp == null:
		print("ui shot missing viewport")
		return
	var img := vp.get_texture().get_image()
	if img == null:
		print("ui shot null image ", stem)
		return
	var path := out.path_join(stem + ".png")
	var err := img.save_png(path)
	var hunger := -1.0
	var poops := -1
	if Sim:
		hunger = float((Sim.state.get("needs", {}) as Dictionary).get("hunger", -1))
		poops = int(Sim.state.get("poops", -1))
	print("ui shot ", path, " ", img.get_width(), "x", img.get_height(), " err=", err, " hunger=", hunger, " poops=", poops, " bubble=", _bubble.visible if _bubble else false)


# Water: btn_care_water_* is shown disabled. Sim.RINSE is 50 and is not applied.
# The data comment does not name which need rinse restores.
# Play: the palm button is pat (Sim.pat / pat_mood). play_tease stays unwired.
