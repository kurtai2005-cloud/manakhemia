extends Node
## 版本化存檔，原子寫入（tmp → rename），帶 migrations 鉤子。

const VERSION := 1
const SAVE_PATH := "user://save_v1.json"
const TMP_PATH := "user://save_v1.json.tmp"
const OVERLAY_PATH := "user://overlay_snapshot.json"

var last_overlay_snapshot: Dictionary = {}

func load_state() -> Dictionary:
	if not FileAccess.file_exists(SAVE_PATH):
		return {}
	var raw := FileAccess.get_file_as_string(SAVE_PATH)
	if raw.strip_edges() == "":
		return {}
	var parsed: Variant = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_warning("SaveSystem: corrupt save, ignored")
		return {}
	var data: Dictionary = parsed
	var v := int(data.get("version", 0))
	if v < VERSION:
		data = migrate(data, v, VERSION)
	return data


func save_state(data: Dictionary) -> bool:
	var out := data.duplicate(true)
	out["version"] = VERSION
	var json := JSON.stringify(out)
	var f := FileAccess.open(TMP_PATH, FileAccess.WRITE)
	if f == null:
		push_error("SaveSystem: cannot write tmp")
		return false
	f.store_string(json)
	f.flush()
	f.close()
	# 原子：Godot 冇 rename overwrite 保證；先刪舊再搬
	if FileAccess.file_exists(SAVE_PATH):
		DirAccess.remove_absolute(SAVE_PATH)
	var err := DirAccess.rename_absolute(TMP_PATH, SAVE_PATH)
	if err != OK:
		push_error("SaveSystem: rename failed " + str(err))
		return false
	write_overlay_snapshot(out)
	return true


func migrate(data: Dictionary, from_v: int, to_v: int) -> Dictionary:
	# G0：v0／缺 version → v1 原樣升。之後加欄位喺呢度逐步搬。
	var cur := from_v
	var out := data.duplicate(true)
	while cur < to_v:
		cur += 1
		out["version"] = cur
	return out


func clear() -> void:
	if FileAccess.file_exists(SAVE_PATH):
		DirAccess.remove_absolute(SAVE_PATH)
	if FileAccess.file_exists(TMP_PATH):
		DirAccess.remove_absolute(TMP_PATH)


func build_overlay_snapshot(s: Dictionary) -> Dictionary:
	# v3：心情／瞌覺／需求，畀 PetOverlayService 讀 CapacitorStorage glimmer.snapshot
	var n: Dictionary = (s.get("needs", {}) as Dictionary).duplicate(true)
	var mood := float(n.get("mood", 70))
	var energy := float(n.get("energy", 70))
	var band := "happy"
	if bool(s.get("sleeping", false)) or energy < 30.0:
		band = "sleepy"
	elif mood < 40.0:
		band = "sad"
	elif mood < 70.0:
		band = "ok"
	var urgent := ""
	var best := 101.0
	for k in ["hunger", "mood", "clean", "energy"]:
		var v := float(n.get(k, 100))
		if v < 30.0 and v < best:
			best = v
			urgent = k
	return {
		"v": 3,
		"form": (str(s.get("form", "soft")) if str(s.get("form", "")) != "" else "soft"),
		"evoForm": str(s.get("form", "")),
		"mood": mood,
		"ts": TimeService.now_ms() if TimeService else 0,
		"egg": str(s.get("stage", "")) == "egg",
		"moodBand": band,
		"sleeping": bool(s.get("sleeping", false)),
		"stage": str(s.get("stage", "")),
		"needs": {
			"urgent": urgent if urgent != "" else null,
			"warnAt": 30.0,
			"vals": n,
			"floor": 20.0,
			"wakeAt": 100.0,
		},
	}


func write_overlay_snapshot(s: Dictionary) -> Dictionary:
	var snap := build_overlay_snapshot(s)
	last_overlay_snapshot = snap
	var json := JSON.stringify(snap)
	var f := FileAccess.open(OVERLAY_PATH, FileAccess.WRITE)
	if f:
		f.store_string(json)
		f.flush()
		f.close()
	if Engine.has_singleton("GlimmerOverlay"):
		Engine.get_singleton("GlimmerOverlay").call("writeSnapshot", json)
	return snap

