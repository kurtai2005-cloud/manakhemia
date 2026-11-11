extends CanvasLayer
## M1a HUD：底部一鍵（餵／執屎／摸）、總結卡（icon＋數字），頭頂需要改由 3D 泡泡。無長文字。

var font: Font
var root: Control
var hide_btn: Button
var dev_btn: Button
var dev_panel: PanelContainer
var hidden := false
var bar: HBoxContainer
var btn_feed: Button
var btn_clean: Button
var btn_pat: Button
var card: PanelContainer
var card_row: HBoxContainer
var card_t := 0.0
var card_queue: Array = []
var observing := false  # 跟拍觀察中：總結卡排隊
var time_lbl: Label
var stage_dot: TextureRect  # 唔用長文字需求列

func _ready() -> void:
	layer = 20
	font = load("res://art/fonts/GenWanMin2TC-R.subset.otf")
	root = Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)

	time_lbl = _lbl("", 16)
	time_lbl.anchor_left = 0
	time_lbl.anchor_top = 0
	time_lbl.position = Vector2(16, 12)
	time_lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(time_lbl)

	# 底部一鍵列
	bar = HBoxContainer.new()
	bar.anchor_left = 0.0
	bar.anchor_right = 1.0
	bar.anchor_top = 1.0
	bar.anchor_bottom = 1.0
	bar.offset_left = 16
	bar.offset_right = -16
	bar.offset_top = -120
	bar.offset_bottom = -24
	bar.add_theme_constant_override("separation", 12)
	bar.alignment = BoxContainer.ALIGNMENT_CENTER
	bar.mouse_filter = Control.MOUSE_FILTER_STOP
	root.add_child(bar)

	btn_feed = _icon_btn("need_eat", "餵")
	btn_clean = _icon_btn("poop", "執")
	btn_pat = _icon_btn("need_pet", "摸")
	btn_feed.pressed.connect(func(): _one_tap("feed"))
	btn_clean.pressed.connect(func(): _one_tap("clean"))
	btn_pat.pressed.connect(func(): _one_tap("pat"))
	bar.add_child(btn_feed)
	bar.add_child(btn_clean)
	bar.add_child(btn_pat)

	# 總結卡（按鈕上方）
	card = PanelContainer.new()
	card.anchor_left = 0.5
	card.anchor_right = 0.5
	card.anchor_top = 1.0
	card.anchor_bottom = 1.0
	card.offset_left = -140
	card.offset_right = 140
	card.offset_top = -200
	card.offset_bottom = -132
	card.visible = false
	card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(1, 0.97, 0.9, 0.92)
	sb.corner_radius_top_left = 16
	sb.corner_radius_top_right = 16
	sb.corner_radius_bottom_left = 16
	sb.corner_radius_bottom_right = 16
	sb.content_margin_left = 12
	sb.content_margin_right = 12
	sb.content_margin_top = 8
	sb.content_margin_bottom = 8
	card.add_theme_stylebox_override("panel", sb)
	card_row = HBoxContainer.new()
	card_row.alignment = BoxContainer.ALIGNMENT_CENTER
	card_row.add_theme_constant_override("separation", 10)
	card.add_child(card_row)
	root.add_child(card)

	hide_btn = _btn("欣賞")
	hide_btn.anchor_left = 0
	hide_btn.anchor_top = 1
	hide_btn.anchor_right = 0
	hide_btn.anchor_bottom = 1
	hide_btn.offset_left = 16
	hide_btn.offset_top = -172
	hide_btn.offset_right = 120
	hide_btn.offset_bottom = -128
	hide_btn.pressed.connect(func():
		if AudioManager:
			AudioManager.play("sfx_ui8_btn_press_a")
		_toggle_hide()
	)
	root.add_child(hide_btn)

	dev_btn = _btn("開發者")
	dev_btn.anchor_left = 1
	dev_btn.anchor_top = 1
	dev_btn.anchor_right = 1
	dev_btn.anchor_bottom = 1
	dev_btn.offset_left = -136
	dev_btn.offset_top = -172
	dev_btn.offset_right = -16
	dev_btn.offset_bottom = -128
	dev_btn.pressed.connect(func():
		if AudioManager:
			AudioManager.play("sfx_ui8_btn_press_a")
		_toggle_dev()
	)
	root.add_child(dev_btn)

	_build_dev()
	dev_panel.visible = false
	if Sim:
		Sim.state_changed.connect(_refresh)
		if Sim.has_signal("care_done"):
			Sim.care_done.connect(_on_care)
		if Sim.has_signal("poops_changed"):
			Sim.poops_changed.connect(func(_n): _refresh())
	_refresh()


func _icon_btn(icon_id: String, tip: String) -> Button:
	var b := Button.new()
	b.custom_minimum_size = Vector2(96, 88)
	b.tooltip_text = tip
	var hb := VBoxContainer.new()
	hb.alignment = BoxContainer.ALIGNMENT_CENTER
	hb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var ic := TextureRect.new()
	var tex: Texture2D = null
	if icon_id == "poop" and ResourceLoader.exists("res://art/sprites/poop.png"):
		tex = load("res://art/sprites/poop.png")
	elif IconBank:
		tex = IconBank.tex(icon_id)
	ic.texture = tex
	ic.custom_minimum_size = Vector2(48, 48)
	ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hb.add_child(ic)
	b.add_child(hb)
	hb.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	if font:
		b.add_theme_font_override("font", font)
	return b


func _lbl(t: String, size: int) -> Label:
	var l := Label.new()
	l.text = t
	if font:
		l.add_theme_font_override("font", font)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", Color(0.15, 0.1, 0.08))
	l.add_theme_color_override("font_outline_color", Color(1, 1, 0.94, 0.85))
	l.add_theme_constant_override("outline_size", 4)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _btn(t: String) -> Button:
	var b := Button.new()
	b.text = t
	if font:
		b.add_theme_font_override("font", font)
	b.add_theme_font_size_override("font_size", 16)
	b.custom_minimum_size = Vector2(100, 40)
	return b


func _build_dev() -> void:
	dev_panel = PanelContainer.new()
	dev_panel.anchor_left = 1
	dev_panel.anchor_top = 0
	dev_panel.anchor_right = 1
	dev_panel.anchor_bottom = 0
	dev_panel.offset_left = -280
	dev_panel.offset_top = 16
	dev_panel.offset_right = -16
	dev_panel.offset_bottom = 340
	var vb := VBoxContainer.new()
	dev_panel.add_child(vb)
	vb.add_child(_lbl("開發者模式", 18))
	for item in [["低畫質（基線）", QualitySettings.Tier.LOW], ["中畫質", QualitySettings.Tier.MID], ["高畫質", QualitySettings.Tier.HIGH]]:
		var b := _btn(str(item[0]))
		var tier: int = item[1]
		b.pressed.connect(func():
			if AudioManager:
				AudioManager.play("sfx_ui8_btn_press_a")
			QualitySettings.set_tier(tier)
		)
		vb.add_child(b)
	var b_poop := _btn("加一粒便便")
	b_poop.pressed.connect(func():
		if AudioManager:
			AudioManager.play("sfx_ui8_btn_press_a")
		Sim.add_poop()
	)
	vb.add_child(b_poop)
	var b_slp := _btn("切換睡眠")
	b_slp.pressed.connect(_toggle_sleep)
	vb.add_child(b_slp)
	var b_h := _btn("快轉 +1 小時")
	b_h.pressed.connect(func():
		if AudioManager:
			AudioManager.play("sfx_ui8_btn_press_a")
		_ff_hour()
	)
	vb.add_child(b_h)
	root.add_child(dev_panel)


func _toggle_sleep() -> void:
	if AudioManager:
		AudioManager.play("sfx_ui8_btn_press_a")
	var on := not bool(Sim.state.get("sleeping", false))
	Sim.set_sleeping(on)
	if AudioManager:
		if on:
			AudioManager.play("sfx_sleep_on")
			AudioManager.start_loop("sfx_pet_sleep_breath_loop")
		else:
			AudioManager.stop_loop("sfx_pet_sleep_breath_loop")


func _ff_hour() -> void:
	Sim.advance(Sim.state, 3600.0, {})
	Sim.state["last_seen"] = TimeService.now_ms()
	Sim.state_changed.emit()
	Sim.poops_changed.emit(int(Sim.state.get("poops", 0)))


func _toggle_hide() -> void:
	hidden = not hidden
	bar.visible = not hidden
	dev_btn.visible = not hidden
	time_lbl.visible = not hidden
	dev_panel.visible = dev_panel.visible and not hidden
	if hidden:
		card.visible = false
	hide_btn.text = "顯示" if hidden else "欣賞"


func _toggle_dev() -> void:
	if hidden:
		return
	dev_panel.visible = not dev_panel.visible


func set_observing(on: bool) -> void:
	observing = on
	if not on and not card_queue.is_empty():
		_show_card(card_queue.pop_front())


func _one_tap(act: String) -> void:
	if AudioManager:
		AudioManager.play("sfx_ui8_btn_press_a")
	var rec: Dictionary = {}
	match act:
		"feed":
			rec = Sim.feed("meal")
		"clean":
			rec = Sim.clean_all()
		"pat":
			rec = Sim.pat()
			# 通知所有寵物做摸反應
			var main := get_tree().get_first_node_in_group("glimmer_main")
			if main and main.has_method("pet_all_react"):
				main.pet_all_react()
	if rec.is_empty():
		return
	_on_care(act, rec)


func _on_care(act: String, rec: Dictionary) -> void:
	if not bool(rec.get("ok", false)):
		# 食唔落／冇屎：都出一張細卡
		if str(rec.get("reason", "")) == "full":
			_queue_or_show(_card_items(act, rec))
		return
	_queue_or_show(_card_items(act, rec))
	_refresh()


func _queue_or_show(items: Array) -> void:
	if items.is_empty():
		return
	if observing:
		card_queue.append(items)
		return
	_show_card(items)


func _card_items(act: String, rec: Dictionary) -> Array:
	var items: Array = []
	match act:
		"feed":
			items.append({"icon": "need_eat", "num": "+%d" % int(round(float(rec.get("hunger", 0))))})
			if float(rec.get("mood", 0)) != 0.0:
				items.append({"icon": "mood_happy", "num": "+%d" % int(round(float(rec.get("mood", 0))))})
		"clean":
			items.append({"icon": "poop", "num": "×%d" % int(rec.get("count", 0))})
		"pat":
			items.append({"icon": "need_pet", "num": "+%d" % int(round(float(rec.get("mood", 0))))})
	return items


func _show_card(items: Array) -> void:
	for c in card_row.get_children():
		c.queue_free()
	for it in items:
		if not (it is Dictionary):
			continue
		var vb := VBoxContainer.new()
		vb.alignment = BoxContainer.ALIGNMENT_CENTER
		var ic := TextureRect.new()
		var iid := str(it.get("icon", ""))
		var tex: Texture2D = null
		if iid == "poop" and ResourceLoader.exists("res://art/sprites/poop.png"):
			tex = load("res://art/sprites/poop.png")
		elif IconBank:
			tex = IconBank.tex(iid)
		ic.texture = tex
		ic.custom_minimum_size = Vector2(36, 36)
		ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		vb.add_child(ic)
		var n := _lbl(str(it.get("num", "")), 18)
		n.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		vb.add_child(n)
		card_row.add_child(vb)
	var hold := 3.0
	var m1: Dictionary = GameData.m1a if GameData else {}
	hold = float(m1.get("summary_card_sec", 3))
	card_t = hold
	card.visible = not hidden


func _refresh() -> void:
	# 執屎掣：冇屎就淡
	if btn_clean:
		var n := int(Sim.state.get("poops", 0)) if Sim else 0
		btn_clean.modulate = Color(1, 1, 1, 1) if n > 0 else Color(1, 1, 1, 0.45)
		btn_clean.disabled = n <= 0
	if btn_feed and Sim:
		var hung := float((Sim.state.get("needs", {}) as Dictionary).get("hunger", 0))
		var full := hung >= float(Sim.FEED_REFUSE_AT)
		btn_feed.modulate = Color(1, 1, 1, 0.45) if full else Color.WHITE


func _process(dt: float) -> void:
	if time_lbl and not hidden and TimeService:
		var d: Dictionary = TimeService.local_dict(TimeService.now_ms())
		time_lbl.text = "%02d:%02d" % [int(d.get("hour", 0)), int(d.get("minute", 0))]
	if card_t > 0.0:
		card_t -= dt
		if card_t <= 0.0:
			card.visible = false
			if not observing and not card_queue.is_empty():
				_show_card(card_queue.pop_front())
