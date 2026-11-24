extends RefCounted
## Press / move / release. Swipe and long-press cancel the tap.

const Rules := preload("res://gameplay/m1_input_rules.gd")

var pressed := false
var origin := Vector2.ZERO
var last := Vector2.ZERO
var hold := 0.0
var fired := ""


func down(pos: Vector2) -> void:
	pressed = true
	origin = pos
	last = pos
	hold = 0.0
	fired = ""


func move(pos: Vector2) -> String:
	if not pressed:
		return ""
	last = pos
	if fired != "":
		return ""
	if origin.distance_to(pos) >= Rules.SWIPE_PX:
		fired = "swipe"
		return "swipe"
	return ""


func tick(dt: float) -> String:
	if not pressed or fired != "":
		return ""
	if origin.distance_to(last) >= Rules.SWIPE_PX:
		return ""
	hold += dt
	if hold >= Rules.LONG_PRESS_SEC:
		fired = "long"
		return "long"
	return ""


func up(pos: Vector2) -> String:
	if not pressed:
		return ""
	pressed = false
	last = pos
	if fired != "":
		fired = ""
		return ""
	if origin.distance_to(pos) >= Rules.SWIPE_PX:
		return "swipe"
	return "tap"


func swipe_dir() -> float:
	return last.x - origin.x
