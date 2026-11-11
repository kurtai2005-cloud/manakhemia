extends Node
## 版本化存檔，原子寫入（tmp → rename），帶 migrations 鉤子。

const VERSION := 1
const SAVE_PATH := "user://save_v1.json"
const TMP_PATH := "user://save_v1.json.tmp"

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
