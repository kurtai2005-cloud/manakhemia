extends Node
## 資料驅動美術匯入：讀 遊美 godot_import.json／CLIPS.json／environments.json／anim_timing.json。
## clip 時機同 SFX cue 只由 anim_timing.json 驅動（正式檔由遊美發布；未到之前用由 CLIPS 衍生嘅草稿）。
## 唔好喺腳本寫死幀數、fps、逐幀時長。

signal sfx_cue(clip: String, hook: String, frame: int, actor: Object)

const CLIPS_PATH := "res://art/liveliness/CLIPS.json"
const TIMING_PATHS: PackedStringArray = [
	"res://art-pet/anim_timing.json",  # 遊美正式單一來源（發布後放呢度）
	"res://art/import/anim_timing.json",
	"res://art/anim_timing.json",  # CLIPS 衍生草稿，正式檔未到先用
]
const ATLAS_PATHS: PackedStringArray = [
	"res://art/liveliness/atlas_radiant_live.json",
	"res://art/liveliness/atlas_radiant_live_s2.json",
]
const GODOT_IMPORT_PATHS: PackedStringArray = [
	"res://art/import/godot_import.json",
	"res://art/m2-actions/godot_import.json",
]
const ENV_PATH := "res://art/import/environments.json"
const ACTOR_ANIM_PATH := "res://data/actor_anim.json"

var clips_doc: Dictionary = {}
var timing: Dictionary = {}  # clip name -> timing dict
var environments: Dictionary = {}
var actor_anim: Dictionary = {}
var import_docs: Array = []
var _atlases: Array = []  # {json, texture, dir, frame_size}
var _tex_cache: Dictionary = {}  # "scratch" or "scratch@M" -> Array[Texture2D]


func _ready() -> void:
	_load_all()


func _load_all() -> void:
	clips_doc = _json(CLIPS_PATH)
	timing = {}
	# 正式 art-pet/anim_timing.json 優先；草稿／CLIPS 補官方冇嘅 liveliness clip
	for tp in TIMING_PATHS:
		_merge_timing(_json(tp))
	_merge_clips_fallback()
	environments = _json(ENV_PATH)
	actor_anim = _json(ACTOR_ANIM_PATH)
	import_docs.clear()
	for p in GODOT_IMPORT_PATHS:
		var d := _json(p)
		if not d.is_empty():
			import_docs.append(d)
	_atlases.clear()
	for p in ATLAS_PATHS:
		var doc := _json(p)
		if doc.is_empty():
			continue
		var meta: Dictionary = doc.get("meta", {})
		var dir := p.get_base_dir() + "/"
		var img := str(meta.get("image", ""))
		var tex: Texture2D = load(dir + img) if img != "" else null
		var frame_size := float(meta.get("frameSize", 64))
		_atlases.append({"doc": doc, "tex": tex, "dir": dir, "frame_size": frame_size})
	_tex_cache.clear()
	# 預熱生命感 2–3 條（同 mood walk／nuzzle／rush）
	for name in ["scratch", "sneeze", "sniff", "nuzzle", "rush", "walk_happy", "walk_drag"]:
		frames_of(name)


func _json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var raw := FileAccess.get_file_as_string(path)
	var p: Variant = JSON.parse_string(raw)
	return p if typeof(p) == TYPE_DICTIONARY else {}


func _merge_timing(raw: Dictionary) -> void:
	if raw.is_empty():
		return
	var c: Variant = raw.get("clips", {})
	if c is Array:
		for item in c:
			if not (item is Dictionary):
				continue
			var id := str(item.get("id", ""))
			if id == "" or timing.has(id):
				continue
			timing[id] = _normalize_official(item)
	elif c is Dictionary:
		for k in c.keys():
			if timing.has(str(k)):
				continue
			var v = c[k]
			if v is Dictionary:
				timing[str(k)] = _normalize_draft(str(k), v)


func _normalize_official(item: Dictionary) -> Dictionary:
	var durs: Array = item.get("frameMs", [])
	var evs: Array = []
	for e in item.get("events", []):
		if not (e is Dictionary):
			continue
		var hook = e.get("sfx_hook", null)
		var fi := int(e.get("frameIndex", 0))
		evs.append({
			"id": str(e.get("id", "")),
			"hook": hook,
			"sfx_hook": hook,
			"frameIndex": fi,
			"frame": fi + 1,
			"t_ms": int(e.get("t_ms", 0)),
			"accent": str(e.get("accent", "")),
		})
	return {
		"frames": int(item.get("frameCount", durs.size())),
		"fps": float(item.get("fps", 8)),
		"frame_durations_ms": durs,
		"loop": bool(item.get("loop", false)),
		"sizes": item.get("sizes", []),
		"events": evs,
		"sfx": evs,
	}


func _normalize_draft(name: String, item: Dictionary) -> Dictionary:
	var n := int(item.get("frames", 0))
	var fps := float(item.get("fps", 8))
	var durs: Array = item.get("frame_durations_ms", [])
	if durs.is_empty() and n > 0:
		var dur := int(round(1000.0 / maxf(fps, 0.001)))
		for _i in range(n):
			durs.append(dur)
	var evs: Array = []
	for e in item.get("sfx", []):
		if not (e is Dictionary):
			continue
		var fr := int(e.get("frame", 0))  # 草稿 1-based
		var fi := fr - 1 if fr > 0 else int(e.get("frameIndex", 0))
		var hook = e.get("sfx_hook", e.get("hook", null))
		if hook == null:
			var id := str(e.get("id", ""))
			# 草稿 id "sneeze" → sfx_pet_sneeze_a（a/b 由 AudioManager 揀）
			if id != "":
				hook = "sfx_pet_%s_a" % id if not id.begins_with("sfx_") else id
		evs.append({
			"id": str(e.get("id", "")),
			"hook": hook,
			"sfx_hook": hook,
			"frameIndex": fi,
			"frame": fi + 1,
			"t_ms": int(e.get("t_ms", e.get("time_ms", 0))),
			"accent": str(e.get("accent", "")),
		})
	# 已知 liveliness：scratch 通用、sneeze 有聲線；sniff 暫無專屬檔（null＝靜音）
	if evs.is_empty():
		if name == "scratch":
			evs.append({"id": "scratch", "hook": "sfx_pet_scratch_a", "sfx_hook": "sfx_pet_scratch_a", "frameIndex": 2, "frame": 3, "t_ms": 2 * int(round(1000.0 / maxf(fps, 0.001))), "accent": "peak"})
		elif name == "sneeze":
			evs.append({"id": "sneeze", "hook": "sfx_pet_sneeze_a", "sfx_hook": "sfx_pet_sneeze_a", "frameIndex": 2, "frame": 3, "t_ms": 2 * int(round(1000.0 / maxf(fps, 0.001))), "accent": "peak"})
		elif name == "sniff":
			evs.append({"id": "sniff", "hook": null, "sfx_hook": null, "frameIndex": 1, "frame": 2, "t_ms": int(round(1000.0 / maxf(fps, 0.001))), "accent": "peak"})
	return {
		"frames": n,
		"fps": fps,
		"frame_durations_ms": durs,
		"loop": bool(item.get("loop", false)),
		"events": evs,
		"sfx": evs,
	}


func _merge_clips_fallback() -> void:
	# official 未收 scratch／sneeze／sniff 時，用 CLIPS frames/fps
	for name in ["scratch", "sneeze", "sniff", "nuzzle", "rush", "walk_happy", "walk_drag"]:
		if timing.has(name):
			continue
		var c := clip_meta(name)
		if c.is_empty():
			continue
		timing[name] = _normalize_draft(name, {
			"frames": int(c.get("frames", 0)),
			"fps": float(c.get("fps", 8)),
			"loop": bool(c.get("loop", false)),
			"sfx": [],
		})


func clip_meta(name: String) -> Dictionary:
	var list: Array = clips_doc.get("clips", [])
	for c in list:
		if c is Dictionary and str(c.get("name", "")) == name:
			return c
	return {}


func clip_timing(name: String) -> Dictionary:
	# 單一來源：優先正式 anim_timing（t_ms／sfx_hook）；否則草稿／CLIPS。
	if timing.has(name) and timing[name] is Dictionary:
		return timing[name]
	var c := clip_meta(name)
	if c.is_empty():
		return {}
	var d := _normalize_draft(name, {
		"frames": int(c.get("frames", 0)),
		"fps": float(c.get("fps", 8)),
		"loop": bool(c.get("loop", false)),
		"sfx": [],
	})
	timing[name] = d
	return d


func frame_duration_sec(name: String, index: int) -> float:
	var t := clip_timing(name)
	var durs: Array = t.get("frame_durations_ms", [])
	if index >= 0 and index < durs.size():
		return maxf(0.001, float(durs[index]) / 1000.0)
	var fps := float(t.get("fps", 0))
	if fps > 0.0:
		return 1.0 / fps
	return 0.125


func sfx_cues(name: String) -> Array:
	var tmg := clip_timing(name)
	var evs: Array = tmg.get("sfx", tmg.get("events", []))
	return evs


func frames_of(name: String, size: String = "") -> Array:
	# size：S／M／L。未有對應體型圖集就 fallback 去已有 atlas（而家得 L 64），由 Walker 按官方 pivot／尺吋顯示。
	var key := name if size == "" else "%s@%s" % [name, size]
	if _tex_cache.has(key):
		return _tex_cache[key]
	var want := size_px(size) if size != "" else 0.0
	var arr: Array = []
	var fallback: Array = []
	for atlas in _atlases:
		var doc: Dictionary = atlas["doc"]
		var tex: Texture2D = atlas["tex"]
		if tex == null:
			continue
		var frames: Dictionary = doc.get("frames", {})
		# 優先完整幀 name_01，其次 noface
		var keys: Array = []
		var i := 1
		while frames.has("%s_%02d" % [name, i]):
			keys.append("%s_%02d" % [name, i])
			i += 1
		if keys.is_empty():
			i = 1
			while frames.has("%s_noface_%02d" % [name, i]):
				keys.append("%s_noface_%02d" % [name, i])
				i += 1
		if keys.is_empty():
			continue
		for k in keys:
			var info: Dictionary = frames[k]
			var fr: Dictionary = info.get("frame", info)
			var at := AtlasTexture.new()
			at.atlas = tex
			at.region = Rect2(float(fr.get("x", 0)), float(fr.get("y", 0)), float(fr.get("w", 64)), float(fr.get("h", 64)))
			at.filter_clip = true
			arr.append(at)
		if arr.size():
			var fs := float(atlas.get("frame_size", 64))
			if want <= 0.0 or is_equal_approx(fs, want):
				_tex_cache[key] = arr
				return arr
			if fallback.is_empty():
				fallback = arr
			arr = []
	_tex_cache[key] = fallback
	return fallback


func liveliness_idle_pool() -> PackedStringArray:
	# G0.1：生命感段落先接 scratch／sneeze／sniff（同 CLIPS 已交付）
	var pool := PackedStringArray()
	for n in ["scratch", "sneeze", "sniff"]:
		if frames_of(n).size():
			pool.append(n)
	return pool


func day_sky_colors() -> Dictionary:
	# 由 environments.json day preset 抽（有就用，冇就空）
	var presets: Array = environments.get("presets", [])
	for p in presets:
		if p is Dictionary and str(p.get("id", "")) == "day":
			return p
	return {}



func size_px(size: String) -> float:
	match size:
		"S":
			return 32.0
		"M":
			return 48.0
		_:
			return 64.0


func liveliness_pivot(size: String) -> Vector2:
	# 官方：S 32→(16, 29)、M 48→(24, 45)、L 64→(32, 61)＝(w/2, h-3)。唔好再用 46。
	var px := size_px(size)
	return Vector2(px * 0.5, px - 3.0)


func actor_spec(character: String) -> Dictionary:
	var actors: Dictionary = actor_anim.get("actors", {})
	var s: Variant = actors.get(character, {})
	return s if s is Dictionary else {}


func actor_walk_fps(character: String) -> float:
	return float(actor_spec(character).get("walk_fps", 10.0))


func actor_idle_fps(character: String) -> float:
	return float(actor_spec(character).get("idle_fps", 4.0))


func actor_pivot(character: String) -> Vector2:
	var s := actor_spec(character)
	var p: Variant = s.get("pivot", [])
	if p is Array and p.size() >= 2:
		return Vector2(float(p[0]), float(p[1]))
	return liveliness_pivot(str(s.get("size", "L")))


func actor_frame(character: String) -> float:
	return float(actor_spec(character).get("frame", size_px(str(actor_spec(character).get("size", "L")))))
