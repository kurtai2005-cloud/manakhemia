extends Node
## 牆鐘、離線補時、裝置時鐘回撥防護。支援測試用假時鐘。

signal resumed(report: Dictionary)
signal day_rolled(kind: String, hour: int)

const STALL_SEC := 2.0
const ROLLBACK_IGNORE := true  # last_seen 只可向前
const MAX_AHEAD_H := 24.0

var _fake := false
var _fake_ms: int = 0
var _last_sim_ms: int = 0
var _last_jobs_day: String = ""
var _last_other_day: String = ""
var _in_catch_up := false

func _ready() -> void:
	_last_sim_ms = now_ms()


func use_fake(ms: int) -> void:
	_fake = true
	_fake_ms = ms


func clear_fake() -> void:
	_fake = false


func advance_fake(sec: float) -> void:
	_fake_ms += int(sec * 1000.0)


func now_ms() -> int:
	if _fake:
		return _fake_ms
	return int(Time.get_unix_time_from_system() * 1000.0)


func now_unix() -> int:
	return int(now_ms() / 1000)


func tz_bias_min() -> int:
	# Godot bias：本地相對 UTC 嘅分鐘（正數＝東，香港 +480）
	return int(Time.get_time_zone_from_system().get("bias", 0))


func local_dict(ms: int = -1) -> Dictionary:
	if ms < 0:
		ms = now_ms()
	# unix + bias → 用 UTC 解析器讀出本地牆鐘
	return Time.get_datetime_dict_from_unix_time(int(ms / 1000) + tz_bias_min() * 60)


func hour_of(ms: int = -1) -> float:
	if ms < 0:
		ms = now_ms()
	var dict := local_dict(ms)
	return float(dict["hour"]) + float(dict["minute"]) / 60.0 + float(dict["second"]) / 3600.0


func date_key(ms: int = -1, at_hour: int = 0) -> String:
	if ms < 0:
		ms = now_ms()
	# 日界：jobs 用 05:00，其他 00:00 — 把鐘倒退到該日界再取本地日期
	var shift_ms := at_hour * 3600 * 1000
	var adj := ms - shift_ms
	var dict := local_dict(adj)
	return "%04d-%02d-%02d" % [dict["year"], dict["month"], dict["day"]]


func is_moon_sleep(ms: int = -1) -> bool:
	var h := hour_of(ms)
	return h >= 20.0 or h < 3.0


func local_wall_ms(hour: float, minute: float = 0.0, year: int = 2026, month: int = 11, day: int = 11) -> int:
	# 造一個「本地牆鐘」毫秒，俾 QA 截圖把 HUD 時鐘同日夜段對齊。
	var bias := tz_bias_min() * 60
	var midnight := Time.get_unix_time_from_datetime_dict({
		"year": year, "month": month, "day": day, "hour": 0, "minute": 0, "second": 0,
	})
	var sec := int(midnight + hour * 3600.0 + minute * 60.0) - bias
	return sec * 1000


func hour_band(ms: int = -1) -> String:
	# 時段 BGM／燈光：05–11 早、11–17 午、17–22 晚、22–05 夜。唔好用 is_moon_sleep（20–03）。
	var h := hour_of(ms)
	if h >= 5.0 and h < 11.0:
		return "morning"
	if h >= 11.0 and h < 17.0:
		return "noon"
	if h >= 17.0 and h < 22.0:
		return "evening"
	return "night"


func mark_sim() -> void:
	_last_sim_ms = now_ms()


func catch_up(state: Dictionary, sim_at_ms: int = -1) -> Dictionary:
	if state.is_empty():
		return {"skipped": true, "T": 0.0}
	var now := now_ms()
	# resume + focus 可能叠住入嚟：重入直接跳過；同一 last_seen 補完後第二次 gap < stall（sim.js catchUp）
	if _in_catch_up:
		return {"skipped": true, "T": 0.0, "show": false, "duplicate": true}
	_in_catch_up = true
	var rep := _catch_up_body(state, sim_at_ms, now)
	_in_catch_up = false
	return rep


func _catch_up_body(state: Dictionary, sim_at_ms: int, now: int) -> Dictionary:
	if sim_at_ms < 0:
		sim_at_ms = _last_sim_ms if _last_sim_ms > 0 else int(state.get("last_seen", now))
	var last := int(state.get("last_seen", now))
	# 回撥：唔把 last_seen 拉後
	if now < last:
		return {"skipped": true, "T": 0.0, "rollback": true, "show": false}
	# 超前存檔 >24h：當無效，重設、呢段唔派離線成長
	var last_save := int(state.get("last_save_time", last))
	if last_save > now + int(MAX_AHEAD_H * 3600.0 * 1000.0):
		state["last_seen"] = now
		state["last_save_time"] = now
		state["save_resets"] = int(state.get("save_resets", 0)) + 1
		_last_sim_ms = now
		return {"skipped": false, "tampered": true, "T": 0.0, "show": false}
	# sim_at 只可以補「已經模擬到」嘅點，唔可以超過而家（避免同假時鐘交叉）
	if sim_at_ms > 0:
		last = max(last, min(sim_at_ms, now))
	state["last_seen"] = last
	var gap := float(now - last) / 1000.0
	if gap < STALL_SEC:
		return {"skipped": true, "T": gap, "show": false}
	var rep: Dictionary = Sim.apply_offline(state, now)
	_check_rollover(state, last, now)
	_last_sim_ms = now
	if int(rep.get("gift", 0)) > 0 and AudioManager:
		AudioManager.play("sfx_event_gift_return")
	return rep


func _check_rollover(state: Dictionary, from_ms: int, to_ms: int) -> void:
	var jobs_h := GameData.day_jobs_hour()
	var other_h := GameData.day_other_hour()
	var jobs_from := date_key(from_ms, jobs_h)
	var jobs_to := date_key(to_ms, jobs_h)
	if jobs_from != jobs_to:
		state["jobs_day"] = jobs_to
		day_rolled.emit("jobs_trips", jobs_h)
	var other_from := date_key(from_ms, other_h)
	var other_to := date_key(to_ms, other_h)
	if other_from != other_to:
		state["other_day"] = other_to
		day_rolled.emit("other", other_h)


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_RESUMED or what == NOTIFICATION_WM_WINDOW_FOCUS_IN:
		if has_node("/root/Sim") and Sim.state:
			var rep := catch_up(Sim.state)
			if not rep.get("skipped", true):
				Sim.after_catch_up(rep)
				resumed.emit(rep)
