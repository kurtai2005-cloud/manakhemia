extends CanvasLayer
## M1b HUD：一鍵只得執屎／收成／派工／狩獵；餵同摸要先揀寵物再人手做。總結卡唔擋住欣賞／開發者。

var font: Font
var root: Control
var hide_btn: Button
var dev_btn: Button
var dev_panel: PanelContainer
var hidden := false
var bar: HBoxContainer
var care_bar: HBoxContainer
var btn_clean: Button
var btn_harvest: Button
var btn_hunt: Button
var btn_dispatch: Button
var btn_feed: Button
var btn_snack: Button
var btn_pat: Button
var btn_book: Button
var back_btn: Button
var book_dot: ColorRect
var harvest_badge: Label
var card: PanelContainer
var card_row: HBoxContainer
var card_t := 0.0
var card_queue: Array = []
var observing := false
var time_lbl: Label
var book_panel: PanelContainer
var care_target: Walker
var shard_lbl: Label
var food_lbl: Label
var goal_bar: BoxContainer
var btn_goal_food: Button
var btn_goal_rest: Button
var btn_replay_post: Button
var btn_replay_hunt: Button
var replay_reason: Label
var preview_lbl: Label


func _ready() -> void:
	layer = 20
	font = Vc27Fonts.ensure()
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

	shard_lbl = _lbl("", 16)
	shard_lbl.anchor_left = 0
	shard_lbl.anchor_top = 0
	shard_lbl.position = Vector2(16, 36)
	shard_lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(shard_lbl)

	var food_icon := TextureRect.new()
	food_icon.name = "FoodIcon"
	food_icon.texture = load("res://art-pet/sprites/hunt/fruits/starberry.png")
	food_icon.position = Vector2(150, 32)
	food_icon.custom_minimum_size = Vector2(22, 22)
	food_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	food_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	food_icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(food_icon)
	food_lbl = _lbl("0", 16)
	food_lbl.name = "FoodCount"
	food_lbl.anchor_left = 0
	food_lbl.anchor_top = 0
	food_lbl.position = Vector2(176, 36)
	food_lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(food_lbl)
	if _show_replay_buttons():
		preview_lbl = _lbl("試玩·各一次", 14)
		preview_lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
		root.add_child(preview_lbl)
		_build_replay_buttons(root)

	# 左上收藏（屋 ×2 之後右上會同煙囪重疊）
	btn_book = _btn("圖鑑")
	btn_book.anchor_left = 0
	btn_book.anchor_top = 0
	btn_book.anchor_right = 0
	btn_book.anchor_bottom = 0
	btn_book.offset_left = 16
	btn_book.offset_top = 64
	btn_book.offset_right = 136
	btn_book.offset_bottom = 108
	btn_book.pressed.connect(func():
		_toggle_book()
	)
	root.add_child(btn_book)
	book_dot = ColorRect.new()
	book_dot.color = Color(0.92, 0.2, 0.18)
	book_dot.size = Vector2(14, 14)
	book_dot.position = Vector2(110, 4)
	book_dot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	book_dot.visible = false
	btn_book.add_child(book_dot)

	# 室內返回（只喺屋內顯示；同圖鑑一列疊喺左上，避開煙囪）
	back_btn = _btn("返回")
	back_btn.anchor_left = 0
	back_btn.anchor_top = 0
	back_btn.anchor_right = 0
	back_btn.anchor_bottom = 0
	back_btn.offset_left = 16
	back_btn.offset_top = 116
	back_btn.offset_right = 136
	back_btn.offset_bottom = 160
	back_btn.visible = false
	back_btn.pressed.connect(func():
		_play_press()
		var main := get_tree().get_first_node_in_group("glimmer_main")
		if main and main.has_method("exit_house"):
			main.exit_house()
	)
	root.add_child(back_btn)

	# 底部一鍵列：執／收成／出發／派工
	bar = HBoxContainer.new()
	bar.anchor_left = 0.0
	bar.anchor_right = 1.0
	bar.anchor_top = 1.0
	bar.anchor_bottom = 1.0
	bar.offset_left = 8
	bar.offset_right = -8
	bar.offset_top = -120
	bar.offset_bottom = -24
	bar.add_theme_constant_override("separation", 8)
	bar.alignment = BoxContainer.ALIGNMENT_CENTER
	bar.mouse_filter = Control.MOUSE_FILTER_STOP
	root.add_child(bar)

	btn_clean = _icon_btn("poop", "執")
	btn_harvest = _icon_btn("ev_gift", "收成")
	btn_hunt = _icon_btn("ev_walk", "出發")
	btn_dispatch = _icon_btn("ev_work", "派工")
	btn_clean.pressed.connect(func(): _one_tap("clean"))
	btn_harvest.pressed.connect(func(): _one_tap("harvest"))
	btn_hunt.pressed.connect(func(): _one_tap("hunt"))
	btn_dispatch.pressed.connect(func(): _one_tap("dispatch"))
	harvest_badge = _lbl("", 14)
	harvest_badge.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	btn_harvest.add_child(harvest_badge)
	harvest_badge.position = Vector2(64, 4)
	bar.add_child(btn_clean)
	bar.add_child(btn_harvest)
	bar.add_child(btn_hunt)
	bar.add_child(btn_dispatch)

	# 揀咗寵物先出嘅人手照顧列
	care_bar = HBoxContainer.new()
	care_bar.anchor_left = 0.0
	care_bar.anchor_right = 1.0
	care_bar.anchor_top = 1.0
	care_bar.anchor_bottom = 1.0
	care_bar.offset_left = 16
	care_bar.offset_right = -16
	care_bar.offset_top = -228
	care_bar.offset_bottom = -140
	care_bar.add_theme_constant_override("separation", 12)
	care_bar.alignment = BoxContainer.ALIGNMENT_CENTER
	care_bar.visible = false
	root.add_child(care_bar)
	btn_feed = _icon_btn("need_eat", "餵")
	btn_snack = _icon_btn("ev_eat", "小吃")
	btn_pat = _icon_btn("need_pet", "摸")
	btn_feed.pressed.connect(func(): _hand("feed", "meal"))
	btn_snack.pressed.connect(func(): _hand("feed", "snack"))
	btn_pat.pressed.connect(func(): _hand("pat", ""))
	care_bar.add_child(btn_feed)
	care_bar.add_child(btn_snack)
	care_bar.add_child(btn_pat)

	goal_bar = VBoxContainer.new()
	goal_bar.name = "GoalBar"
	goal_bar.anchor_left = 1.0
	goal_bar.anchor_right = 1.0
	goal_bar.anchor_top = 0.0
	goal_bar.anchor_bottom = 0.0
	goal_bar.offset_left = -100
	goal_bar.offset_right = -8
	goal_bar.offset_top = 56
	goal_bar.offset_bottom = 248
	goal_bar.add_theme_constant_override("separation", 8)
	goal_bar.alignment = BoxContainer.ALIGNMENT_CENTER
	goal_bar.visible = false
	root.add_child(goal_bar)
	btn_goal_food = _icon_btn("need_eat", "")
	btn_goal_food.name = "GoalFood"
	btn_goal_rest = _icon_btn("need_sleep", "")
	btn_goal_rest.name = "GoalRest"
	btn_goal_food.pressed.connect(_press_goal_food)
	btn_goal_rest.pressed.connect(_press_goal_rest)
	goal_bar.add_child(btn_goal_food)
	goal_bar.add_child(btn_goal_rest)

	# 總結卡：提高，避開欣賞／開發者
	card = PanelContainer.new()
	card.anchor_left = 0.5
	card.anchor_right = 0.5
	card.anchor_top = 1.0
	card.anchor_bottom = 1.0
	card.offset_left = -150
	card.offset_right = 150
	card.offset_top = -360
	card.offset_bottom = -250
	card.visible = false
	card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(1, 0.97, 0.9, 0.94)
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
	hide_btn.anchor_left = 1
	hide_btn.anchor_top = 0
	hide_btn.anchor_right = 1
	hide_btn.anchor_bottom = 0
	hide_btn.offset_left = -120
	hide_btn.offset_top = 12
	hide_btn.offset_right = -16
	hide_btn.offset_bottom = 52
	hide_btn.pressed.connect(func():
		if AudioManager:
			_play_press()  # was: hardcoded _a
		_toggle_hide()
	)
	root.add_child(hide_btn)

	dev_btn = _btn("開發者")
	dev_btn.anchor_left = 1
	dev_btn.anchor_top = 1
	dev_btn.anchor_right = 1
	dev_btn.anchor_bottom = 1
	dev_btn.offset_left = -136
	dev_btn.offset_top = 60
	dev_btn.offset_right = -16
	dev_btn.offset_bottom = 104
	dev_btn.visible = _dev_allowed()
	dev_btn.pressed.connect(func():
		if AudioManager:
			_play_press()  # was: hardcoded _a
		_toggle_dev()
	)
	root.add_child(dev_btn)

	_build_dev()
	dev_panel.visible = false
	_build_book()
	if Sim:
		Sim.state_changed.connect(_refresh)
		if Sim.has_signal("care_done"):
			Sim.care_done.connect(_on_care)
		if Sim.has_signal("poops_changed"):
			Sim.poops_changed.connect(func(_n): _refresh())
	if CollectionSystem and CollectionSystem.has_signal("dots_changed"):
		CollectionSystem.dots_changed.connect(_refresh)
		CollectionSystem.shards_changed.connect(func(_n): _refresh())
	_refresh()
	_apply_appreciate_mute()


func _play_ui(hook: String) -> void:
	if AudioManager:
		AudioManager.play(hook)


func _play_press() -> void:
	_play_ui("sfx_ui8_btn_press")


func _play_error() -> void:
	_play_ui("sfx_ui8_error")


func _icon_btn(icon_id: String, tip: String) -> Button:
	var b := Button.new()
	b.custom_minimum_size = Vector2(80, 88)
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
	ic.custom_minimum_size = Vector2(40, 40)
	ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hb.add_child(ic)
	var tip_l := _lbl(tip, 12)
	tip_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hb.add_child(tip_l)
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
	dev_panel.offset_top = 64
	dev_panel.offset_right = -16
	dev_panel.offset_bottom = 420
	var vb := VBoxContainer.new()
	dev_panel.add_child(vb)
	vb.add_child(_lbl("開發者模式", 18))
	for item in [["低畫質（基線）", QualitySettings.Tier.LOW], ["中畫質", QualitySettings.Tier.MID], ["高畫質", QualitySettings.Tier.HIGH]]:
		var b := _btn(str(item[0]))
		var tier: int = item[1]
		b.pressed.connect(func():
			if AudioManager:
				_play_press()  # was: hardcoded _a
			QualitySettings.set_tier(tier)
		)
		vb.add_child(b)
	var b_poop := _btn("加一粒便便")
	b_poop.pressed.connect(func():
		if AudioManager:
			_play_press()  # was: hardcoded _a
		Sim.add_poop()
	)
	vb.add_child(b_poop)
	var b_slp := _btn("切換睡眠")
	b_slp.pressed.connect(_toggle_sleep)
	vb.add_child(b_slp)
	var b_h := _btn("快轉 +1 小時")
	b_h.pressed.connect(func():
		if AudioManager:
			_play_press()  # was: hardcoded _a
		_ff_hour()
	)
	vb.add_child(b_h)
	var b_sh := _btn("加 20 碎")
	b_sh.pressed.connect(func():
		if AudioManager:
			_play_press()  # was: hardcoded _a
		if CollectionSystem:
			CollectionSystem.add_shards(20, "old")
	)
	vb.add_child(b_sh)
	root.add_child(dev_panel)


func _build_book() -> void:
	book_panel = PanelContainer.new()
	book_panel.anchor_left = 0.06
	book_panel.anchor_right = 0.94
	book_panel.anchor_top = 0.10
	book_panel.anchor_bottom = 0.78
	book_panel.visible = false
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(1, 0.97, 0.9, 0.96)
	sb.corner_radius_top_left = 12
	sb.corner_radius_top_right = 12
	sb.corner_radius_bottom_left = 12
	sb.corner_radius_bottom_right = 12
	sb.content_margin_left = 10
	sb.content_margin_right = 10
	sb.content_margin_top = 8
	sb.content_margin_bottom = 8
	book_panel.add_theme_stylebox_override("panel", sb)
	var vb := VBoxContainer.new()
	book_panel.add_child(vb)
	vb.add_child(_lbl("收藏", 18))
	var close := _btn("關閉")
	close.pressed.connect(func():
		book_panel.visible = false
		_play_ui("sfx_ui8_popup_close")
		if CollectionSystem:
			CollectionSystem.clear_new()
	)
	vb.add_child(close)
	var rec := _btn("一鍵擺家具")
	rec.pressed.connect(func():
		if CollectionSystem:
			var r: Dictionary = CollectionSystem.place_recommended()
			if bool(r.get("ok", false)):
				_queue_or_show([{"icon": "ev_gift", "num": "擺好"}])
				var main := get_tree().get_first_node_in_group("glimmer_main")
				if main and main.has_method("refresh_furniture"):
					main.refresh_furniture()
	)
	vb.add_child(rec)
	# 簡表：碎、已解鎖格數、家具
	var info := _lbl("", 14)
	info.name = "BookInfo"
	vb.add_child(info)
	var shop := VBoxContainer.new()
	shop.name = "Shop"
	vb.add_child(shop)
	root.add_child(book_panel)


func _refresh_book() -> void:
	if book_panel == null or not book_panel.visible or CollectionSystem == null:
		return
	var info: Label = book_panel.find_child("BookInfo", true, false) as Label
	if info:
		var forms: Dictionary = CollectionSystem.ensure()["collection"].get("forms", {})
		var found := ""
		if CollectionSystem.has_method("discovered_names"):
			var names: PackedStringArray = CollectionSystem.discovered_names()
			if names.size() > 0:
				found = "　已發現 " + "、".join(names)
		var stage_name := ""
		if Sim and Sim.has_method("stage_zh"):
			stage_name = Sim.stage_zh() + "　"
		info.text = "%s星星碎 %d　圖鑑 %d／54　家具 %d%s" % [stage_name, CollectionSystem.stardust(), forms.size(), CollectionSystem.owned().size(), found]
	var shop: VBoxContainer = book_panel.find_child("Shop", true, false) as VBoxContainer
	if shop == null:
		return
	for c in shop.get_children():
		c.queue_free()
	for it in CollectionSystem.furniture_items():
		if not (it is Dictionary):
			continue
		if it.get("price", null) == null and str(it.get("src", "")) != "default":
			continue
		var id := str(it.get("id", ""))
		var price = it.get("price", 0)
		var p: int = 0 if price == null else int(price)
		var already_owned: bool = CollectionSystem.is_owned(id)
		var lab := "%s  %s" % [str(it.get("zh", id)), ("已有" if already_owned else ("%d 碎" % p))]
		var b := _btn(lab)
		b.disabled = already_owned and p > 0
		var captured := id
		b.pressed.connect(func():
			if CollectionSystem.is_owned(captured):
				CollectionSystem.place(captured)
				var main := get_tree().get_first_node_in_group("glimmer_main")
				if main and main.has_method("refresh_furniture"):
					main.refresh_furniture()
			else:
				var r: Dictionary = CollectionSystem.buy(captured)
				if bool(r.get("ok", false)):
					CollectionSystem.place(captured)
					_queue_or_show([{"icon": "ev_gift", "num": str(it.get("zh", captured))}])
					var main2 := get_tree().get_first_node_in_group("glimmer_main")
					if main2 and main2.has_method("refresh_furniture"):
						main2.refresh_furniture()
				else:
					_play_error()
			_refresh_book()
		)
		shop.add_child(b)


func _toggle_book() -> void:
	if hidden:
		return
	book_panel.visible = not book_panel.visible
	if book_panel.visible:
		# 開圖鑑：只播翻頁，唔疊 popup_open／btn_press
		_play_ui("sfx_codex_page_flip")
		_refresh_book()
	else:
		_play_ui("sfx_ui8_popup_close")


func _toggle_sleep() -> void:
	if AudioManager:
		_play_press()  # was: hardcoded _a
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
	if HuntSystem:
		HuntSystem.offline_tick(Sim.state, TimeService.now_ms())
	if WorkSystem:
		WorkSystem.offline_tick(Sim.state, TimeService.now_ms())
	Sim.state_changed.emit()
	Sim.poops_changed.emit(int(Sim.state.get("poops", 0)))


func _toggle_hide() -> void:
	hidden = not hidden
	bar.visible = not hidden
	care_bar.visible = (not hidden) and observing and care_target != null
	dev_btn.visible = _dev_allowed() and not hidden and not card.visible
	time_lbl.visible = not hidden
	shard_lbl.visible = not hidden
	btn_book.visible = not hidden
	dev_panel.visible = dev_panel.visible and not hidden
	if hidden:
		card.visible = false
		if book_panel:
			book_panel.visible = false
	hide_btn.text = "顯示" if hidden else "欣賞"
	_apply_appreciate_mute()


func _apply_appreciate_mute() -> void:
	if AudioManager:
		AudioManager.appreciate_muted = hidden


func _toggle_dev() -> void:
	if hidden:
		return
	dev_panel.visible = not dev_panel.visible


func set_observing(on: bool) -> void:
	observing = on
	if not on:
		care_target = null
	care_bar.visible = (not hidden) and observing and care_target != null
	if not on and not card_queue.is_empty():
		_show_card(card_queue.pop_front())


func set_care_target(w: Walker) -> void:
	care_target = w
	care_bar.visible = (not hidden) and w != null
	observing = w != null or observing


func _hand(act: String, food: String) -> void:
	if AudioManager:
		_play_press()  # was: hardcoded _a
	var main := get_tree().get_first_node_in_group("glimmer_main")
	if main == null:
		return
	var rec: Dictionary = {}
	if act == "feed" and main.has_method("hand_feed"):
		rec = main.hand_feed(care_target, food)
	elif act == "pat" and main.has_method("hand_pat"):
		rec = main.hand_pat(care_target)
	if rec.is_empty():
		return
	card_queue.clear()
	set_observing(false)
	# 團絨經 Sim.care_done 出卡；flavor（細佬／訪客）或者食唔落先喺呢度出
	if bool(rec.get("flavor", false)) or str(rec.get("reason", "")) == "full":
		_on_care(act, rec)


func _one_tap(act: String) -> void:
	var rec: Dictionary = {}
	match act:
		"clean":
			_play_press()
			rec = Sim.clean_all()
		"harvest":
			_play_press()
			rec = _do_harvest()
		"hunt":
			rec = _do_hunt()
			if bool(rec.get("ok", false)):
				_play_press()
			else:
				_play_error()
		"dispatch":
			rec = _do_dispatch()
			if bool(rec.get("ok", false)):
				_play_press()
			else:
				_play_error()
	if rec.is_empty():
		return
	if bool(rec.get("ok", false)):
		card_queue.clear()
		set_observing(false)
	_on_care(str(rec.get("act", act)), rec)


func _do_harvest() -> Dictionary:
	var items: Array = []
	var shards := 0
	var fruits := 0
	if HuntSystem and HuntSystem.phase == HuntSystem.PHASE_READY:
		var h: Dictionary = HuntSystem.collect()
		if bool(h.get("ok", false)):
			shards += int(h.get("shards", 0))
			fruits += (h.get("fruits", []) as Array).size()
	if WorkSystem and WorkSystem.is_ready():
		var w: Dictionary = WorkSystem.collect()
		if bool(w.get("ok", false)):
			shards += int(w.get("shards", 0))
	if shards == 0 and fruits == 0:
		return {"ok": false, "reason": "none", "act": "harvest"}
	var rec := {"ok": true, "act": "harvest", "shards": shards, "fruits": fruits}
	# 直接組卡
	if shards > 0:
		items.append({"icon": "ev_gift", "num": "+%d" % shards})
	if fruits > 0:
		items.append({"icon": "ev_walk", "num": "×%d" % fruits})
	_queue_or_show(items)
	_refresh()
	return rec


func _do_hunt() -> Dictionary:
	var main := get_tree().get_first_node_in_group("glimmer_main")
	if main and main.has_method("start_hunt"):
		return main.start_hunt()
	return {"ok": false, "reason": "no_main"}


func _do_dispatch() -> Dictionary:
	var main := get_tree().get_first_node_in_group("glimmer_main")
	if main and main.has_method("one_tap_dispatch"):
		return main.one_tap_dispatch()
	return {"ok": false, "reason": "no_main"}


func _on_care(act: String, rec: Dictionary) -> void:
	if act == "harvest":
		return
	if not bool(rec.get("ok", false)):
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
		"work":
			items.append({"icon": "ev_work", "num": "+%d" % int(rec.get("shards", 0))})
		"hunt":
			items.append({"icon": "ev_walk", "num": "+%d" % int(rec.get("shards", 0))})
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
	var m1: Dictionary = GameData.m1b if GameData and "m1b" in GameData and not GameData.m1b.is_empty() else (GameData.m1a if GameData else {})
	hold = float(m1.get("summary_card_sec", 3))
	card_t = hold
	card.visible = not hidden
	_sync_side_buttons()


func _sync_side_buttons() -> void:
	# 卡出緊就收起欣賞／開發者，避免疊住
	var hide_side := (card.visible and card_t > 0.0) or (care_bar != null and care_bar.visible)
	if hide_btn:
		hide_btn.visible = not hidden and not hide_side
	if dev_btn:
		dev_btn.visible = _dev_allowed() and not hidden and not hide_side


func _refresh() -> void:
	if btn_clean:
		var n := int(Sim.state.get("poops", 0)) if Sim else 0
		btn_clean.modulate = Color(1, 1, 1, 1) if n > 0 else Color(1, 1, 1, 0.45)
		btn_clean.disabled = n <= 0
	if btn_feed and Sim:
		var hung := float((Sim.state.get("needs", {}) as Dictionary).get("hunger", 0))
		var full := hung >= float(Sim.FEED_REFUSE_AT)
		btn_feed.modulate = Color(1, 1, 1, 0.45) if full else Color.WHITE
	var pending := 0
	if CollectionSystem and CollectionSystem.harvest_pending():
		pending = 1
	if HuntSystem and HuntSystem.phase == HuntSystem.PHASE_READY:
		pending = maxi(pending, 1 + (HuntSystem.fruits.size() if HuntSystem.fruits else 0))
	if btn_harvest:
		btn_harvest.modulate = Color.WHITE if pending > 0 else Color(1, 1, 1, 0.45)
		btn_harvest.disabled = pending <= 0
		if harvest_badge:
			harvest_badge.text = str(pending) if pending > 0 else ""
	if btn_hunt and HuntSystem:
		var busy := HuntSystem.phase != HuntSystem.PHASE_IDLE and HuntSystem.phase != HuntSystem.PHASE_READY
		btn_hunt.disabled = busy or HuntSystem.phase == HuntSystem.PHASE_READY
		btn_hunt.modulate = Color(1, 1, 1, 0.45) if btn_hunt.disabled else Color.WHITE
	if btn_dispatch and WorkSystem:
		btn_dispatch.disabled = WorkSystem.any_working() and not WorkSystem.is_ready()
	if book_dot and CollectionSystem:
		book_dot.visible = CollectionSystem.has_dot("collection")
	if shard_lbl and CollectionSystem:
		shard_lbl.text = "★ %d" % CollectionSystem.stardust()
	if food_lbl and CollectionSystem and CollectionSystem.has_method("fruit_count"):
		food_lbl.text = str(int(CollectionSystem.call("fruit_count", "starberry")))
	_refresh_goal()
	_sync_side_buttons()


func _show_replay_buttons() -> bool:
	# Preview launch, not the saved egg shortcut. An upgraded save may lack preview_fixture.
	return SaveSystem != null and SaveSystem.has_method("is_preview") and SaveSystem.is_preview()


func _replay_font() -> Font:
	# Same chain as every other label: the subset, then the CJK fallback.
	return Vc27Fonts.ensure()


func _build_replay_buttons(root_node: Control) -> void:
	# Left column, under 圖鑑, inside the portrait safe area. Not the top-right corner.
	var face := _replay_font()
	var panel := StyleBoxFlat.new()
	panel.bg_color = Color(1.0, 0.96, 0.88, 0.96)
	panel.border_color = Color(0.25, 0.16, 0.08, 1)
	panel.set_border_width_all(2)
	panel.set_corner_radius_all(8)
	panel.content_margin_left = 8
	panel.content_margin_right = 8
	btn_replay_post = _replay_btn("重看郵局", face, panel)
	btn_replay_post.pressed.connect(func(): _press_replay("post"))
	root_node.add_child(btn_replay_post)
	btn_replay_hunt = _replay_btn("重看狩獵", face, panel)
	btn_replay_hunt.pressed.connect(func(): _press_replay("hunt"))
	root_node.add_child(btn_replay_hunt)
	replay_reason = _lbl("", 16)
	replay_reason.add_theme_font_override("font", face)
	root_node.add_child(replay_reason)
	btn_replay_post.z_index = 20
	btn_replay_hunt.z_index = 20
	_apply_replay_safe()


func _safe_viewport_rect() -> Rect2:
	var vp: Vector2 = get_viewport().get_visible_rect().size
	var win: Vector2i = DisplayServer.window_get_size()
	var safe: Rect2i = DisplayServer.get_display_safe_area()
	var fit := 1.0
	var ox := 0.0
	var oy := 0.0
	if win.x > 0 and win.y > 0 and vp.x > 1.0 and vp.y > 1.0:
		fit = minf(float(win.x) / vp.x, float(win.y) / vp.y)
		if fit <= 0.0:
			fit = 1.0
		ox = (float(win.x) - vp.x * fit) * 0.5
		oy = (float(win.y) - vp.y * fit) * 0.5
	var left := maxf(0.0, (float(safe.position.x) - ox) / fit)
	var top := maxf(0.0, (float(safe.position.y) - oy) / fit)
	var right := minf(vp.x, (float(safe.position.x + safe.size.x) - ox) / fit)
	var bottom := minf(vp.y, (float(safe.position.y + safe.size.y) - oy) / fit)
	left += 16.0
	top += 8.0
	right -= 16.0
	bottom -= 8.0
	return Rect2(Vector2(left, top), Vector2(maxf(0.0, right - left), maxf(0.0, bottom - top)))


func _min_tap_px() -> float:
	var dpi := float(DisplayServer.screen_get_dpi())
	if dpi < 10.0:
		dpi = 160.0
	var win: Vector2i = DisplayServer.window_get_size()
	var vp: Vector2 = get_viewport().get_visible_rect().size
	var fit := 1.0
	if win.x > 0 and win.y > 0 and vp.x > 1.0 and vp.y > 1.0:
		fit = minf(float(win.x) / vp.x, float(win.y) / vp.y)
	if fit <= 0.0:
		fit = 1.0
	# 48dp on the phone, and at least 64 design px so Note10+ 19:9 stays above that.
	return maxf(64.0, (48.0 * dpi / 160.0) / fit)


func _place_box(node: Control, x: float, y: float, w: float, h: float) -> void:
	node.anchor_left = 0
	node.anchor_right = 0
	node.anchor_top = 0
	node.anchor_bottom = 0
	node.offset_left = x
	node.offset_top = y
	node.offset_right = x + w
	node.offset_bottom = y + h


func _apply_replay_safe() -> void:
	if btn_replay_post == null or btn_replay_hunt == null:
		return
	var area := _safe_viewport_rect()
	var tap := _min_tap_px()
	# 圖鑑 occupies y 64–108. Stay under it even if its rect is not ready yet.
	var book_end := 108.0
	if btn_book:
		var br: Rect2 = btn_book.get_global_rect()
		if br.size.y > 1.0:
			book_end = br.end.y
	var y := maxf(area.position.y, book_end + 12.0)
	var x := area.position.x
	var w := minf(220.0, area.size.x)
	if w < tap:
		w = area.size.x
	if preview_lbl:
		_place_box(preview_lbl, x, y, w, 28.0)
		y += 32.0
	_place_box(btn_replay_post, x, y, w, tap)
	_place_box(btn_replay_hunt, x, y + tap + 8.0, w, tap)
	if replay_reason:
		_place_box(replay_reason, x, y + (tap + 8.0) * 2.0, w, 28.0)


func _replay_btn(text: String, face: Font, panel: StyleBox) -> Button:
	var b := Button.new()
	b.text = text
	b.add_theme_font_override("font", face)
	b.add_theme_font_size_override("font_size", 22)
	b.add_theme_color_override("font_color", Color(0.15, 0.08, 0.04))
	b.add_theme_color_override("font_disabled_color", Color(0.35, 0.28, 0.22))
	b.add_theme_stylebox_override("normal", panel)
	b.add_theme_stylebox_override("hover", panel)
	b.add_theme_stylebox_override("pressed", panel)
	b.add_theme_stylebox_override("disabled", panel)
	b.custom_minimum_size = Vector2(204, 52)
	b.anchor_left = 0
	b.anchor_right = 0
	b.anchor_top = 0
	b.anchor_bottom = 0
	b.offset_left = 16
	b.offset_right = 220
	return b


func _press_replay(kind: String) -> void:
	var main := get_tree().get_first_node_in_group("glimmer_main")
	if main == null:
		return
	var rec: Dictionary = {}
	if kind == "post" and main.has_method("replay_post"):
		rec = main.replay_post()
	elif kind == "hunt" and main.has_method("replay_hunt"):
		rec = main.replay_hunt()
	if bool(rec.get("ok", false)):
		_play_press()
		if replay_reason:
			replay_reason.text = ""
	else:
		_play_error()
		if replay_reason:
			replay_reason.text = str(rec.get("reason", ""))


func _sync_replay_buttons() -> void:
	if btn_replay_post == null or btn_replay_hunt == null:
		return
	var main := get_tree().get_first_node_in_group("glimmer_main")
	var why := ""
	if main and main.has_method("replay_block_reason"):
		why = str(main.replay_block_reason())
	var blocked := why != ""
	btn_replay_post.disabled = blocked
	btn_replay_hunt.disabled = blocked
	btn_replay_post.modulate = Color(1, 1, 1, 0.45) if blocked else Color.WHITE
	btn_replay_hunt.modulate = Color(1, 1, 1, 0.45) if blocked else Color.WHITE
	if replay_reason:
		replay_reason.text = why
	_apply_replay_safe()


func _process(dt: float) -> void:
	if time_lbl and not hidden and TimeService:
		var d: Dictionary = TimeService.local_dict(TimeService.now_ms())
		time_lbl.text = "%02d:%02d" % [int(d.get("hour", 0)), int(d.get("minute", 0))]
	if food_lbl and not hidden and CollectionSystem and CollectionSystem.has_method("fruit_count"):
		food_lbl.text = str(int(CollectionSystem.call("fruit_count", "starberry")))
	if not hidden:
		_refresh_goal()
	_sync_replay_buttons()
	if card_t > 0.0:
		card_t -= dt
		if card_t <= 0.0:
			card.visible = false
			_sync_side_buttons()
			if not observing and not card_queue.is_empty():
				_show_card(card_queue.pop_front())


func _dev_allowed() -> bool:
	return OS.get_environment("VC27_DEV_HUD") == "1"


func _press_goal_food() -> void:
	var errand := _errand()
	if errand and errand.has_method("press_food"):
		errand.call("press_food")


func _press_goal_rest() -> void:
	var errand := _errand()
	if errand and errand.has_method("press_rest"):
		errand.call("press_rest")


func _errand() -> Node:
	var main := get_tree().get_first_node_in_group("glimmer_main")
	if main == null:
		return null
	return main.get_node_or_null("GardenErrand")


func _refresh_goal() -> void:
	if goal_bar == null:
		return
	var errand := _errand()
	var food := errand != null and errand.has_method("food_choice") and bool(errand.call("food_choice"))
	var rest := errand != null and errand.has_method("rest_offered") and bool(errand.call("rest_offered"))
	var food_live := errand != null and errand.has_method("food_offered") and bool(errand.call("food_offered"))
	if btn_goal_food:
		btn_goal_food.visible = food
		btn_goal_food.modulate = Color.WHITE if food_live else Color(1, 1, 1, 0.45)
	if btn_goal_rest:
		btn_goal_rest.visible = rest
	goal_bar.visible = not hidden and (food or rest)


func set_in_interior(on: bool) -> void:
	if back_btn:
		back_btn.visible = on
