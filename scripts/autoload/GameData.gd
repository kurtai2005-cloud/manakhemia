extends Node
## 載入遊策 JSON（保留 _src／_missing／_doc_vs_code 欄）。

var economy: Dictionary = {}
var evolution: Dictionary = {}
var personality: Dictionary = {}
var hunting: Dictionary = {}
var sim: Dictionary = {}
var m1a: Dictionary = {}

const NEED_KEYS: PackedStringArray = ["hunger", "mood", "clean", "energy"]

func _ready() -> void:
	economy = _load_json("res://data/economy.json")
	evolution = _load_json("res://data/evolution.json")
	personality = _load_json("res://data/personality.json")
	hunting = _load_json("res://data/hunting.json")
	sim = _load_json("res://data/sim.json")
	m1a = _load_json("res://data/m1a.json")


func _load_json(path: String) -> Dictionary:
	var raw := FileAccess.get_file_as_string(path)
	var parsed: Variant = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("GameData: failed to parse " + path)
		return {}
	return parsed


func stage_list() -> Array:
	var stages: Dictionary = evolution.get("stages", {})
	return stages.get("list", [])


func stage_duration(stage_id: String) -> float:
	for s in stage_list():
		if s is Dictionary and str(s.get("id", "")) == stage_id:
			return float(s.get("duration_sec", 0))
	return 0.0


func stage_zh(stage_id: String) -> String:
	for s in stage_list():
		if s is Dictionary and str(s.get("id", "")) == stage_id:
			return str(s.get("zh", stage_id))
	return stage_id


func next_stage(stage_id: String) -> String:
	var ids: Array = []
	for s in stage_list():
		if s is Dictionary:
			ids.append(str(s.get("id", "")))
	var i := ids.find(stage_id)
	if i < 0 or i >= ids.size() - 1:
		return ""
	return str(ids[i + 1])


func day_jobs_hour() -> int:
	var dc: Dictionary = economy.get("day_change", {})
	return int(dc.get("jobs_and_trips_hour", 5))


func day_other_hour() -> int:
	var dc: Dictionary = economy.get("day_change", {})
	return int(dc.get("old_sources_and_steps_hour", 0))
