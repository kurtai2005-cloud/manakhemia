extends SceneTree
## Headless smoke: load vc26-touched scripts/shaders + main scene resource (not just exit 0).


func _initialize() -> void:
	var paths := [
		"res://scenes/art_depth.gd",
		"res://scenes/capture.gd",
		"res://shaders/ground_dapple.gdshader",
		"res://shaders/texel_lit.gdshader",
		"res://shaders/tuft.gdshader",
		"res://shaders/near_lawn.gdshader",
	]
	for p in paths:
		var scr: Variant = load(p)
		if scr == null:
			push_error("gdscript_parse_smoke: failed to load %s" % p)
			quit(1)
			return
	var scene: Variant = load("res://scenes/capture.tscn")
	if scene == null:
		push_error("gdscript_parse_smoke: failed to load capture.tscn")
		quit(1)
		return
	print("gdscript_parse_smoke: ok scripts=", paths.size(), " scene=capture.tscn")
	quit(0)