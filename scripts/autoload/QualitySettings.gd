extends Node
## 低畫質係開發基線（穩定 30fps）。mid／high 只喺開發者模式切。
## Kurt 11-11 08:20：低畫質仍然係完整 3D 花園（同一場景、鏡頭、mesh、nav、遮擋）。
## 低只減成本：唔開 shadow map（腳底 blob 得）、唔開 glow／DoF／fog、較低 3D render scale、粒子較少。
## 永遠唔可以喺低畫質退回分層 2D。

enum Tier { LOW, MID, HIGH }

signal changed(tier: int)

var tier: int = Tier.LOW
var max_fps_low: int = 30

# 3D render scale（低細啲，場景同相機不變）
const SCALE_LOW := 0.67
const SCALE_MID := 1.0
const SCALE_HIGH := 1.0

func _ready() -> void:
	apply()


func set_tier(t: int) -> void:
	tier = clampi(t, Tier.LOW, Tier.HIGH)
	apply()
	changed.emit(tier)


func is_low() -> bool:
	return tier == Tier.LOW


func render_scale() -> float:
	if tier == Tier.HIGH:
		return SCALE_HIGH
	if tier == Tier.MID:
		return SCALE_MID
	return SCALE_LOW


func particle_budget() -> int:
	# G0 未有粒子；預留給之後。低 0／少，mid／high 先加。
	if tier == Tier.LOW:
		return 0
	if tier == Tier.MID:
		return 24
	return 48


func apply() -> void:
	if tier == Tier.LOW:
		Engine.max_fps = max_fps_low
	else:
		Engine.max_fps = 60
	var vp := get_viewport()
	if vp:
		vp.scaling_3d_scale = render_scale()
