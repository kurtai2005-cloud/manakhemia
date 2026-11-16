extends Node

## Fixture-only. job "zero" runs before art_depth and shows it offset 0.
## job "restore" runs after art_depth and puts the grounded feet back for the draw.
var job := "restore"


func _process(_dt: float) -> void:
	var host := get_parent()
	if host == null or str(host.get_meta("vc27_shadow_force", "")) != "uncorrected":
		return
	if not host.has_method("set_foot_visual_anchor"):
		return
	if job == "zero":
		host.call("set_foot_visual_anchor", false)
	else:
		host.call("set_foot_visual_anchor", true)
		var pet := host.get("_pet") as Sprite3D
		if pet != null:
			host.set_meta("vc27_draw_offset", pet.offset.y)
