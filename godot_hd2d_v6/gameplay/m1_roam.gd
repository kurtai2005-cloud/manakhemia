extends RefCounted
## Idle + roam for the pilot pet.
## Adapted from mainline Walker (speed, arrival, idle pause, repick when blocked)
## and PetBrain wander (a nearby reachable point; farther when social is low).
## Manual go_to takes the same precedence as Walker.go_to.
## Care and the observe camera do not clear the current target.
## Bounds and cottage/fence rects come from data/prop_bump.json.
## The prop circles are the points capture already refuses while walking.
## No new care or economy numbers. No walk-cycle art.

const SPEED := 20.0
const PAUSE_MIN := 1.2
const PAUSE_MAX := 3.5
const ARRIVE := 1.5
const PICK_MIN := 20.0
const PICK_NEAR := 70.0
const PICK_FAR := 120.0
const SOCIAL_FAR := -5
const PROP_R := 10.0
const ACTOR := "tuanrong"

var cause := "none"
var motion := "none"
var care_hold := false
var walk_sec := 0.0
var dest: Variant = null
var x_min := -140.0
var x_max := 150.0
var z_min := -110.0
var z_max := 90.0
# Same back-left cut as capture.gd, so roam does not enter the tree.
var back_z := -70.0
var back_x := -110.0

var _manual := false
var _pause := 0.0
var _stash: Variant = null
var _rng := RandomNumberGenerator.new()
var _seeded := false
var _booted := false
var _rects: Array[Rect2] = []
var _props: Array[Vector2] = []


func boot() -> void:
	if _booted:
		return
	_booted = true
	if not _seeded:
		_rng.randomize()
	_load_garden()


func seed(s: int) -> void:
	_rng.seed = s
	_seeded = true


func set_care_hold(on: bool) -> void:
	# Freeze stepping. The destination stays where it was.
	care_hold = on


func note_camera() -> void:
	# Follow and overview move the camera only.
	pass


func begin_manual() -> void:
	if _manual:
		return
	_manual = true
	if dest != null:
		_stash = dest
	_pause = 0.0
	cause = "tap_directed"
	motion = "walk"


func notify_manual_done() -> void:
	_manual = false
	if _stash != null:
		dest = _stash
		_stash = null
		_pause = 0.0
		cause = "autonomous"
		motion = "walk"
		return
	dest = null
	_pause = _rng.randf_range(PAUSE_MIN, PAUSE_MAX)
	cause = "autonomous"
	motion = "idle"


func tick(pos: Vector2, dt: float, mul: float, social: int) -> Vector2:
	boot()
	if _manual:
		cause = "tap_directed"
		motion = "walk"
		return pos
	if care_hold:
		if cause == "none":
			cause = "autonomous"
		motion = "hold"
		return pos
	if _pause > 0.0:
		_pause = maxf(0.0, _pause - dt)
		cause = "autonomous"
		motion = "idle"
		if _pause <= 0.0 and dest == null:
			var picked := choose_dest(pos, social)
			if picked.distance_to(pos) > ARRIVE:
				dest = picked
		return pos
	if dest == null:
		var picked := choose_dest(pos, social)
		if picked.distance_to(pos) <= ARRIVE:
			_pause = _rng.randf_range(PAUSE_MIN, PAUSE_MAX)
			cause = "autonomous"
			motion = "idle"
			return pos
		dest = picked
	var goal: Vector2 = dest
	var delta := goal - pos
	var dist := delta.length()
	if dist <= ARRIVE:
		dest = null
		_pause = _rng.randf_range(PAUSE_MIN, PAUSE_MAX)
		cause = "autonomous"
		motion = "idle"
		return pos
	var step_len := SPEED * maxf(mul, 0.1) * dt
	var nxt := pos + delta * (minf(step_len, dist) / dist)
	if not garden_free(nxt):
		# Do not enter the house, fence, or a prop. Pick another free point.
		dest = null
		cause = "autonomous"
		motion = "idle"
		return pos
	cause = "autonomous"
	motion = "walk"
	walk_sec += dt
	return nxt


func far_free(origin: Vector2) -> Vector2:
	return _farthest(origin, Callable())


func far_visible(origin: Vector2, accept: Callable) -> Vector2:
	# Trace-only filter. Autonomous pick still uses choose_dest.
	return _farthest(origin, accept)


func _farthest(origin: Vector2, accept: Callable) -> Vector2:
	boot()
	var spots: Array[Vector2] = [
		Vector2(110, -30), Vector2(-40, 10), Vector2(0, 75),
		Vector2(120, 20), Vector2(-90, 40), Vector2(90, 50),
		Vector2(-70, 10), Vector2(40, -25),
	]
	var best := origin
	var best_d := 0.0
	for s in spots:
		var p := clamp_walk(s)
		if not segment_free(origin, p):
			continue
		if accept.is_valid() and not bool(accept.call(p)):
			continue
		var d := origin.distance_to(p)
		if d > best_d:
			best_d = d
			best = p
	return best


func choose_dest(origin: Vector2, social: int) -> Vector2:
	boot()
	var reach := PICK_FAR if social <= SOCIAL_FAR else PICK_NEAR
	var fallback := origin
	for _i in 40:
		var ang := _rng.randf() * TAU
		var dist := _rng.randf_range(PICK_MIN, reach)
		var p := clamp_walk(origin + Vector2(cos(ang), sin(ang)) * dist)
		if p.distance_to(origin) < PICK_MIN:
			continue
		if segment_free(origin, p):
			return p
		if garden_free(p) and segment_free(origin, p):
			fallback = p
	if garden_free(fallback) and segment_free(origin, fallback) and fallback.distance_to(origin) >= ARRIVE:
		return fallback
	return origin


func garden_blocked(p: Vector2) -> bool:
	boot()
	for r in _rects:
		if r.has_point(p):
			return true
	for q in _props:
		if p.distance_to(q) < PROP_R:
			return true
	return false


func garden_free(p: Vector2) -> bool:
	return inside_walk(p) and not garden_blocked(p)


func inside_walk(p: Vector2) -> bool:
	if p.x < x_min or p.x > x_max or p.y < z_min or p.y > z_max:
		return false
	if p.y < back_z and p.x < back_x:
		return false
	return true


func clamp_walk(p: Vector2) -> Vector2:
	var c := Vector2(clampf(p.x, x_min, x_max), clampf(p.y, z_min, z_max))
	if c.y < back_z:
		c.x = maxf(c.x, back_x)
	return c


func segment_free(a: Vector2, b: Vector2) -> bool:
	if not garden_free(a) or not garden_free(b):
		return false
	var dist := a.distance_to(b)
	if dist <= 0.01:
		return true
	var n := int(dist / 2.0) + 1
	for i in n + 1:
		var p := a.lerp(b, float(i) / float(n))
		if not garden_free(p):
			return false
	return true


func _load_garden() -> void:
	_props = [
		Vector2(-72.5, 22), Vector2(71, 24), Vector2(-39, 42), Vector2(35, 22),
		Vector2(-81, 70), Vector2(81, 54), Vector2(49, 22), Vector2(22, 18),
		Vector2(-24, 28), Vector2(48, 48), Vector2(18, 8), Vector2(-15, 35),
		Vector2(30, -20),
	]
	var f := FileAccess.open("res://data/prop_bump.json", FileAccess.READ)
	if f == null:
		return
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if not (parsed is Dictionary):
		return
	var cfg: Dictionary = parsed
	var bounds: Dictionary = cfg.get("bounds", {})
	x_min = float(bounds.get("x_min", x_min))
	x_max = float(bounds.get("x_max", x_max))
	z_min = float(bounds.get("z_min", z_min))
	z_max = float(bounds.get("z_max", z_max))
	_rects.clear()
	for row in cfg.get("blocked_rects", []):
		if not (row is Dictionary):
			continue
		var rd: Dictionary = row
		_rects.append(Rect2(float(rd.get("x", 0)), float(rd.get("z", 0)), float(rd.get("w", 0)), float(rd.get("h", 0))))
