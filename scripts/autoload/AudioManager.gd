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
var appreciate_muted := false  # 「欣賞」模式：需求警告唔出聲，泡泡照出
var _need_warn_pet_at: Dictionary = {}
var _need_warn_global_at := -999.0
const NEED_WARN_PET_COOLDOWN := 8.0
const NEED_WARN_SAME_MOMENT := 0.25
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
var _loop_fades: Dictionary = {}  # hook -> {player, t, dur, start_lin}
var play_log: Array = []  # 測試用：每次 play／延遲觸發
var m1b_map: Dictionary = {}
var _scene_bgm := ""  # "" 照顧時段；"hunt" 狩獵場
var _pending: Array = []  # {at, hook, actor}
var _place_burst: Array = []
var _bought_at := -999.0
var _unlock_burst_at := -999.0
var _unlock_burst_n := 0
var _systems_connected := false
const HUNT_BAR_SEC := 98000.0 / 44100.0  # 108 BPM 4/4；唔好用 BAR_SEC
const HUNT_XFADE_SEC := 1.5
const DEFAULT_PLACE_AFTER_BUY := 0.14
const DEFAULT_PLACE_GAP := 0.12
const DEFAULT_PLACE_MAX := 3


func _ready() -> void:
	_bgm_a = _make_player("BGM_A", "BGM")
	_bgm_b = _make_player("BGM_B", "BGM")
	for i in range(6):
		_sfx_pool.append(_make_player("SFX_%d" % i, "SFX"))
	if ArtImporter and not ArtImporter.sfx_cue.is_connected(_on_sfx_cue):
		ArtImporter.sfx_cue.connect(_on_sfx_cue)
	_load_m1b_map()
	_connect_feature_hooks()
	call_deferred("_connect_feature_hooks")


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



func bus_for(hook: Variant) -> String:
	var h := "" if hook == null else str(hook)
	if h.find("sfx_need_warning") >= 0:
		return "UI"
	if h.begins_with("sfx_ui") or h.find("_btn_") >= 0 or h.find("sfx_ui8") >= 0:
		return "UI"
	if h.begins_with("bgm_"):
		return "BGM"
	if h.begins_with("amb_"):
		return "AMB"
	if h.begins_with("sfx_pet") or is_voiced(h) or is_generic(h):
		return "Pet"
	if h.find("sleep_breath") >= 0 or h.find("sfx_sleep") >= 0:
		return "Pet"
	return "SFX"


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
	if rec["silent"] or muted:
		_record(rec)
		return rec
	var st: AudioStream = _stream_for(str(rec["stream"]), _root_hook(str(rec["hook"])))
	if st == null:
		rec["silent"] = true
		_record(rec)
		return rec
	_record(rec)
	var p: AudioStreamPlayer = _sfx_pool[_pool_i % _sfx_pool.size()]
	_pool_i += 1
	p.stop()
	p.stream = st
	var jitter := 1.0
	if is_generic(str(rec["hook"])) or rec.get("fallback", false):
		jitter = randf_range(0.95, 1.05)
	p.bus = bus_for(rec.get("hook", hook))
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
		_record(rec)
		return
	var st := _load_stream(str(rec["stream"]))
	if st == null:
		return
	_ensure_loop(st, true)
	var p: AudioStreamPlayer = _loop_players.get(hook, null)
	if p == null:
		p = _make_player("LOOP_" + hook, bus if bus != "SFX" else bus_for(hook))
		_loop_players[hook] = p
	p.stream = st
	p.pitch_scale = 1.0
	p.volume_db = 0.0
	if hook.find("sleep_breath") >= 0:
		p.volume_db = -3.0  # README 建議再 ×0.7
	_loop_fades.erase(hook)
	if not muted:
		p.play()
	rec["loop"] = true
	_record(rec)


func stop_loop(hook: String, fade := 0.6) -> void:
	var p: AudioStreamPlayer = _loop_players.get(hook, null)
	if p == null or not p.playing:
		_loop_fades.erase(hook)
		return
	if fade <= 0.0:
		p.stop()
		p.volume_db = 0.0
		_loop_fades.erase(hook)
		return
	# 真正淡出：唔即停
	_loop_fades[hook] = {
		"player": p,
		"t": 0.0,
		"dur": fade,
		"start_lin": db_to_linear(p.volume_db),
	}


func hunt_bar_sec() -> float:
	if GameData and "m1c" in GameData:
		var v = GameData.m1c.get("audio", {}).get("hunt_bgm_bar_sec", GameData.m1c.get("hunt", {}).get("sfx", {}).get("bgm_bar_sec", HUNT_BAR_SEC))
		return float(v)
	return HUNT_BAR_SEC


func hunt_xfade_sec() -> float:
	if GameData and "m1c" in GameData:
		var v = GameData.m1c.get("audio", {}).get("hunt_bgm_crossfade_sec", GameData.m1c.get("hunt", {}).get("sfx", {}).get("bgm_crossfade_sec", HUNT_XFADE_SEC))
		return float(v)
	return HUNT_XFADE_SEC


func hunt_bgm_path() -> String:
	return "res://audio/bgm/bgm_hunt_loop.ogg"


func is_hunt_bgm() -> bool:
	return _scene_bgm == "hunt"


func enter_hunt_bgm() -> void:
	_scene_bgm = "hunt"
	_crossfade_to(hunt_bgm_path(), hunt_xfade_sec(), hunt_bar_sec(), _outgoing_bar_sec())
	_bgm_band = "hunt"


func exit_hunt_bgm() -> void:
	if _scene_bgm != "hunt" and _bgm_band != "hunt":
		return
	_scene_bgm = ""
	_bgm_band = ""  # 逼 sync 重新對照顧
	sync_bgm("", true)


func sync_bgm(band: String = "", force: bool = false) -> void:
	# 狩獵場 BGM 期間唔好被時段照顧 loop 蓋過
	if _scene_bgm == "hunt" and not force:
		return
	if band == "":
		band = TimeService.hour_band() if TimeService else "noon"
	if band == "day":
		band = "noon"
	if not force and band == _bgm_band and (_bgm_a.playing or _bgm_b.playing):
		return
	var path := str(BGM_BY_BAND.get(band, BGM_BY_BAND["noon"]))
	var fade := hunt_xfade_sec() if _bgm_band == "hunt" else 1.5
	_crossfade_to(path, fade, BAR_SEC, _outgoing_bar_sec())
	_bgm_band = band


func _outgoing_bar_sec() -> float:
	return hunt_bar_sec() if _scene_bgm == "hunt" or _bgm_band == "hunt" else BAR_SEC


func _crossfade_to(path: String, fade_dur: float, incoming_bar: float, outgoing_bar: float) -> void:
	var st := _load_stream(path)
	if st == null:
		return
	_ensure_loop(st, true)
	var incoming: AudioStreamPlayer = _bgm_b if _bgm_front else _bgm_a
	var outgoing: AudioStreamPlayer = _bgm_a if _bgm_front else _bgm_b
	incoming.stream = st
	# 下一小節對位：用嗰條曲自己嘅小節長，狩獵唔好用 BAR_SEC
	var start_sec := 0.0
	var bar := outgoing_bar if outgoing_bar > 0.0 else incoming_bar
	if outgoing.playing and outgoing.stream:
		var pos := outgoing.get_playback_position()
		var b := int(floor(pos / maxf(bar, 0.001)))
		var len := 0.0
		if outgoing.stream is AudioStream:
			len = outgoing.stream.get_length()
		var bars := int(round(len / maxf(bar, 0.001))) if len > 0.1 else 0
		if bars > 0:
			start_sec = fmod(float(b + 1), float(bars)) * bar
	incoming.play(start_sec)
	incoming.volume_db = -80.0
	_fade_dur = fade_dur if fade_dur > 0.0 else 1.5
	_fade_t = 0.0
	_bgm_front = not _bgm_front
	if not outgoing.playing:
		incoming.volume_db = 0.0
		_fade_t = -1.0


func _process(dt: float) -> void:
	_tick_pending(dt)
	_tick_loop_fades(dt)
	if _fade_t < 0.0:
		return
	_fade_t += dt
	var k := clampf(_fade_t / maxf(_fade_dur, 0.001), 0.0, 1.0)
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


func _ensure_loop(st: AudioStream, force: bool = false) -> void:
	if st is AudioStreamOggVorbis:
		var ogg := st as AudioStreamOggVorbis
		var path := ""
		if ogg.resource_path:
			path = ogg.resource_path
		if force or path.find("_loop") >= 0:
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


func play_need_warning(pet_id: String = "") -> Dictionary:
	# 泡泡出現時播一次；欣賞模式靜音；同一瞬間多個泡泡只播一次；每隻寵物冷卻 ≥8 秒。
	# a/b 由 _stream_for Randomizer 處理，唔會連續兩次同一個。
	var out := {"played": false, "reason": "", "hook": "sfx_need_warning", "silent": true}
	if appreciate_muted:
		out["reason"] = "appreciate"
		last_play = out
		return out
	var now := Time.get_ticks_msec() / 1000.0
	if now - _need_warn_global_at < NEED_WARN_SAME_MOMENT:
		out["reason"] = "same_moment"
		last_play = out
		return out
	if pet_id != "" and _need_warn_pet_at.has(pet_id):
		if now - float(_need_warn_pet_at[pet_id]) < NEED_WARN_PET_COOLDOWN:
			out["reason"] = "pet_cooldown"
			last_play = out
			return out
	var rec := play("sfx_need_warning")
	out["silent"] = bool(rec.get("silent", true))
	out["stream"] = rec.get("stream", "")
	if not out["silent"]:
		out["played"] = true
		out["reason"] = "ok"
		_need_warn_global_at = now
		if pet_id != "":
			_need_warn_pet_at[pet_id] = now
	else:
		out["reason"] = "missing"
	last_play = out
	return out


func reset_need_warning_cooldowns() -> void:
	_need_warn_pet_at.clear()
	_need_warn_global_at = -999.0

func _record(rec: Dictionary) -> void:
	last_play = rec
	var row := rec.duplicate()
	row["t"] = Time.get_ticks_msec() / 1000.0
	play_log.append(row)
	if play_log.size() > 240:
		play_log = play_log.slice(play_log.size() - 180)


func clear_play_log() -> void:
	play_log.clear()
	last_play = {}
	_pending.clear()
	_place_burst.clear()
	_bought_at = -999.0
	_unlock_burst_at = -999.0
	_unlock_burst_n = 0


func hooks_played() -> Array:
	var out: Array = []
	for rec in play_log:
		if rec is Dictionary:
			out.append(str(rec.get("hook", "")))
	return out


func hook_count(prefix: String) -> int:
	var n := 0
	for h in hooks_played():
		if str(h) == prefix or str(h).begins_with(prefix):
			n += 1
	return n


func _load_m1b_map() -> void:
	var path := "res://audio/m1b_sfx_map.json"
	if GameData and "m1c" in GameData:
		path = str(GameData.m1c.get("audio", {}).get("m1b_sfx_map", path))
	if FileAccess.file_exists(path) or ResourceLoader.exists(path):
		var txt := FileAccess.get_file_as_string(path)
		var parsed: Variant = JSON.parse_string(txt)
		if parsed is Dictionary:
			m1b_map = parsed


func audio_cfg() -> Dictionary:
	if GameData and "m1c" in GameData:
		return GameData.m1c.get("audio", {})
	return {}


func place_after_buy_sec() -> float:
	return float(audio_cfg().get("furn_place_after_buy_ms", DEFAULT_PLACE_AFTER_BUY * 1000.0)) / 1000.0


func place_burst_gap_sec() -> float:
	return float(audio_cfg().get("furn_place_burst_gap_ms", DEFAULT_PLACE_GAP * 1000.0)) / 1000.0


func place_burst_max() -> int:
	return int(audio_cfg().get("furn_place_burst_max", DEFAULT_PLACE_MAX))


func play_later(hook: String, delay_sec: float, actor: Object = null) -> void:
	if hook == "" or hook == "sfx_mg_miss":
		return
	if delay_sec <= 0.0:
		play(hook, actor)
		return
	_pending.append({"at": 0.0, "wait": delay_sec, "hook": hook, "actor": actor})


func _tick_pending(dt: float) -> void:
	if _pending.is_empty():
		return
	var keep: Array = []
	for it in _pending:
		if not (it is Dictionary):
			continue
		it["at"] = float(it.get("at", 0.0)) + dt
		if float(it["at"]) >= float(it.get("wait", 0.0)):
			play(str(it.get("hook", "")), it.get("actor", null))
		else:
			keep.append(it)
	_pending = keep


func _tick_loop_fades(dt: float) -> void:
	if _loop_fades.is_empty():
		return
	var done: Array = []
	for hook in _loop_fades.keys():
		var f: Dictionary = _loop_fades[hook]
		var p: AudioStreamPlayer = f.get("player")
		if p == null or not is_instance_valid(p) or not p.playing:
			done.append(hook)
			continue
		f["t"] = float(f.get("t", 0.0)) + dt
		var dur := maxf(float(f.get("dur", 0.6)), 0.001)
		var k := clampf(float(f["t"]) / dur, 0.0, 1.0)
		var lin := float(f.get("start_lin", 1.0)) * (1.0 - k)
		p.volume_db = linear_to_db(maxf(lin, 0.0001))
		if k >= 1.0:
			p.stop()
			p.volume_db = 0.0
			done.append(hook)
	for hook2 in done:
		_loop_fades.erase(hook2)


func _connect_feature_hooks() -> void:
	if WorkSystem == null or HuntSystem == null or CollectionSystem == null:
		return
	if _systems_connected:
		return
	_systems_connected = true
	if WorkSystem:
		if WorkSystem.has_signal("dispatched") and not WorkSystem.dispatched.is_connected(_on_work_dispatched):
			WorkSystem.dispatched.connect(_on_work_dispatched)
		if WorkSystem.has_signal("work_ready") and not WorkSystem.work_ready.is_connected(_on_work_ready):
			WorkSystem.work_ready.connect(_on_work_ready)
		if WorkSystem.has_signal("collected") and not WorkSystem.collected.is_connected(_on_work_collected):
			WorkSystem.collected.connect(_on_work_collected)
	if HuntSystem:
		if HuntSystem.has_signal("hunt_started") and not HuntSystem.hunt_started.is_connected(_on_hunt_started):
			HuntSystem.hunt_started.connect(_on_hunt_started)
		if HuntSystem.has_signal("hunt_phase") and not HuntSystem.hunt_phase.is_connected(_on_hunt_phase):
			HuntSystem.hunt_phase.connect(_on_hunt_phase)
		if HuntSystem.has_signal("hunt_collected") and not HuntSystem.hunt_collected.is_connected(_on_hunt_collected):
			HuntSystem.hunt_collected.connect(_on_hunt_collected)
	if CollectionSystem:
		if CollectionSystem.has_signal("unlocked") and not CollectionSystem.unlocked.is_connected(_on_unlocked):
			CollectionSystem.unlocked.connect(_on_unlocked)
		if CollectionSystem.has_signal("placed") and not CollectionSystem.placed.is_connected(_on_placed):
			CollectionSystem.placed.connect(_on_placed)
		if CollectionSystem.has_signal("bought") and not CollectionSystem.bought.is_connected(_on_bought):
			CollectionSystem.bought.connect(_on_bought)


func _on_work_dispatched(building: String, _pets: Array) -> void:
	if building == "post":
		play("sfx_post_letter_send")
	elif building == "kitchen":
		play("sfx_kitchen_cook_start")
		# 攪拌只喺真係有攪拌動作先 loop；而家寵物只播 idle_quiet／scratch
		if has_kitchen_stir_action():
			start_loop("sfx_kitchen_stir")


func _on_work_ready(building: String) -> void:
	if building == "post":
		play("sfx_post_letter_receive")
	elif building == "kitchen":
		stop_loop("sfx_kitchen_stir", 0.4)
		play("sfx_kitchen_cook_done")


func _on_work_collected(_rec: Dictionary) -> void:
	play("sfx_ui8_confirm")


func _on_hunt_started() -> void:
	play("sfx_mg_start")


func _on_hunt_phase(phase: String) -> void:
	if phase == "hunt":
		play("sfx_hunt_enter")
		enter_hunt_bgm()
	elif phase == "ready" or phase == "home":
		exit_hunt_bgm()


func _on_hunt_collected(rec: Dictionary) -> void:
	play("sfx_ui8_toast_in")
	# 新圖鑑格（若有）由 unlocked 合併播一次


func _on_unlocked(_kind: String, _id: String) -> void:
	if CollectionSystem and bool(CollectionSystem.silent_unlocks):
		return
	var now := Time.get_ticks_msec() / 1000.0
	# 同一下解鎖多個只播一次
	if now - _unlock_burst_at < 0.05 and _unlock_burst_n > 0:
		_unlock_burst_n += 1
		return
	_unlock_burst_at = now
	_unlock_burst_n = 1
	play("sfx_codex_new_entry")


func _on_bought(_item_id: String) -> void:
	play("sfx_furn_buy")
	_bought_at = Time.get_ticks_msec() / 1000.0
	_place_burst.clear()


func _on_placed(_item_id: String) -> void:
	var now := Time.get_ticks_msec() / 1000.0
	var delay := 0.0
	if now - _bought_at <= 0.05:
		delay = place_after_buy_sec()
	# 連續擺最多 3 下，間隔 ≥120 ms
	if _place_burst.size() >= place_burst_max():
		return
	if not _place_burst.is_empty():
		var last_at := float(_place_burst[-1])
		var gap := place_burst_gap_sec()
		delay = maxf(delay, last_at + gap - now)
	_place_burst.append(now + delay)
	play_later("sfx_furn_place", delay)


func has_kitchen_stir_action() -> bool:
	# 規格：未有攪拌動畫／hook 就唔好空播 loop
	if bool(audio_cfg().get("kitchen_stir_only_if_action", true)) == false:
		return true
	if ArtImporter and ArtImporter.has_method("frames_of"):
		var fr: Array = ArtImporter.frames_of("stir", "M", "tuanrong")
		if not fr.is_empty():
			return true
		# 有啲專案用 cook／kitchen_stir
		for nm in ["kitchen_stir", "cook_stir", "stir_pot"]:
			fr = ArtImporter.frames_of(nm, "M", "tuanrong")
			if not fr.is_empty():
				return true
	return false
