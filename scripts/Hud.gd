extends CanvasLayer
## 最簡 HUD：階段、需求、隱藏 UI、開發者模式。GenWanMin2 TC。

var font: Font
var root: Control
var bar_box: VBoxContainer
var stage_lbl: Label
var time_lbl: Label
var need_lbl: Label
var hide_btn: Button
var dev_btn: Button
var dev_panel: PanelContainer
var hidden := false

func _ready() -> void:
	layer = 20
	font = load("res://art/fonts/GenWanMin2TC-R.subset.otf")
	root = Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)

	bar_box = VBoxContainer.new()
	bar_box.position = Vector2(16, 16)
	bar_box.custom_minimum_size = Vector2(280, 0)
	bar_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(bar_box)

	stage_lbl = _lbl("", 22)
	bar_box.add_child(stage_lbl)
	time_lbl = _lbl("", 16)
	bar_box.add_child(time_lbl)
	need_lbl = _lbl("", 16)
	bar_box.add_child(need_lbl)

	hide_btn = _btn("隱藏界面")
	hide_btn.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	hide_btn.position = Vector2(16, -64)
	hide_btn.offset_left = 16
	hide_btn.offset_top = -72
	hide_btn.offset_right = 160
	hide_btn.offset_bottom = -24
	hide_btn.anchor_left = 0
	hide_btn.anchor_top = 1
	hide_btn.anchor_right = 0
	hide_btn.anchor_bottom = 1
	hide_btn.pressed.connect(_toggle_hide)
	root.add_child(hide_btn)

	dev_btn = _btn("開發者")
	dev_btn.anchor_left = 1
	dev_btn.anchor_top = 1
	dev_btn.anchor_right = 1
	dev_btn.anchor_bottom = 1
	dev_btn.offset_left = -160
	dev_btn.offset_top = -72
	dev_btn.offset_right = -16
	dev_btn.offset_bottom = -24
	dev_btn.pressed.connect(_toggle_dev)
	root.add_child(dev_btn)

	_build_dev()
	dev_panel.visible = false
	Sim.state_changed.connect(_refresh)
	_refresh()


func _lbl(t: String, size: int) -> Label:
	var l := Label.new()
	l.text = t
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
	b.add_theme_font_override("font", font)
	b.add_theme_font_size_override("font_size", 18)
	b.custom_minimum_size = Vector2(120, 44)
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
	dev_panel.offset_bottom = 320
	var vb := VBoxContainer.new()
	dev_panel.add_child(vb)
	var t := _lbl("開發者模式", 18)
	vb.add_child(t)
	for item in [["低畫質（基線）", QualitySettings.Tier.LOW], ["中畫質", QualitySettings.Tier.MID], ["高畫質", QualitySettings.Tier.HIGH]]:
		var b := _btn(str(item[0]))
		var tier: int = item[1]
		b.pressed.connect(func(): QualitySettings.set_tier(tier))
		vb.add_child(b)
	var b_poop := _btn("加一粒便便")
	b_poop.pressed.connect(func(): Sim.add_poop())
	vb.add_child(b_poop)
	var b_slp := _btn("切換睡眠")
	b_slp.pressed.connect(func(): Sim.set_sleeping(not bool(Sim.state.get("sleeping", false))))
	vb.add_child(b_slp)
	var b_h := _btn("快轉 +1 小時")
	b_h.pressed.connect(_ff_hour)
	vb.add_child(b_h)
	root.add_child(dev_panel)


func _ff_hour() -> void:
	Sim.advance(Sim.state, 3600.0, {})
	Sim.state["last_seen"] = TimeService.now_ms()
	Sim.state_changed.emit()
	Sim.poops_changed.emit(int(Sim.state.get("poops", 0)))


func _toggle_hide() -> void:
	hidden = not hidden
	bar_box.visible = not hidden
	dev_btn.visible = not hidden
	dev_panel.visible = dev_panel.visible and not hidden
	hide_btn.text = "顯示界面" if hidden else "隱藏界面"


func _toggle_dev() -> void:
	if hidden:
		return
	dev_panel.visible = not dev_panel.visible


func _refresh() -> void:
	if hidden:
		return
	var s := Sim.state
	var form := str(s.get("form", ""))
	var form_names := {"bright": "燦光", "soft": "柔光", "dust": "微塵", "lumi": "螢絨", "tide": "潮汐", "shroom": "菇傘", "crystal": "晶角", "moon": "月眠", "ember": "火苗"}
	var form_zh: String = str(form_names.get(form, form))
	var extra := "" if form == "" else " · " + str(form_zh)
	stage_lbl.text = "微光小圃  " + Sim.stage_zh() + extra
	var n: Dictionary = s.get("needs", {})
	var slp := "  月眠中" if bool(s.get("sleeping", false)) else ""
	need_lbl.text = "飢 %d  心 %d  潔 %d  力 %d%s" % [
		int(n.get("hunger", 0)), int(n.get("mood", 0)), int(n.get("clean", 0)), int(n.get("energy", 0)), slp
	]


func _process(_dt: float) -> void:
	if hidden or time_lbl == null:
		return
	var ms := TimeService.now_ms()
	var d: Dictionary = TimeService.local_dict(ms)
	time_lbl.text = "%02d:%02d" % [int(d["hour"]), int(d["minute"])]
	# 需求每秒刷新足夠
	_refresh()
