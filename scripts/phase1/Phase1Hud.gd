class_name Phase1Hud
extends CanvasLayer

const UI := "res://art/phase1/ui/"

var root: Control
var top: Control
var top_row: HBoxContainer
var care_row: HBoxContainer
var dock: HBoxContainer
var feed_row: HBoxContainer
var train_row: HBoxContainer
var map_row: HBoxContainer
var drawer: PanelContainer
var toast: Label
var emote: PanelContainer
var emote_label: Label
var emote_left := 0.0
var modal: PanelContainer
var modal_title: Label
var modal_body: Label
var import_box: TextEdit
var name_btn: Button
var shard_lbl: Label
var expand_btn: Button
var bars: Dictionary = {}
var collapsed := false
var zone_buttons: Dictionary = {}
var _btn_normal: StyleBox
var _btn_pressed: StyleBox
var _btn_disabled: StyleBox


func build() -> void:
	layer = 30
	root = Control.new()
	root.name = "Phase1Root"
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = Vc27Fonts.theme()
	root.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(root)
	_btn_normal = _slice("ui_btn_normal_9slice.png", 10.0, _flat(Color(0.96, 0.91, 0.8), Color(0.55, 0.36, 0.16)), 3.0)
	_btn_pressed = _slice("ui_btn_pressed_9slice.png", 10.0, _flat(Color(0.86, 0.72, 0.48), Color(0.42, 0.24, 0.1)), 3.0)
	_btn_disabled = _slice("ui_btn_disabled_9slice.png", 10.0, _flat(Color(0.75, 0.7, 0.62), Color(0.45, 0.38, 0.3)), 3.0)
	top = Control.new()
	top.name = "TopBar"
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(top)
	top_row = HBoxContainer.new()
	top_row.name = "TopRow"
	top_row.add_theme_constant_override("separation", 8)
	top_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top.add_child(top_row)
	name_btn = _btn("TopName", "小團絨 · 幼年期", _on_name)
	name_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name_btn.clip_text = true
	name_btn.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	top_row.add_child(name_btn)
	var shard_pill := PanelContainer.new()
	shard_pill.name = "ShardPill"
	shard_pill.add_theme_stylebox_override("panel", _slice("ui_pill_9slice.png", 8.0, _flat(Color(0.22, 0.13, 0.07, 0.82), Color(0.78, 0.62, 0.28))))
	shard_pill.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var shard_icon := _icon("icon_shard_16.png")
	shard_lbl = Label.new()
	shard_lbl.name = "Shards"
	Vc27Fonts.bind(shard_lbl)
	shard_lbl.add_theme_color_override("font_color", Color("f7ebd2"))
	shard_lbl.add_theme_color_override("font_outline_color", Color("24170f"))
	shard_lbl.add_theme_constant_override("outline_size", 4)
	if shard_icon:
		var row := HBoxContainer.new()
		var icon := TextureRect.new()
		icon.texture = shard_icon
		icon.custom_minimum_size = Vector2(16, 16)
		icon.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		row.add_child(icon)
		row.add_child(shard_lbl)
		shard_pill.add_child(row)
	else:
		shard_pill.add_child(shard_lbl)
	top_row.add_child(shard_pill)
	top_row.add_child(_btn("HideHud", "收起", _on_hide, "icon_hide_32.png"))
	top_row.add_child(_btn("OpenTools", "工具", _on_tools, "icon_tools_32.png"))
	care_row = HBoxContainer.new()
	care_row.name = "CareRow"
	care_row.add_theme_constant_override("separation", 6)
	care_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(care_row)
	var tones := {
		"飽食": Color("e6b65b"),
		"心情": Color("e88f79"),
		"親密": Color("bca0d8"),
		"體力": Color("8fba68"),
	}
	for key in ["飽食", "心情", "親密", "體力"]:
		var bar := _bar(key, tones[key])
		bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		care_row.add_child(bar)
		bars[key] = bar
	dock = HBoxContainer.new()
	dock.name = "Dock"
	dock.add_theme_constant_override("separation", 6)
	root.add_child(dock)
	dock.add_child(_btn("DockFeed", "餵食", _call.bind("open_feed"), "icon_feed_32.png"))
	dock.add_child(_btn("DockClean", "清潔", _call.bind("clean"), "icon_clean_32.png"))
	dock.add_child(_btn("DockPat", "摸摸", _call.bind("pat"), "icon_pat_32.png"))
	dock.add_child(_btn("DockTrain", "鍛鍊", _call.bind("open_train"), "icon_train_32.png"))
	dock.add_child(_btn("DockMap", "地圖", _call.bind("open_map"), "icon_map_32.png"))
	feed_row = _strip("FeedRow")
	feed_row.add_child(_btn("FoodDew", "露水莓", _call1.bind("feed", "dew")))
	feed_row.add_child(_btn("FoodStar", "星星果", _call1.bind("feed", "star")))
	feed_row.add_child(_btn("FoodSoup", "暖心湯", _call1.bind("feed", "soup")))
	root.add_child(feed_row)
	train_row = _strip("TrainRow")
	train_row.add_child(_btn("TrainPower", "力量", _call1.bind("train", "力量")))
	train_row.add_child(_btn("TrainAgility", "身手", _call1.bind("train", "身手")))
	train_row.add_child(_btn("TrainStamina", "耐力", _call1.bind("train", "耐力")))
	root.add_child(train_row)
	map_row = _strip("MapRow")
	for pair in [["ZoneHome", "小屋", "garden"], ["ZoneFarm", "農圃", "zone_farm"], ["ZoneShop", "工坊", "zone_workshop"], ["ZonePrairie", "草原", "prairie_edge"]]:
		var zid := str(pair[2])
		var b := _btn(str(pair[0]), str(pair[1]), _call1.bind("go_zone", zid))
		zone_buttons[zid] = b
		map_row.add_child(b)
	map_row.add_child(_btn("FollowPet", "跟寵", _call.bind("follow_pet")))
	root.add_child(map_row)
	expand_btn = _btn("ExpandHud", "展開", _on_expand)
	expand_btn.visible = false
	root.add_child(expand_btn)
	var toast_pill := PanelContainer.new()
	toast_pill.name = "ToastPill"
	toast_pill.visible = false
	toast_pill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	toast_pill.add_theme_stylebox_override("panel", _slice("ui_pill_9slice.png", 8.0, _flat(Color(0.16, 0.1, 0.06, 0.88), Color(0.78, 0.62, 0.28))))
	toast = Label.new()
	toast.name = "Toast"
	Vc27Fonts.bind(toast)
	toast.add_theme_color_override("font_color", Color("f7ebd2"))
	toast.add_theme_color_override("font_outline_color", Color("24170f"))
	toast.add_theme_constant_override("outline_size", 4)
	toast_pill.add_child(toast)
	root.add_child(toast_pill)
	emote = PanelContainer.new()
	emote.name = "Emote"
	emote.visible = false
	emote.mouse_filter = Control.MOUSE_FILTER_IGNORE
	emote.add_theme_stylebox_override("panel", _slice("ui_pill_9slice.png", 8.0, _flat(Color(0.18, 0.1, 0.06, 0.9), Color(0.86, 0.7, 0.32))))
	emote.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	emote_label = Label.new()
	emote_label.name = "EmoteText"
	Vc27Fonts.bind(emote_label)
	emote_label.add_theme_color_override("font_color", Color("f7ebd2"))
	emote_label.add_theme_color_override("font_outline_color", Color("24170f"))
	emote_label.add_theme_constant_override("outline_size", 4)
	emote.add_child(emote_label)
	root.add_child(emote)
	_build_drawer()
	_build_modal()
	apply_layout()
	refresh()


func _process(dt: float) -> void:
	if emote_left <= 0.0 or emote == null or not emote.visible:
		return
	emote_left -= dt
	_place_emote()
	if emote_left < 0.35:
		emote.modulate.a = clampf(emote_left / 0.35, 0.0, 1.0)
	if emote_left <= 0.0:
		emote.visible = false


func apply_layout() -> void:
	var safe := _safe()
	top.position = safe.position
	top.size = Vector2(safe.size.x, 40)
	top_row.position = Vector2.ZERO
	top_row.size = top.size
	for child in top_row.get_children():
		if child is Control and child != name_btn:
			(child as Control).custom_minimum_size = Vector2(64, 36)
	var shard := top_row.get_node_or_null("ShardPill") as Control
	if shard:
		shard.custom_minimum_size = Vector2(78, 36)
	care_row.position = Vector2(safe.position.x, safe.position.y + 44)
	care_row.size = Vector2(safe.size.x, 22)
	var dock_h := 52.0
	dock.position = Vector2(safe.position.x, safe.end.y - dock_h)
	dock.size = Vector2(safe.size.x, dock_h)
	for c in dock.get_children():
		if c is Control:
			(c as Control).custom_minimum_size = Vector2((safe.size.x - 24.0) / 5.0, 48)
			(c as Control).size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for row in [feed_row, train_row, map_row]:
		row.position = Vector2(safe.position.x, dock.position.y - 50)
		row.size = Vector2(safe.size.x, 44)
	expand_btn.position = Vector2(safe.end.x - 72, safe.position.y)
	expand_btn.size = Vector2(68, 34)
	var toast_pill := root.get_node_or_null("ToastPill") as Control
	if toast_pill:
		toast_pill.position = Vector2(safe.position.x + 8, safe.position.y + 72)
		toast_pill.size = Vector2(minf(160.0, safe.size.x * 0.4), 28)
	if drawer:
		drawer.position = Vector2(safe.position.x + 24, safe.position.y + 96)
		drawer.size = Vector2(safe.size.x - 48, 250)
	if modal and modal.visible:
		_fit_modal()


func refresh() -> void:
	var sim := Phase1Config.node("Sim")
	if sim == null:
		return
	var state: Dictionary = sim.get("state")
	var pet := Phase1Registry.primary(state)
	var p1 := Phase1Config.node("Phase1")
	var catalog: Dictionary = p1.get("doc") if p1 else {}
	var spec := Phase1Config.species(catalog, str(pet.get("species_id", "baby")))
	var stage_zh := EvolutionEngine.zh(catalog, str(pet.get("stage", "baby")))
	name_btn.text = "%s · %s Lv.%d" % [spec.get("zh", pet.get("name", "小團絨")), stage_zh, int(pet.get("stats", {}).get("lv", 1))]
	var shards := 0
	var bag := Phase1Config.node("CollectionSystem")
	if bag and bag.has_method("stardust"):
		shards = int(bag.call("stardust"))
	shard_lbl.text = "碎 %d" % shards
	var care: Dictionary = pet.get("care", {})
	for key in bars.keys():
		var bar := bars[key] as Control
		var fill := bar.get_node_or_null("Fill") as Control
		if fill:
			fill.size.x = maxf(8.0, (bar.size.x - 4.0) * clampf(float(care.get(key, 0)) / 100.0, 0.0, 1.0))
			fill.size.y = bar.size.y - 4.0
		var lab := bar.get_node_or_null("Cap") as Label
		if lab:
			lab.text = "%s %d" % [key, int(care.get(key, 0))]
	var zone := str(pet.get("zone_id", "garden"))
	for zid in zone_buttons.keys():
		var b := zone_buttons[zid] as Button
		b.modulate = Color(1.0, 0.9, 0.62) if zid == zone else Color.WHITE


func show_toast(text: String) -> void:
	toast.text = text
	var pill := root.get_node_or_null("ToastPill") as CanvasItem
	if pill:
		pill.visible = text != ""


func show_bubble(text: String) -> void:
	show_emote(text)


func show_emote(text: String) -> void:
	emote_label.text = text
	emote.visible = text != ""
	emote.modulate.a = 1.0
	emote_left = 2.2 if text != "" else 0.0
	if emote.visible:
		_place_emote()


func show_modal(title: String, body: String) -> void:
	if drawer:
		drawer.visible = false
	show_toast("")
	show_emote("")
	modal_title.text = title
	modal_body.text = body
	import_box.visible = false
	import_box.custom_minimum_size = Vector2.ZERO
	_modal_btn("ModalConfirm").visible = false
	_modal_btn("ModalCancel").visible = false
	_modal_btn("ModalClaim").visible = true
	modal.visible = true
	_fit_modal()
	call_deferred("_fit_modal")


func show_import(text: String) -> void:
	if drawer:
		drawer.visible = false
	modal_title.text = "匯入存檔"
	modal_body.text = "貼上存檔文字後按確認"
	import_box.text = text
	import_box.visible = true
	_modal_btn("ModalConfirm").visible = true
	_modal_btn("ModalCancel").visible = true
	_modal_btn("ModalClaim").visible = false
	modal.visible = true
	_fit_modal()
	call_deferred("_fit_modal")


func set_collapsed(v: bool) -> void:
	collapsed = v
	top.visible = not v
	care_row.visible = not v
	dock.visible = not v
	if v:
		feed_row.visible = false
		train_row.visible = false
		map_row.visible = false
		drawer.visible = false
	expand_btn.visible = v


func _fit_modal() -> void:
	var safe := _safe()
	var width := minf(300.0, safe.size.x - 36.0)
	modal.set_anchors_preset(Control.PRESET_TOP_LEFT)
	var lines := maxi(modal_body.text.split("\n", false).size(), 1)
	var body_h := float(lines) * 22.0
	modal_body.custom_minimum_size = Vector2(width - 36.0, body_h)
	var import_h := 0.0
	if import_box.visible:
		import_h = 72.0
		import_box.custom_minimum_size = Vector2(width - 36.0, 64.0)
	else:
		import_box.custom_minimum_size = Vector2.ZERO
	var h := 20.0 + 28.0 + body_h + import_h + 52.0
	modal.anchor_left = 0.0
	modal.anchor_top = 0.0
	modal.anchor_right = 0.0
	modal.anchor_bottom = 0.0
	var x := safe.position.x + (safe.size.x - width) * 0.5
	var y := safe.position.y + 108.0
	modal.offset_left = x
	modal.offset_top = y
	modal.offset_right = x + width
	modal.offset_bottom = y + h
	modal.custom_minimum_size = Vector2(width, h)


func _place_emote() -> void:
	var main := get_tree().root.get_node_or_null("Main")
	if main == null:
		return
	var cam := main.get("cam") as Camera3D
	var pet := main.get("pet") as Node3D
	if cam == null or pet == null:
		return
	if cam.is_position_behind(pet.global_position):
		emote.visible = false
		return
	var head := pet.global_position + Vector3(0, 48, 0)
	var coat := pet.get_node_or_null("Hd2dCoat") as Node3D
	if coat:
		head = coat.global_position + Vector3(0, 24, 0)
	var pt := cam.unproject_position(head)
	var safe := _safe()
	var w := 120.0
	var x := clampf(pt.x - w * 0.5, safe.position.x, safe.end.x - w)
	var y := clampf(pt.y - 40.0, safe.position.y + 70.0, safe.end.y - 80.0)
	emote.position = Vector2(x, y)
	emote.size = Vector2(w, 32)


func _on_name() -> void:
	_call("open_info")


func _on_hide() -> void:
	_call1("set_collapsed", true)


func _on_expand() -> void:
	_call1("set_collapsed", false)


func _on_tools() -> void:
	_call("toggle_drawer")


func _call(method: String) -> void:
	var p1 := Phase1Config.node("Phase1")
	if p1:
		p1.call(method)


func _call1(method: String, arg: Variant) -> void:
	var p1 := Phase1Config.node("Phase1")
	if p1:
		p1.call(method, arg)


func _build_drawer() -> void:
	drawer = PanelContainer.new()
	drawer.name = "ToolDrawer"
	drawer.visible = false
	drawer.add_theme_stylebox_override("panel", _slice("ui_panel_9slice.png", 12.0, _flat(Color(0.97, 0.93, 0.84, 0.96), Color(0.5, 0.32, 0.14))))
	drawer.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 8)
	margin.add_theme_constant_override("margin_right", 8)
	margin.add_theme_constant_override("margin_top", 8)
	margin.add_theme_constant_override("margin_bottom", 8)
	drawer.add_child(margin)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	margin.add_child(box)
	box.add_child(_btn("ToolHour", "+1 小時放置", _call.bind("idle_hour")))
	box.add_child(_btn("ToolShards", "+50 星星碎", _call.bind("grant_debug")))
	box.add_child(_btn("ToolEvo", "強制滿成長進化", _call.bind("force_evo")))
	box.add_child(_btn("ToolEgg", "立即產蛋", _call.bind("spawn_pet")))
	box.add_child(_btn("ToolExport", "匯出存檔", _call.bind("export_save")))
	box.add_child(_btn("ToolImport", "匯入存檔", _call.bind("import_save")))
	box.add_child(_btn("ToolReset", "重置測試存檔", _call.bind("reset_profile")))
	var saves := Phase1Config.node("SaveSystem")
	if saves and bool(saves.call("is_preview")):
		box.add_child(_btn("ReplayPost", "重看郵局", _call1.bind("replay", "post")))
		box.add_child(_btn("ReplayHunt", "重看狩獵", _call1.bind("replay", "hunt")))
	root.add_child(drawer)


func _build_modal() -> void:
	modal = PanelContainer.new()
	modal.name = "Modal"
	modal.visible = false
	modal.add_theme_stylebox_override("panel", _slice("ui_panel_9slice.png", 12.0, _flat(Color(0.16, 0.1, 0.07, 0.94), Color(0.8, 0.64, 0.3))))
	modal.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var margin := MarginContainer.new()
	margin.name = "ModalMargin"
	margin.add_theme_constant_override("margin_left", 12)
	margin.add_theme_constant_override("margin_right", 12)
	margin.add_theme_constant_override("margin_top", 10)
	margin.add_theme_constant_override("margin_bottom", 10)
	modal.add_child(margin)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 6)
	margin.add_child(box)
	modal_title = Label.new()
	modal_title.name = "ModalTitle"
	Vc27Fonts.bind(modal_title)
	modal_title.add_theme_color_override("font_color", Color("f7ebd2"))
	modal_title.add_theme_color_override("font_outline_color", Color("24170f"))
	modal_title.add_theme_constant_override("outline_size", 4)
	box.add_child(modal_title)
	modal_body = Label.new()
	modal_body.name = "ModalBody"
	modal_body.autowrap_mode = TextServer.AUTOWRAP_OFF
	Vc27Fonts.bind(modal_body)
	modal_body.add_theme_color_override("font_color", Color("f7ebd2"))
	modal_body.add_theme_color_override("font_outline_color", Color("24170f"))
	modal_body.add_theme_constant_override("outline_size", 4)
	box.add_child(modal_body)
	import_box = TextEdit.new()
	import_box.name = "ImportText"
	import_box.visible = false
	import_box.custom_minimum_size = Vector2.ZERO
	box.add_child(import_box)
	box.add_child(_btn("ModalClaim", "領取並關閉", _call.bind("close_modal")))
	box.add_child(_btn("ModalConfirm", "確認", _call.bind("confirm_modal")))
	box.add_child(_btn("ModalCancel", "取消", _call.bind("close_modal")))
	root.add_child(modal)


func _strip(node_name: String) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.name = node_name
	row.visible = false
	row.add_theme_constant_override("separation", 6)
	return row


func _bar(key: String, tone: Color) -> Control:
	var box := Control.new()
	box.name = "Bar" + key
	box.custom_minimum_size = Vector2(40, 22)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var track := Panel.new()
	track.name = "Track"
	track.set_anchors_preset(Control.PRESET_FULL_RECT)
	track.mouse_filter = Control.MOUSE_FILTER_IGNORE
	track.add_theme_stylebox_override("panel", _slice("ui_bar_track_9slice.png", 6.0, _flat(Color(0.15, 0.1, 0.07, 0.55), Color(0.35, 0.22, 0.12))))
	track.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	box.add_child(track)
	var fill := Panel.new()
	fill.name = "Fill"
	fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fill.position = Vector2(2, 2)
	var fill_style := _slice("ui_bar_fill_9slice.png", 6.0, _flat(Color.WHITE, Color(0.35, 0.22, 0.12)))
	fill.add_theme_stylebox_override("panel", fill_style)
	fill.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	fill.self_modulate = tone
	box.add_child(fill)
	var lab := Label.new()
	lab.name = "Cap"
	lab.text = key
	lab.position = Vector2(4, 1)
	Vc27Fonts.bind(lab)
	lab.add_theme_color_override("font_color", Color("f7ebd2"))
	lab.add_theme_color_override("font_outline_color", Color("24170f"))
	lab.add_theme_constant_override("outline_size", 4)
	lab.add_theme_font_size_override("font_size", 12)
	box.add_child(lab)
	return box


func _btn(node_name: String, text: String, cb: Callable, icon_file: String = "") -> Button:
	var b := Button.new()
	b.name = node_name
	b.text = text
	Vc27Fonts.bind(b)
	b.add_theme_color_override("font_color", Color("f7ebd2"))
	b.add_theme_color_override("font_hover_color", Color("f7ebd2"))
	b.add_theme_color_override("font_pressed_color", Color("e6b65b"))
	b.add_theme_color_override("font_outline_color", Color("24170f"))
	b.add_theme_constant_override("outline_size", 4)
	b.add_theme_font_size_override("font_size", 14)
	b.add_theme_constant_override("h_separation", 2)
	b.clip_text = true
	b.add_theme_stylebox_override("normal", _btn_normal)
	b.add_theme_stylebox_override("hover", _btn_normal)
	b.add_theme_stylebox_override("pressed", _btn_pressed)
	b.add_theme_stylebox_override("disabled", _btn_disabled)
	b.add_theme_stylebox_override("focus", _btn_normal)
	b.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var icon := _icon(icon_file) if icon_file != "" else null
	if icon:
		b.icon = icon
		b.expand_icon = false
	b.pressed.connect(cb)
	return b


func _slice(file: String, margin: float, fallback: StyleBox, content: float = -1.0) -> StyleBox:
	var path := UI + file
	if not ResourceLoader.exists(path):
		return fallback
	var tex := load(path) as Texture2D
	if tex == null:
		return fallback
	var box := StyleBoxTexture.new()
	box.texture = tex
	box.texture_margin_left = margin
	box.texture_margin_top = margin
	box.texture_margin_right = margin
	box.texture_margin_bottom = margin
	var inset := margin if content < 0.0 else content
	box.content_margin_left = inset
	box.content_margin_top = inset
	box.content_margin_right = inset
	box.content_margin_bottom = inset
	box.draw_center = true
	return box


func _icon(file: String) -> Texture2D:
	if file == "":
		return null
	var path := UI + file
	if not ResourceLoader.exists(path):
		return null
	var tex := load(path) as Texture2D
	if tex == null or not file.ends_with("_32.png"):
		return tex
	var img := tex.get_image()
	if img == null:
		return tex
	img.resize(18, 18, Image.INTERPOLATE_NEAREST)
	return ImageTexture.create_from_image(img)


func _flat(fill: Color, border: Color) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = fill
	box.border_color = border
	box.set_border_width_all(2)
	box.set_corner_radius_all(10)
	box.content_margin_left = 8
	box.content_margin_right = 8
	box.content_margin_top = 4
	box.content_margin_bottom = 4
	box.shadow_color = Color(0.25, 0.12, 0.05, 0.28)
	box.shadow_size = 3
	return box


func _modal_btn(node_name: String) -> Button:
	return modal.find_child(node_name, true, false) as Button


func _safe() -> Rect2:
	var vp := get_viewport().get_visible_rect().size
	var win := DisplayServer.window_get_size()
	var safe := DisplayServer.get_display_safe_area()
	var p1 := Phase1Config.node("Phase1")
	if p1 and bool(p1.get("layout_override")):
		win = p1.get("layout_window")
		safe = p1.get("layout_safe")
		vp = p1.get("layout_viewport")
	if safe.size.x < 2 or safe.size.y < 2:
		if win.x < 2:
			win = Vector2i(int(vp.x), int(vp.y))
		safe = Rect2i(Vector2i.ZERO, win)
	var fit := 1.0
	var ox := 0.0
	var oy := 0.0
	if win.x > 0 and vp.x > 1.0:
		fit = minf(float(win.x) / vp.x, float(win.y) / vp.y)
		ox = (float(win.x) - vp.x * fit) * 0.5
		oy = (float(win.y) - vp.y * fit) * 0.5
	var left := maxf(0.0, (float(safe.position.x) - ox) / fit) + 8.0
	var top_y := maxf(0.0, (float(safe.position.y) - oy) / fit) + 4.0
	var right := minf(vp.x, (float(safe.position.x + safe.size.x) - ox) / fit) - 8.0
	var bottom := minf(vp.y, (float(safe.position.y + safe.size.y) - oy) / fit) - 4.0
	return Rect2(Vector2(left, top_y), Vector2(maxf(0.0, right - left), maxf(0.0, bottom - top_y)))
