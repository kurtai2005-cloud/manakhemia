extends Node
## First M1 slice on the vc27 pilot: observation + care.
## Art, shaders, and art_depth stay untouched. Icons are the original
## 32px M1 files (Nearest, integer scale). 64x56 V3 bubble frames are not used.
##
## Water / play are not wired. See the note at the bottom of this file.

const Rules := preload("res://gameplay/m1_input_rules.gd")
const Gesture := preload("res://gameplay/m1_gesture.gd")
const Fade := preload("res://gameplay/m1_ui_fade.gd")

const ICON_SCALE := 2
const POOP_SCALE := 2
const TOUCH := Vector2(96, 96)

var host: Node = null
var pets: Array[Node3D] = []
var origins: Dictionary = {}
var selected: Node3D = null
var overview := false
var gesture
var fade
var _ui_ready := false
var _care_bar: Control
var _fade_root: CanvasItem
var _btn_appreciate: Button
var _btn_feed: Button
var _btn_pat: Button
var _btn_one: Button
var _btn_all: Button
var _bubble: Sprite3D
var _poop_root: Node3D
var _poops: Array[Sprite3D] = []


func bind_host(p_host: Node) -> void:
	host = p_host
	gesture = Gesture.new()
	fade = Fade.new()
	fade.fade_sec = _fade_sec()
	var pet: Node3D = host.get("_pet") as Node3D
	if pet:
		_register(pet, host.get("_pet_origin_xz") as Vector3)
		selected = pet
	# Same boot as mainline Main._ready: a new egg save becomes sprout so
	# feed/pat are reachable, and one poop is placed so clean can be tried.
	if Sim:
		if str(Sim.state.get("stage", "egg")) == "egg" and Sim.has_method("force_stage"):
			Sim.force_stage("sprout")
		if int(Sim.state.get("poops", 0)) == 0 and Sim.has_method("add_poop"):
			Sim.add_poop()
	_build_ui()
	_build_bubble()
	_build_poops()
	if Sim and Sim.has_signal("poops_changed"):
		Sim.poops_changed.connect(func(_n): _sync_poops())
	_sync_poops()
	_ui_ready = true


func camera_overview() -> bool:
	return overview


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
	var kind: String = gesture.tick(dt)
	if kind != "":
		_dispatch(kind, gesture.last)
	fade.tick(dt)
	_apply_fade()
	_sync_buttons()
	_sync_bubble()


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


func _enter_follow(pet: Node3D) -> void:
	if pet == null:
		return
	selected = pet
	overview = false


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


func _build_ui() -> void:
	var layer := CanvasLayer.new()
	layer.name = "M1CareUi"
	layer.layer = 30
	add_child(layer)
	var font := _font()
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(root)
	_fade_root = root

	_btn_appreciate = Button.new()
	_btn_appreciate.text = "欣賞"
	_btn_appreciate.focus_mode = Control.FOCUS_NONE
	_btn_appreciate.anchor_left = 1.0
	_btn_appreciate.anchor_right = 1.0
	_btn_appreciate.anchor_top = 0.0
	_btn_appreciate.anchor_bottom = 0.0
	_btn_appreciate.offset_left = -200.0
	_btn_appreciate.offset_right = -24.0
	_btn_appreciate.offset_top = 88.0
	_btn_appreciate.offset_bottom = 160.0
	if font:
		_btn_appreciate.add_theme_font_override("font", font)
		_btn_appreciate.add_theme_font_size_override("font_size", 28)
	_btn_appreciate.pressed.connect(_on_appreciate)
	root.add_child(_btn_appreciate)

	_care_bar = HBoxContainer.new()
	_care_bar.anchor_left = 0.0
	_care_bar.anchor_right = 1.0
	_care_bar.anchor_top = 1.0
	_care_bar.anchor_bottom = 1.0
	_care_bar.offset_left = 24.0
	_care_bar.offset_right = -24.0
	_care_bar.offset_top = -220.0
	_care_bar.offset_bottom = -48.0
	_care_bar.alignment = BoxContainer.ALIGNMENT_CENTER
	_care_bar.add_theme_constant_override("separation", 18)
	_care_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_care_bar)
	_btn_feed = _icon_button("need_eat", "餵", font)
	_btn_pat = _icon_button("need_pet", "摸", font)
	_btn_one = _icon_button("poop", "執一", font)
	_btn_all = _icon_button("poop", "執晒", font)
	_btn_feed.pressed.connect(func(): _act_feed())
	_btn_pat.pressed.connect(func(): _act_pat())
	_btn_one.pressed.connect(func(): _act_clean_one())
	_btn_all.pressed.connect(func(): _act_clean_all())
	_care_bar.add_child(_btn_feed)
	_care_bar.add_child(_btn_pat)
	_care_bar.add_child(_btn_one)
	_care_bar.add_child(_btn_all)


func _icon_button(icon_id: String, tip: String, font: Font) -> Button:
	var b := Button.new()
	b.custom_minimum_size = TOUCH
	b.focus_mode = Control.FOCUS_NONE
	b.tooltip_text = tip
	b.flat = true
	var box := VBoxContainer.new()
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.alignment = BoxContainer.ALIGNMENT_CENTER
	box.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var rect := TextureRect.new()
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rect.texture = _icon(icon_id)
	rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	var tex_px := 32
	if rect.texture:
		tex_px = rect.texture.get_width()
	var shown := float(tex_px * (ICON_SCALE if icon_id != "poop" else POOP_SCALE))
	rect.custom_minimum_size = Vector2(shown, shown)
	box.add_child(rect)
	var lab := Label.new()
	lab.mouse_filter = Control.MOUSE_FILTER_IGNORE
	lab.text = tip
	lab.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if font:
		lab.add_theme_font_override("font", font)
		lab.add_theme_font_size_override("font_size", 22)
	box.add_child(lab)
	b.add_child(box)
	return b


func _icon(id: String) -> Texture2D:
	var path := "res://gameplay/icons/%s.png" % id
	if ResourceLoader.exists(path) or FileAccess.file_exists(path):
		var tex := load(path) as Texture2D
		return tex
	return null


func _font() -> Font:
	var path := "res://art/ui/GenWanMin2TC-R.subset.otf"
	if not ResourceLoader.exists(path) and not FileAccess.file_exists(path):
		return null
	var ff := FontFile.new()
	ff.load_dynamic_font(path)
	return ff


func _on_appreciate() -> void:
	fade.toggle_appreciate()
	_btn_appreciate.text = "顯示" if fade.appreciate else "欣賞"
	_apply_fade()


func _apply_fade() -> void:
	if _care_bar == null:
		return
	var a := float(fade.alpha)
	var hidden: bool = fade.appreciate
	_care_bar.visible = not hidden
	_care_bar.modulate = Color(1, 1, 1, a)
	var take: bool = (not hidden) and a > 0.2 and not overview
	_care_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for b in [_btn_feed, _btn_pat, _btn_one, _btn_all]:
		if b:
			b.mouse_filter = Control.MOUSE_FILTER_STOP if take else Control.MOUSE_FILTER_IGNORE


func _sync_buttons() -> void:
	if _care_bar == null:
		return
	_care_bar.visible = (not overview) and (not fade.appreciate)
	var poops := int(Sim.state.get("poops", 0)) if Sim else 0
	var hunger := 100.0
	var egg := true
	var sleeping := false
	if Sim:
		var n: Dictionary = Sim.state.get("needs", {})
		hunger = float(n.get("hunger", 100))
		egg = str(Sim.state.get("stage", "egg")) == "egg"
		sleeping = bool(Sim.state.get("sleeping", false))
	var full := hunger >= float(Sim.FEED_REFUSE_AT) if Sim else false
	_set_enabled(_btn_feed, not egg and not sleeping and not full)
	_set_enabled(_btn_pat, not egg)
	_set_enabled(_btn_one, poops > 0)
	_set_enabled(_btn_all, poops > 0)


func _set_enabled(b: Button, on: bool) -> void:
	if b == null:
		return
	b.disabled = not on
	b.modulate = Color(1, 1, 1, 1) if on else Color(1, 1, 1, 0.4)


func _act_feed() -> void:
	fade.note_input()
	if Sim:
		Sim.feed("meal")


func _act_pat() -> void:
	fade.note_input()
	if Sim:
		Sim.pat()


func _act_clean_one() -> void:
	fade.note_input()
	if Sim and int(Sim.state.get("poops", 0)) > 0:
		Sim.clean_one()


func _act_clean_all() -> void:
	fade.note_input()
	if Sim and int(Sim.state.get("poops", 0)) > 0:
		Sim.clean_all()


func _build_bubble() -> void:
	var pet := follow_subject()
	if pet == null:
		return
	_bubble = Sprite3D.new()
	_bubble.name = "NeedBubble"
	_bubble.pixel_size = 1.0
	_bubble.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_bubble.shaded = false
	_bubble.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	_bubble.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
	_bubble.alpha_scissor_threshold = 0.5
	_bubble.position = Vector3(0, 48, 0)
	_bubble.visible = false
	pet.add_child(_bubble)


func _sync_bubble() -> void:
	if _bubble == null or Sim == null:
		return
	var id := _need_id()
	if id == "":
		_bubble.visible = false
		return
	var tex := _icon(id)
	_bubble.texture = tex
	_bubble.visible = tex != null


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
	while _poops.size() < n:
		var spr := Sprite3D.new()
		spr.texture = _icon("poop")
		spr.pixel_size = float(POOP_SCALE)
		spr.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
		spr.shaded = false
		spr.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
		spr.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
		var i := _poops.size()
		var ang := TAU * float(i) / 5.0
		spr.position = Vector3(base.x + cos(ang) * 22.0, 8.0, base.z + sin(ang) * 22.0)
		_poop_root.add_child(spr)
		_poops.append(spr)
	while _poops.size() > n:
		var last: Sprite3D = _poops.pop_back()
		if last:
			last.queue_free()


# Water / play — not wired.
# data/sim.json care.rinse is 50 and Sim.RINSE loads it, but no call applies it.
# The comment groups rinse with other restore amounts and does not name the need.
# personality.json water_plants is only a 勤力 autonomous weight (1.3), not a player act.
# care.play_tease is 15 and is also loaded (Sim.PLAY_TEASE) with no player call.
# pat_mood is the wired "摸" amount. Do not invent a water or play delta.
