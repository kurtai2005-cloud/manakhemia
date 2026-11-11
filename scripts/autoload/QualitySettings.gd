extends Node
## 低畫質係開發基線。mid／high 只喺開發者模式切。

enum Tier { LOW, MID, HIGH }

signal changed(tier: int)

var tier: int = Tier.LOW
var max_fps_low: int = 30

func _ready() -> void:
	apply()


func set_tier(t: int) -> void:
	tier = clampi(t, Tier.LOW, Tier.HIGH)
	apply()
	changed.emit(tier)


func is_low() -> bool:
	return tier == Tier.LOW


func apply() -> void:
	if tier == Tier.LOW:
		Engine.max_fps = max_fps_low
	else:
		Engine.max_fps = 60
	# shadows / glow 由花園場景跟呢個旗標開關
