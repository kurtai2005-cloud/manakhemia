class_name Vc27Fonts
extends RefCounted
## One UI font: the game subset, then the CJK fallback. Android has no system CJK.

const PATH_R := "res://art/fonts/GenWanMin2TC-R.subset.otf"
const PATH_SB := "res://art/fonts/GenWanMin2TC-SB.subset.otf"
const PATH_FB := "res://art/fonts/vc27_label_fallback.otf"
const PATH_DEFAULT := "res://assets/fonts/vc27_default_font.tres"
const PATH_THEME := "res://assets/fonts/vc27_default_theme.tres"


static func ensure() -> Font:
	var fb := load(PATH_FB) as Font
	_attach(load(PATH_R) as Font, fb)
	_attach(load(PATH_SB) as Font, fb)
	var face := load(PATH_DEFAULT) as Font
	if face == null:
		face = load(PATH_R) as Font
	_attach(face, fb)
	if face is FontVariation:
		_attach((face as FontVariation).base_font, fb)
	return face


static func theme() -> Theme:
	ensure()
	return load(PATH_THEME) as Theme


static func bind(node: Control) -> void:
	var face := ensure()
	if node == null or face == null:
		return
	node.add_theme_font_override("font", face)


static func _attach(face: Font, fb: Font) -> void:
	if face == null or fb == null:
		return
	var next: Array[Font] = []
	next.assign(face.fallbacks)
	for item in next:
		if item == fb:
			return
	next.append(fb)
	face.fallbacks = next
