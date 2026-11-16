extends RefCounted
## 3s idle fade for the observation UI. Appreciate forces it hidden.
## A pointer brings a faded panel back immediately.

var fade_sec := 3.0
var fade_out_sec := 0.35
var idle := 0.0
var alpha := 1.0
var appreciate := false


func note_input() -> void:
	idle = 0.0
	if not appreciate:
		alpha = 1.0


func toggle_appreciate() -> void:
	appreciate = not appreciate
	idle = 0.0
	alpha = 0.0 if appreciate else 1.0


func tick(dt: float) -> void:
	if appreciate:
		alpha = 0.0
		return
	idle += dt
	if idle >= fade_sec:
		var step := dt / maxf(fade_out_sec, 0.01)
		alpha = move_toward(alpha, 0.0, step)
