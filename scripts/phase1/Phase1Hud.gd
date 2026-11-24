class_name Phase1Hud
extends CanvasLayer

var root: Control
var top: Control
var dock: HBoxContainer
var feed_row: HBoxContainer
var train_row: HBoxContainer
var map_row: HBoxContainer
var drawer: PanelContainer
var toast: Label
var bubble: Label
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


func build() -> void:
	layer = 30
	root = Control.new()
	root.name = "Phase1Root"
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = Vc27Fonts.theme()
	add_child(root)
	top = Control.new()
	top.name = "TopBar"
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(top)
	name_btn = _btn("TopName", "小團絨 · 幼年期", _on_name)
	top.add_child(name_btn)
	var shard_pill := Panel.new()
	shard_pill.name = "ShardPill"
	var pill := StyleBoxFlat.new()
	pill.bg_color = Color(0.12, 0.08, 0.05, 0.72)
	pill.set_corner_radius_all(8)
	shard_pill.add_theme_stylebox_override("panel", pill)
	top.add_child(shard_pill)
	shard_lbl = Label.new()
	shard_lbl.name = "Shards"
	Vc27Fonts.bind(shard_lbl)
	shard_pill.add_child(shard_lbl)
	top.add_child(_btn("HideHud", "收起", _on_hide))
	top.add_child(_btn("OpenTools", "工具", _on_tools))
	for key in ["飽食", "心情", "親密", "體力"]:
		var bar := _bar(key)
		top.add_child(bar)
		bars[key] = bar
	dock = HBoxContainer.new()
	dock.name = "Dock"
	dock.add_theme_constant_override("separation", 6)
	root.add_child(dock)
	dock.add_child(_btn("DockFeed", "餵食", _call.bind("open_feed")))
	dock.add_child(_btn("DockClean", "清潔", _call.bind("clean")))
	dock.add_child(_btn("DockPat", "摸摸", _call.bind("pat")))
	dock.add_child(_btn("DockTrain", "鍛鍊", _call.bind("open_train")))
	dock.add_child(_btn("DockMap", "地圖", _call.bind("open_map")))
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
	var toast_bg := ColorRect.new()
	toast_bg.name = "ToastBg"
	toast_bg.color = Color(0.1, 0.07, 0.04, 0.82)
	toast_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	toast_bg.visible = false
	root.add_child(toast_bg)
	toast = Label.new()
	toast.name = "Toast"
	toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	Vc27Fonts.bind(toast)
	root.add_child(toast)
	bubble = Label.new()
	bubble.name = "Bubble"
	bubble.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	Vc27Fonts.bind(bubble)
	root.add_child(bubble)
	_build_drawer()
	_build_modal()
	apply_layout()
	refresh()


func apply_layout() -> void:
	var safe := _safe()
	top.position = safe.position
	top.size = Vector2(safe.size.x, 78)
	name_btn.position = Vector2(0, 0)
	name_btn.size = Vector2(safe.size.x * 0.46, 34)
	var pill_node := top.get_node("ShardPill") as Control
	pill_node.position = Vector2(safe.size.x * 0.46, 2)
	pill_node.size = Vector2(78, 32)
	shard_lbl.position = Vector2(8, 4)
	shard_lbl.size = Vector2(64, 24)
	var hide_b := top.get_node("HideHud") as Control
	var tool_b := top.get_node("OpenTools") as Control
	hide_b.position = Vector2(safe.size.x - 132, 0)
	hide_b.size = Vector2(60, 34)
	tool_b.position = Vector2(safe.size.x - 66, 0)
	tool_b.size = Vector2(64, 34)
	var i := 0
	for key in ["飽食", "心情", "親密", "體力"]:
		var bar := bars[key] as Control
		bar.position = Vector2(float(i) * (safe.size.x / 4.0), 40)
		bar.size = Vector2(safe.size.x / 4.0 - 6.0, 28)
		i += 1
	var dock_h := 56.0
	dock.position = Vector2(safe.position.x, safe.end.y - dock_h)
	dock.size = Vector2(safe.size.x, dock_h)
	for c in dock.get_children():
		if c is Control:
			(c as Control).custom_minimum_size = Vector2((safe.size.x - 24.0) / 5.0, 52)
	feed_row.position = Vector2(safe.position.x, dock.position.y - 48)
	train_row.position = feed_row.position
	map_row.position = Vector2(safe.position.x, dock.position.y - 48)
	for row in [feed_row, train_row, map_row]:
		row.size = Vector2(safe.size.x, 44)
	expand_btn.position = Vector2(safe.end.x - 72, safe.position.y)
	expand_btn.size = Vector2(68, 32)
	toast.position = Vector2(safe.position.x + 12, safe.position.y + 86)
	toast.size = Vector2(minf(220.0, safe.size.x - 24.0), 26)
	var toast_bg := root.get_node_or_null("ToastBg") as Control
	if toast_bg:
		toast_bg.position = toast.position
		toast_bg.size = toast.size
	bubble.position = Vector2(safe.position.x, safe.position.y + 130)
	bubble.size = Vector2(safe.size.x, 28)
	if drawer:
		drawer.position = Vector2(safe.position.x + 16, safe.position.y + 88)
		drawer.size = Vector2(safe.size.x - 32, 280)
	if modal:
		modal.position = Vector2(safe.position.x + 28, safe.position.y + 110)
		modal.size = Vector2(safe.size.x - 56, modal.get_combined_minimum_size().y)


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
		var fill := bar.get_node_or_null("Fill") as ColorRect
		if fill:
			fill.size.x = bar.size.x * clampf(float(care.get(key, 0)) / 100.0, 0.0, 1.0)
		var lab := bar.get_node_or_null("Cap") as Label
		if lab:
			lab.text = "%s %d" % [key, int(care.get(key, 0))]
	var zone := str(pet.get("zone_id", "garden"))
	for zid in zone_buttons.keys():
		var b := zone_buttons[zid] as Button
		b.modulate = Color(1, 0.92, 0.55) if zid == zone else Color.WHITE


func show_toast(text: String) -> void:
	toast.text = text
	var bg := root.get_node_or_null("ToastBg") as CanvasItem
	if bg:
		bg.visible = text != ""


func show_bubble(text: String) -> void:
	bubble.text = text


func show_modal(title: String, body: String) -> void:
	if drawer:
		drawer.visible = false
	show_toast("")
	show_bubble("")
	modal_title.text = title
	modal_body.text = body
	import_box.visible = false
	_modal_btn("ModalConfirm").visible = false
	_modal_btn("ModalCancel").visible = false
	_modal_btn("ModalClaim").visible = true
	modal.visible = true
	_fit_modal()


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


func _fit_modal() -> void:
	var box := modal.get_child(0) as Control
	if box:
		var h := box.get_combined_minimum_size().y + 16.0
		modal.size.y = h


func _modal_btn(node_name: String) -> Button:
	return modal.find_child(node_name, true, false) as Button


func set_collapsed(v: bool) -> void:
	collapsed = v
	top.visible = not v
	dock.visible = not v
	if v:
		feed_row.visible = false
		train_row.visible = false
		map_row.visible = false
		drawer.visible = false
	expand_btn.visible = v


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
	var box := VBoxContainer.new()
	drawer.add_child(box)
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
	var box := VBoxContainer.new()
	modal.add_child(box)
	modal_title = Label.new()
	modal_title.name = "ModalTitle"
	Vc27Fonts.bind(modal_title)
	box.add_child(modal_title)
	modal_body = Label.new()
	modal_body.name = "ModalBody"
	modal_body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	Vc27Fonts.bind(modal_body)
	box.add_child(modal_body)
	import_box = TextEdit.new()
	import_box.name = "ImportText"
	import_box.custom_minimum_size = Vector2(200, 80)
	import_box.visible = false
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


func _bar(key: String) -> Control:
	var box := Control.new()
	box.name = "Bar" + key
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bg := ColorRect.new()
	bg.color = Color(0.15, 0.1, 0.08, 0.35)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(bg)
	var fill := ColorRect.new()
	fill.name = "Fill"
	fill.color = Color(0.93, 0.62, 0.28, 0.9)
	fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(fill)
	var lab := Label.new()
	lab.name = "Cap"
	lab.text = key
	Vc27Fonts.bind(lab)
	box.add_child(lab)
	return box


func _btn(node_name: String, text: String, cb: Callable) -> Button:
	var b := Button.new()
	b.name = node_name
	b.text = text
	Vc27Fonts.bind(b)
	b.pressed.connect(cb)
	return b


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
