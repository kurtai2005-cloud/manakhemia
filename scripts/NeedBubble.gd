extends Node3D
class_name NeedBubble
## 寵物頭頂需要／表情泡泡。照顧值低（想要 ≥ threshold）先出需要 icon；撳／互動出表情。無文字。

var walker: Walker
var sprite: Sprite3D
var icon_id := ""
var threshold := 70.0

func _ready() -> void:
	var m1: Dictionary = GameData.m1a if GameData else {}
	var b: Dictionary = m1.get("bubbles", {})
	threshold = float(b.get("want_threshold", 70))
	sprite = Sprite3D.new()
	sprite.centered = true
	sprite.pixel_size = 0.35
	sprite.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	sprite.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
	sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	sprite.position = Vector3(0, 72, 0)
	sprite.visible = false
	add_child(sprite)


func attach(w: Walker) -> void:
	walker = w
	if walker:
		var h := 70.0
		if walker.frame_size.y > 0.0:
			h = walker.frame_size.y * maxf(walker.pixel_size, 1.0) + 10.0
		sprite.position = Vector3(0, h, 0)


func _process(_dt: float) -> void:
	if sprite == null:
		return
	var show_id := _pick()
	if show_id != icon_id:
		icon_id = show_id
		if icon_id == "":
			sprite.visible = false
			sprite.texture = null
		else:
			var tex: Texture2D = IconBank.tex(icon_id)
			sprite.texture = tex
			sprite.visible = tex != null


func _pick() -> String:
	# 表情優先（撳／互動緊）
	if walker:
		var brain: Node = walker.get_node_or_null("PetBrain")
		if brain and "expr_name" in brain and str(brain.expr_name) != "" and float(brain.expr_t) > 0.0:
			return str(brain.expr_name)
	# 只係主寵有照顧值；細佬／訪客跟主寵最高需要（家族一齊想）但淡啲——M1a 只喺主寵出需要泡泡
	if walker == null or str(walker.character) != "tuanrong":
		return ""
	var care: Dictionary = Sim.state.get("needs", {}) if Sim else {}
	# 想要值＝100−照顧值。對應想食／想摸／想玩／想瞓
	var wants := {
		"need_eat": 100.0 - float(care.get("hunger", 100)),
		"need_play": 100.0 - float(care.get("mood", 100)),
		"need_sleep": 100.0 - float(care.get("energy", 100)),
		"need_pet": 100.0 - float(care.get("mood", 100)) * 0.5 - float(care.get("clean", 100)) * 0.5,
	}
	# 清潔低時用 need_pet 唔夠清楚：清潔急用一個清潔／執屎意思——用 need 最高仍按 4 個需要 icon（清潔併入想摸／稍後再加清潔 icon）
	if float(care.get("clean", 100)) <= 30.0:
		wants["need_pet"] = maxf(float(wants["need_pet"]), 100.0 - float(care.get("clean", 100)))
	var best := ""
	var best_v := threshold - 0.01
	for k in wants.keys():
		if float(wants[k]) > best_v:
			best_v = float(wants[k])
			best = str(k)
	return best
