extends Node3D
class_name NeedBubble
## 寵物頭頂需要／表情泡泡。照顧值低（想要 ≥ threshold）先出需要 icon；撳／互動出表情。無文字。
## M1c：遊美 V3-A 單格 bubble_need_*.png（金幼線＋深藍磨砂），唔再用米色圓底。HUD need_*.png 唔改。

var walker: Walker
var sprite: Sprite3D
var icon_id := ""
var threshold := 70.0
var _bob_t := 0.0
var _base_y := 72.0
var pixel_sz := 0.62
var bob_amp := 6.0
var bob_hz := 0.85
var tail_px := 26.0
var head_gap := 6.0


func _ready() -> void:
	if sprite != null:
		return
	var m1: Dictionary = {}
	if GameData:
		if "m1c" in GameData and not GameData.m1c.is_empty():
			m1 = GameData.m1c
		elif "m1b" in GameData and not GameData.m1b.is_empty():
			m1 = GameData.m1b
		elif "m1a" in GameData:
			m1 = GameData.m1a
	var b: Dictionary = m1.get("bubbles", {})
	if b.is_empty() and GameData and "m1b" in GameData:
		b = GameData.m1b.get("bubbles", {})
	threshold = float(b.get("want_threshold", 70))
	pixel_sz = float(b.get("pixel_size", 0.62))
	bob_amp = float(b.get("bob_amp", 6.0))
	bob_hz = float(b.get("bob_hz", 0.85))
	tail_px = float(b.get("tail_px", 26))
	head_gap = float(b.get("offset_above_head", 6))
	sprite = Sprite3D.new()
	sprite.centered = true
	sprite.pixel_size = pixel_sz
	sprite.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	sprite.shaded = false
	sprite.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
	sprite.alpha_scissor_threshold = 0.5
	sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	sprite.modulate = Color(1, 1, 1, 1)
	sprite.render_priority = 2
	sprite.no_depth_test = true
	sprite.double_sided = true
	sprite.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	sprite.visible = false
	add_child(sprite)
	_place_y()


func _need_tex(nid: String) -> Texture2D:
	# 預合成框+icon；唔好再用 HUD 嘅 IconBank need_*.png
	var path := "res://art/m1-icons/bubble_%s.png" % nid
	if ResourceLoader.exists(path) or FileAccess.file_exists(path):
		return load(path)
	return null


func attach(w: Walker) -> void:
	walker = w
	_place_y()


func _place_y() -> void:
	var h := 70.0
	if walker:
		if walker.has_method("visible_world_top"):
			h = walker.visible_world_top() + head_gap + tail_px * pixel_sz
		elif walker.frame_size.y > 0.0:
			h = walker.frame_size.y * maxf(walker.pixel_size, 1.0) + head_gap + tail_px * pixel_sz
	_base_y = h
	if sprite:
		sprite.position = Vector3(0, h, 0)


func _process(dt: float) -> void:
	if sprite == null:
		return
	var show_id := _pick()
	if show_id != icon_id:
		var appeared := icon_id == "" and show_id.begins_with("need_")
		icon_id = show_id
		if icon_id == "":
			sprite.visible = false
			sprite.texture = null
		else:
			var tex: Texture2D = null
			if icon_id.begins_with("need_"):
				tex = _need_tex(icon_id)
			if tex == null and IconBank:
				tex = IconBank.tex(icon_id)
			sprite.texture = tex
			sprite.visible = tex != null
			sprite.modulate = Color(1, 1, 1, 1)
			if appeared and sprite.visible and AudioManager and AudioManager.has_method("play_need_warning"):
				var pid := ""
				if walker:
					pid = str(walker.character)
				AudioManager.play_need_warning(pid)
			_place_y()
	_bob_t += dt
	var bob := sin(_bob_t * TAU * bob_hz) * bob_amp
	if sprite and sprite.visible:
		sprite.position.y = _base_y + bob


func _pick() -> String:
	if walker:
		var brain: Node = walker.get_node_or_null("PetBrain")
		if brain and "expr_name" in brain and str(brain.expr_name) != "" and float(brain.expr_t) > 0.0:
			return str(brain.expr_name)
	if walker == null or str(walker.character) != "tuanrong":
		return ""
	var care: Dictionary = Sim.state.get("needs", {}) if Sim else {}
	var wants := {
		"need_eat": 100.0 - float(care.get("hunger", 100)),
		"need_play": 100.0 - float(care.get("mood", 100)),
		"need_sleep": 100.0 - float(care.get("energy", 100)),
		"need_pet": 100.0 - float(care.get("mood", 100)) * 0.5 - float(care.get("clean", 100)) * 0.5,
	}
	if float(care.get("clean", 100)) <= 30.0:
		wants["need_pet"] = maxf(float(wants["need_pet"]), 100.0 - float(care.get("clean", 100)))
	var best := ""
	var best_v := threshold - 0.01
	for k in wants.keys():
		if float(wants[k]) > best_v:
			best_v = float(wants[k])
			best = str(k)
	return best
