extends Node3D
class_name NeedBubble
## 寵物頭頂需要／表情泡泡。照顧值低（想要 ≥ threshold）先出需要 icon；撳／互動出表情。無文字。
## M1b：更大、有底、上下浮；出現時播 sfx_need_warning（欣賞模式靜音）。

var walker: Walker
var sprite: Sprite3D
var back: Sprite3D
var icon_id := ""
var threshold := 70.0
var _bob_t := 0.0
var _base_y := 72.0
var pixel_sz := 0.62
var bob_amp := 6.0
var bob_hz := 0.85


func _ready() -> void:
	var m1: Dictionary = {}
	if GameData:
		if "m1b" in GameData and not GameData.m1b.is_empty():
			m1 = GameData.m1b
		elif "m1a" in GameData:
			m1 = GameData.m1a
	var b: Dictionary = m1.get("bubbles", GameData.m1a.get("bubbles", {}) if GameData else {})
	threshold = float(b.get("want_threshold", 70))
	pixel_sz = float(b.get("pixel_size", 0.62))
	bob_amp = float(b.get("bob_amp", 6.0))
	bob_hz = float(b.get("bob_hz", 0.85))
	back = Sprite3D.new()
	back.centered = true
	back.pixel_size = pixel_sz * 1.15
	back.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	back.alpha_cut = SpriteBase3D.ALPHA_CUT_DISABLED
	back.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	back.texture = _backdrop()
	back.modulate = Color(0.12, 0.08, 0.05, 0.55)
	back.visible = false
	add_child(back)
	sprite = Sprite3D.new()
	sprite.centered = true
	sprite.pixel_size = pixel_sz
	sprite.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	sprite.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
	sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	sprite.modulate = Color(1.15, 1.12, 1.05, 1.0)
	sprite.visible = false
	add_child(sprite)
	_place_y()


func _backdrop() -> Texture2D:
	var img := Image.create(48, 48, false, Image.FORMAT_RGBA8)
	var c := Vector2(23.5, 23.5)
	for y in range(48):
		for x in range(48):
			var d := Vector2(float(x), float(y)).distance_to(c) / 22.0
			var a := 1.0 if d <= 1.0 else 0.0
			if d > 0.82:
				img.set_pixel(x, y, Color(0.18, 0.1, 0.05, a * 0.95))
			else:
				img.set_pixel(x, y, Color(1.0, 0.97, 0.88, a))
	return ImageTexture.create_from_image(img)


func attach(w: Walker) -> void:
	walker = w
	_place_y()


func _place_y() -> void:
	var h := 70.0
	if walker:
		if walker.has_method("visible_world_top"):
			h = walker.visible_world_top() + 14.0
		elif walker.frame_size.y > 0.0:
			h = walker.frame_size.y * maxf(walker.pixel_size, 1.0) + 10.0
	_base_y = h
	if sprite:
		sprite.position = Vector3(0, h, 0)
	if back:
		back.position = Vector3(0, h, -0.4)


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
			if back:
				back.visible = false
		else:
			var tex: Texture2D = IconBank.tex(icon_id) if IconBank else null
			sprite.texture = tex
			sprite.visible = tex != null
			if back:
				back.visible = sprite.visible
			if appeared and sprite.visible and AudioManager and AudioManager.has_method("play_need_warning"):
				var pid := ""
				if walker:
					pid = str(walker.character)
				AudioManager.play_need_warning(pid)
	_bob_t += dt
	var bob := sin(_bob_t * TAU * bob_hz) * bob_amp
	if sprite and sprite.visible:
		sprite.position.y = _base_y + bob
		if back:
			back.position.y = _base_y + bob


func _pick() -> String:
	# 表情優先（撳／互動緊）
	if walker:
		var brain: Node = walker.get_node_or_null("PetBrain")
		if brain and "expr_name" in brain and str(brain.expr_name) != "" and float(brain.expr_t) > 0.0:
			return str(brain.expr_name)
	# 只係主寵有照顧值；M1 只喺主寵出需要泡泡
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
