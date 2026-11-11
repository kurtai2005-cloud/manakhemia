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
const SFX_MAP_PATH := "res://audio/anim_sfx_map.json"

var clips_doc: Dictionary = {}
var timing: Dictionary = {}  # clip name -> timing dict
var environments: Dictionary = {}
var actor_anim: Dictionary = {}
var import_docs: Array = []
var _atlases: Array = []  # {json, texture, dir, frame_size}
var _tex_cache: Dictionary = {}  # "scratch" or "scratch@M" -> Array[Texture2D]
var _actor_atlases: Dictionary = {}  # character -> clip -> {doc, tex, frame_size, pivot}
var _idle_quiet: Dictionary = {}  # size -> {doc, tex, frame_size, pivot}
var _hunt: Dictionary = {}  # "clip@S" -> {doc, tex}
var sfx_map: Dictionary = {}  # clip -> Array of cue dicts


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
	_load_actor_catalogs()
	_load_sfx_map()
	_load_idle_quiet()
	_load_hunt_clips()


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
	if sfx_map.has(name):
		var mapped: Array = sfx_map[name]
		if mapped.size() > 0:
			return mapped
	var tmg := clip_timing(name)
	var evs: Array = tmg.get("sfx", tmg.get("events", []))
	return evs


func frames_of(name: String, size: String = "", character: String = "") -> Array:
	# size：S／M／L。character 有就先用 art-fix1 角色圖集（細佬／訪客唔好再用團絨 L）。
	var key := "%s@%s@%s" % [name, size, character]
	if _tex_cache.has(key):
		return _tex_cache[key]
	if name == "idle_quiet":
		var sz := size if size in _idle_quiet else ("L" if _idle_quiet.has("L") else "")
		if sz != "":
			var rec: Dictionary = _idle_quiet[sz]
			var arr_q: Array = _frames_from_doc(rec.get("doc", {}), rec.get("tex"), "idle_quiet")
			# 有啲圖集 frame key 可能唔帶 clip 名前綴
			if arr_q.is_empty():
				arr_q = _frames_from_doc(rec.get("doc", {}), rec.get("tex"), name)
			_tex_cache[key] = arr_q
			return arr_q
	# 狩獵 clip：part_grass／pounce／carry_fruit／cheer（S／M／L）
	if name in ["part_grass", "pounce", "carry_fruit", "cheer"]:
		var hsz := size if size != "" else "L"
		var hkey := "%s@%s" % [name, hsz]
		if not _hunt.has(hkey):
			hkey = "%s@L" % name
		if _hunt.has(hkey):
			var rec_h: Dictionary = _hunt[hkey]
			var arr_h: Array = _frames_from_doc(rec_h.get("doc", {}), rec_h.get("tex"), name)
			_tex_cache[key] = arr_h
			return arr_h
	if character != "":
		var who := character
		if who == "visitor":
			who = str(actor_spec("visitor").get("form", "snail_postman"))
		var bag: Dictionary = _actor_atlases.get(who, _actor_atlases.get(character, {}))
		if bag.has(name):
			var rec2: Dictionary = bag[name]
			var arr_a: Array = _frames_from_doc(rec2.get("doc", {}), rec2.get("tex"), name)
			if arr_a.size():
				_tex_cache[key] = arr_a
				return arr_a
	# size：S／M／L。未有對應體型圖集就 fallback 去已有 atlas（而家得 L 64），由 Walker 按官方 pivot／尺吋顯示。
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


func _load_actor_catalogs() -> void:
	# art-fix1：細佬 A1 同訪客各自 scratch／sneeze／sniff，唔再用團絨 L。
	_actor_atlases.clear()
	var paths := {
		"kid": "res://art-pet/sprites/series2/liveliness/clips.json",
		"A1": "res://art-pet/sprites/series2/liveliness/clips.json",
		"snail_postman": "res://art-pet/sprites/visitors/m2/liveliness_clips.json",
		"mushroom_granny": "res://art-pet/sprites/visitors/m2/liveliness_clips.json",
		"firefly_vendor": "res://art-pet/sprites/visitors/m2/liveliness_clips.json",
		"visitor": "res://art-pet/sprites/visitors/m2/liveliness_clips.json",
	}
	# 亦由 actor_anim 讀 index
	for aid in actor_anim.get("actors", {}).keys() if actor_anim.get("actors", {}) is Dictionary else []:
		var spec: Dictionary = actor_spec(str(aid))
		var idx := str(spec.get("liveliness_index", ""))
		if idx != "":
			paths[str(aid)] = idx
	var loaded: Dictionary = {}
	for character in paths.keys():
		var idx_path: String = str(paths[character])
		if not loaded.has(idx_path):
			loaded[idx_path] = _json(idx_path)
		var cat: Dictionary = loaded[idx_path]
		if cat.is_empty():
			continue
		var form := str(actor_spec(character).get("form", character))
		if character == "kid":
			form = "A1"
		if character == "visitor":
			form = str(actor_spec("visitor").get("form", "snail_postman"))
		var bag: Dictionary = _actor_atlases.get(character, {})
		for item in cat.get("items", []):
			if not (item is Dictionary):
				continue
			var iid := str(item.get("id", ""))
			# 呢份 index 可能包晒三位訪客；只收呢個角色
			if cat.get("format", "").find("visitor") >= 0 and iid != form and character != "visitor":
				if iid != character:
					continue
			if cat.get("format", "").find("visitor") >= 0 and character == "visitor" and iid != form:
				continue
			var clip := str(item.get("clip", ""))
			var atlas_rel := str(item.get("atlas", ""))
			if clip == "" or atlas_rel == "":
				continue
			var dir := idx_path.get_base_dir() + "/"
			var doc := _json(dir + atlas_rel)
			if doc.is_empty():
				continue
			var img := str(doc.get("alpha", doc.get("meta", {}).get("image", "") if doc.get("meta", {}) is Dictionary else ""))
			if img == "":
				var meta: Dictionary = doc.get("meta", {})
				img = str(meta.get("image", atlas_rel.replace(".json", ".png")))
			var tex: Texture2D = load(dir + img) if img != "" and (ResourceLoader.exists(dir + img) or FileAccess.file_exists(dir + img)) else null
			if tex == null:
				continue
			bag[clip] = {
				"doc": doc,
				"tex": tex,
				"frame_size": float(item.get("frameSize", doc.get("frameSize", 48))),
				"pivot": item.get("pivotPx", doc.get("pivotPx", [24, 45])),
				"fps": float(item.get("fps", doc.get("fps", 8))),
				"loop": bool(item.get("loop", doc.get("loop", false))),
			}
		_actor_atlases[character] = bag
	# alias
	if _actor_atlases.has("kid"):
		_actor_atlases["A1"] = _actor_atlases["kid"]


func _load_idle_quiet() -> void:
	_idle_quiet.clear()
	for sz in ["S", "M", "L"]:
		var path := "res://art-pet/sprites/tuanrong/motion/m2/atlas_radiant_idle_quiet_%s.json" % sz
		var doc := _json(path)
		if doc.is_empty():
			continue
		var dir := path.get_base_dir() + "/"
		var img := str(doc.get("alpha", ""))
		if img == "":
			var meta: Dictionary = doc.get("meta", {})
			img = str(meta.get("image", "atlas_radiant_idle_quiet_%s.png" % sz))
		var tex: Texture2D = load(dir + img) if img != "" else null
		if tex == null:
			continue
		_idle_quiet[sz] = {
			"doc": doc, "tex": tex,
			"frame_size": float(doc.get("frameSize", 64)),
			"pivot": doc.get("pivotPx", [32, 61]),
			"fps": float(doc.get("fps", 6)),
			"loop": true,
		}



func _load_hunt_clips() -> void:
	_hunt.clear()
	var cat := _json("res://art-pet/sprites/tuanrong/motion/hunt/clips.json")
	if cat.is_empty():
		return
	var dir := "res://art-pet/sprites/tuanrong/motion/hunt/"
	var atlases: Dictionary = cat.get("atlases", {})
	for sz in atlases.keys():
		var bag: Dictionary = atlases[sz]
		for clip in bag.keys():
			var jp := dir + str(bag[clip])
			var doc := _json(jp)
			if doc.is_empty():
				continue
			var img := str(doc.get("meta", {}).get("image", str(bag[clip]).replace(".json", ".png")))
			var tex: Texture2D = load(dir + img) if img != "" else null
			if tex == null:
				continue
			_hunt["%s@%s" % [str(clip), str(sz)]] = {"doc": doc, "tex": tex}


func _frames_from_doc(doc: Dictionary, tex: Texture2D, clip: String) -> Array:
	if tex == null or doc.is_empty():
		return []
	var frames: Dictionary = doc.get("frames", {})
	var keys: Array = []
	var i := 1
	while frames.has("%s_%02d" % [clip, i]):
		keys.append("%s_%02d" % [clip, i])
		i += 1
	if keys.is_empty():
		# 有啲圖集 key 就係 clip_01
		i = 1
		while frames.has("%s_%02d" % [clip, i]):
			keys.append("%s_%02d" % [clip, i])
			i += 1
	var arr: Array = []
	for k in keys:
		var info: Dictionary = frames[k]
		var fr: Dictionary = info.get("frame", info)
		var at := AtlasTexture.new()
		at.atlas = tex
		at.region = Rect2(float(fr.get("x", 0)), float(fr.get("y", 0)), float(fr.get("w", 48)), float(fr.get("h", 48)))
		at.filter_clip = true
		arr.append(at)
	return arr




func _load_sfx_map() -> void:
	sfx_map = {}
	var doc := _json(SFX_MAP_PATH)
	if doc.is_empty():
		return
	for e in doc.get("entries", []):
		if not (e is Dictionary):
			continue
		var cue: Dictionary = e.duplicate(true)
		var preroll := int(cue.get("preroll_ms", 0))
		if preroll > 0:
			cue["t_ms"] = int(cue.get("t_ms", 0)) - preroll
		if str(cue.get("kind_clip", "")) == "critter" and str(cue.get("event", "")) == "startle":
			cue["on_enter"] = true
		var clip := str(cue.get("clip", ""))
		if clip.begins_with("idle_") or str(cue.get("kind_clip", "")) == "visitor":
			if int(cue.get("every_n_loops", 0)) <= 0:
				cue["every_n_loops"] = 3
		if clip == "":
			continue
		if not sfx_map.has(clip):
			sfx_map[clip] = []
		var arr: Array = sfx_map[clip]
		arr.append(cue)
		sfx_map[clip] = arr
	# aliases：scratch／sneeze／sniff 細佬／訪客共用同一 hook
	if sfx_map.has("scratch_head") and not sfx_map.has("scratch"):
		sfx_map["scratch"] = sfx_map["scratch_head"]


