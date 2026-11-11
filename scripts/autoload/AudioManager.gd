extends Node
## 遊音：play(hook, actor) 用正在做動作嗰隻寵物嘅角色＋體型。
## 通用動作（scratch／sniff／腳步）共用檔，按體型變速：S 1.12、M 1.0、L 0.88。
## 有聲線（sneeze 等）先查 sfx_pet_sneeze_<character>_a/b，冇就退回團絨檔再按體型變速。
## hook 係 null 或對唔到檔就靜音。

const BAR_SEC := 3.5294
const SIZE_PITCH := {"S": 1.12, "M": 1.0, "L": 0.88}
const GENERIC_PREFIXES: PackedStringArray = [
	"sfx_pet_scratch", "sfx_pet_sniff",
	"sfx_pet_step_hop", "sfx_pet_step_drag", "sfx_pet_step_plod",
]
const VOICED_PREFIXES: PackedStringArray = [
	"sfx_pet_sneeze", "sfx_pet_yawn", "sfx_pet_happy", "sfx_pet_hungry",
	"sfx_pet_sleepy", "sfx_pet_touch", "sfx_pet_grumpy", "sfx_pet_content",
	"sfx_pet_curious", "sfx_pet_uncomfortable", "sfx_pet_reunion_happy",
	"sfx_pet_nuzzle_purr", "sfx_pet_turn_huh", "sfx_pet_bug_pat",
]
const BGM_BY_BAND := {
	"morning": "res://audio/bgm/bgm_care_morning_loop.ogg",
	"noon": "res://audio/bgm/bgm_care_loop.ogg",
	"day": "res://audio/bgm/bgm_care_loop.ogg",
	"evening": "res://audio/bgm/bgm_care_evening_loop.ogg",
	"night": "res://audio/bgm/bgm_care_night_loop.ogg",
}

var last_play: Dictionary = {}  # 俾測試讀：hook, character, size, pitch, stream, silent, actor
var muted := false
var _streams: Dictionary = {}
var _randomizers: Dictionary = {}
var _last_ab: Dictionary = {}
var _sfx_pool: Array = []
var _pool_i := 0
var _pet_voice_at := -999.0
var _bgm_a: AudioStreamPlayer
var _bgm_b: AudioStreamPlayer
var _bgm_front := true
var _bgm_band := ""
var _fade_t := -1.0
var _fade_dur := 1.5
var _loop_players: Dictionary = {}  # hook -> player


func _ready() -> void:
	_bgm_a = _make_player("BGM_A", "BGM")
	_bgm_b = _make_player("BGM_B", "BGM")
	for i in range(6):
		_sfx_pool.append(_make_player("SFX_%d" % i, "SFX"))
	if ArtImporter and not ArtImporter.sfx_cue.is_connected(_on_sfx_cue):
		ArtImporter.sfx_cue.connect(_on_sfx_cue)


func _make_player(p_name: String, bus: String) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.name = p_name
	p.bus = bus
	add_child(p)
	return p


func size_pitch(size: String) -> float:
	return float(SIZE_PITCH.get(size, 1.0))


func is_generic(hook: String) -> bool:
	var root := _root_hook(hook)
	for p in GENERIC_PREFIXES:
		if root == p or root.begins_with(p):
			return true
	return false


func is_voiced(hook: String) -> bool:
	var root := _root_hook(hook)
	for p in VOICED_PREFIXES:
		if root == p or root.begins_with(p):
			return true
	return false


func _root_hook(hook: String) -> String:
	var h := hook
	if h.ends_with("_a") or h.ends_with("_b"):
		h = h.substr(0, h.length() - 2)
	return h


func _actor_info(actor: Object) -> Dictionary:
	var character := "tuanrong"
	var size := "L"
	var actor_name := ""
	if actor != null:
		if actor.has_method("get") or true:
			if "character" in actor:
				character = str(actor.character)
			if "body_size" in actor:
				size = str(actor.body_size)
			if "name" in actor:
				actor_name = str(actor.name)
	if character == "":
		character = "tuanrong"
	if size not in SIZE_PITCH:
		size = "M"
	return {"character": character, "size": size, "actor": actor_name}


func resolve_play(hook: Variant, actor: Object = null) -> Dictionary:
	# 純解析（測試用）：唔播聲。null hook → silent。
	var out := {
		"hook": hook, "character": "", "size": "", "pitch": 1.0,
		"stream": "", "silent": true, "fallback": false, "actor": "",
	}
	if hook == null:
		return out
	var hs := str(hook).strip_edges()
	if hs == "" or hs == "<null>" or hs == "null":
		return out
	var info := _actor_info(actor)
	out["character"] = info["character"]
	out["size"] = info["size"]
	out["actor"] = info["actor"]
	out["hook"] = hs
	var root := _root_hook(hs)
	var pitch := 1.0
	var path := ""
	var fallback := false
	if is_voiced(hs):
		path = _find_variant(root + "_" + info["character"])
		if path == "":
			path = _find_variant(root)  # 團絨檔 sfx_pet_sneeze_a/b
			fallback = true
			pitch = size_pitch(info["size"])
		# 角色專屬檔用自己聲線，唔再疊體型變速
	elif is_generic(hs):
		path = _find_variant(root)
		pitch = size_pitch(info["size"])
	else:
		path = _find_variant(root)
		if path == "":
			# 可能 hook 本身已係完整檔名（無 _a/_b）
			path = _stream_path(hs)
	if path == "":
		out["silent"] = true
		out["pitch"] = pitch
		out["fallback"] = fallback
		return out
	out["silent"] = false
	out["stream"] = path
	out["pitch"] = pitch
	out["fallback"] = fallback
	return out


func play(hook: Variant, actor: Object = null) -> Dictionary:
	var rec := resolve_play(hook, actor)
	# 寵物聲線最短間隔 4 s（grumpy 例外）；事件／UI／腳步／抓癢唔受呢條限
	if not rec["silent"] and is_voiced(str(rec.get("hook", ""))):
		var h := _root_hook(str(rec["hook"]))
		if h != "sfx_pet_grumpy":
			var now := Time.get_ticks_msec() / 1000.0
			if now - _pet_voice_at < 4.0:
				rec["silent"] = true
				rec["deferred"] = true
				last_play = rec
				return rec
			_pet_voice_at = now
	last_play = rec
	if rec["silent"] or muted:
		return rec
	var st: AudioStream = _stream_for(str(rec["stream"]), _root_hook(str(rec["hook"])))
	if st == null:
		rec["silent"] = true
		last_play = rec
		return rec
	var p: AudioStreamPlayer = _sfx_pool[_pool_i % _sfx_pool.size()]
	_pool_i += 1
	p.stop()
	p.stream = st
	var jitter := 1.0
	if is_generic(str(rec["hook"])) or rec.get("fallback", false):
		jitter = randf_range(0.95, 1.05)
	p.pitch_scale = float(rec["pitch"]) * jitter
	rec["pitch_played"] = p.pitch_scale
	last_play = rec
	p.play()
	return rec


func _on_sfx_cue(clip: String, hook: String, _frame: int, actor: Object = null) -> void:
	# 只播正在做呢個動作嘅嗰隻（actor）；冇 actor 就唔當團絨誤播
	if hook == "" or hook == "null":
		return
	play(hook, actor)


func start_loop(hook: String, bus: String = "SFX") -> void:
	var rec := resolve_play(hook, null)
	if rec["silent"]:
		last_play = rec
		return
	var st := _load_stream(str(rec["stream"]))
	if st == null:
		return
	_ensure_loop(st)
	var p: AudioStreamPlayer = _loop_players.get(hook, null)
	if p == null:
		p = _make_player("LOOP_" + hook, bus)
		_loop_players[hook] = p
	p.stream = st
	p.pitch_scale = 1.0
	if hook.find("sleep_breath") >= 0:
		p.volume_db = -3.0  # README 建議再 ×0.7
	if not muted:
		p.play()
	last_play = rec
	last_play["loop"] = true


func stop_loop(hook: String, fade := 0.6) -> void:
	var p: AudioStreamPlayer = _loop_players.get(hook, null)
	if p and p.playing:
		p.stop()
	# fade 參數留畀之後；G0.1 直接停


func sync_bgm(band: String = "") -> void:
	if band == "":
		band = TimeService.hour_band() if TimeService else "noon"
	if band == "day":
		band = "noon"
	if band == _bgm_band and (_bgm_a.playing or _bgm_b.playing):
		return
	var path := str(BGM_BY_BAND.get(band, BGM_BY_BAND["noon"]))
	var st := _load_stream(path)
	if st == null:
		return
	_ensure_loop(st)
	var incoming: AudioStreamPlayer = _bgm_b if _bgm_front else _bgm_a
	var outgoing: AudioStreamPlayer = _bgm_a if _bgm_front else _bgm_b
	incoming.stream = st
	# 下一小節線對位：由 outgoing 位置推 (b+1) mod
	var start_sec := 0.0
	if outgoing.playing and outgoing.stream:
		var pos := outgoing.get_playback_position()
		var b := int(floor(pos / BAR_SEC))
		var len := 0.0
		if outgoing.stream is AudioStream:
			len = outgoing.stream.get_length()
		var bars := int(round(len / BAR_SEC)) if len > 0.1 else 0
		if bars > 0:
			start_sec = fmod(float(b + 1), float(bars)) * BAR_SEC
	incoming.play(start_sec)
	incoming.volume_db = -80.0
	_fade_t = 0.0
	_bgm_front = not _bgm_front
	_bgm_band = band
	if not outgoing.playing:
		incoming.volume_db = 0.0
		_fade_t = -1.0


func _process(dt: float) -> void:
	if _fade_t < 0.0:
		return
	_fade_t += dt
	var k := clampf(_fade_t / _fade_dur, 0.0, 1.0)
	# equal-power
	var inn: AudioStreamPlayer = _bgm_a if _bgm_front else _bgm_b
	var outg: AudioStreamPlayer = _bgm_b if _bgm_front else _bgm_a
	inn.volume_db = linear_to_db(maxf(sin(k * PI * 0.5), 0.0001))
	outg.volume_db = linear_to_db(maxf(cos(k * PI * 0.5), 0.0001))
	if k >= 1.0:
		outg.stop()
		inn.volume_db = 0.0
		_fade_t = -1.0


func _find_variant(root: String) -> String:
	# 优先 a/b，再試無後綴
	var a := _stream_path(root + "_a")
	var b := _stream_path(root + "_b")
	if a != "" or b != "":
		return a if a != "" else b
	return _stream_path(root)


func _stream_path(hook: String) -> String:
	var name := hook
	if not name.begins_with("sfx_") and not name.begins_with("bgm_") and not name.begins_with("amb_"):
		name = hook
	for folder in ["sfx", "bgm", "amb"]:
		var p := "res://audio/%s/%s.ogg" % [folder, name]
		if ResourceLoader.exists(p) or FileAccess.file_exists(p):
			return p
	return ""


func _load_stream(path: String) -> AudioStream:
	if path == "":
		return null
	if _streams.has(path):
		return _streams[path]
	var st: AudioStream = load(path)
	if st:
		_ensure_loop(st)
		_streams[path] = st
	return st


func _ensure_loop(st: AudioStream) -> void:
	if st is AudioStreamOggVorbis:
		var ogg := st as AudioStreamOggVorbis
		var path := ""
		if ogg.resource_path:
			path = ogg.resource_path
		if path.find("_loop") >= 0:
			ogg.loop = true
			ogg.loop_offset = 0.0


func _stream_for(path: String, root: String) -> AudioStream:
	# a/b 用 Randomizer，唔好連續兩次同一個
	var a := _stream_path(root + "_a")
	var b := _stream_path(root + "_b")
	if a != "" and b != "":
		if not _randomizers.has(root):
			var r := AudioStreamRandomizer.new()
			r.playback_mode = AudioStreamRandomizer.PLAYBACK_RANDOM_NO_REPEATS
			r.random_pitch = 1.0
			r.random_volume_offset_db = 0.0
			r.add_stream(0, _load_stream(a))
			r.add_stream(1, _load_stream(b))
			_randomizers[root] = r
		return _randomizers[root]
	return _load_stream(path if path != "" else _find_variant(root))
