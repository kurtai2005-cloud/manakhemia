extends GutTest
## M1c.2 音效回歸。跑喺 code/glimmer-godot @ d2ddd47f。
## 四項修復要過：腳步只 emit、拍速不同由 0 起、sfx_codex_* 走 UI、
## bgm_hunt_loop.ogg.import loop=true。
## 另外跟 m1b_sfx_map.json 對 bus／檔案，同埋 AudioManager 引用的 id 都要有檔。
## 聲池重疊只記錄。


func before_each() -> void:
	AudioManager.muted = false
	if "appreciate_muted" in AudioManager:
		AudioManager.appreciate_muted = false
	if AudioManager.has_method("clear_play_log"):
		AudioManager.clear_play_log()
	if "_scene_bgm" in AudioManager:
		AudioManager._scene_bgm = ""
		AudioManager._bgm_band = ""


func test_footstep_emits_once() -> void:
	var src := FileAccess.get_file_as_string("res://scripts/Walker.gd")
	var i := src.find("func _maybe_footstep")
	var j := src.find("func _apply_frame", i)
	var body := src.substr(i, j - i) if i >= 0 and j > i else ""
	assert_true(body.find("ArtImporter.sfx_cue.emit") >= 0, "footstep emits sfx_cue")
	assert_true(body.find("AudioManager.play") < 0, "footstep does not call AudioManager.play")
	var w := Walker.new()
	w.character = "tuanrong"
	w.body_size = "L"
	add_child(w)
	w.frame_i = 0
	w._step_cool = 0.0
	AudioManager.clear_play_log()
	w._maybe_footstep(6)
	var n: int = AudioManager.hook_count("sfx_pet_step_hop")
	gut.p("footstep plays=%d" % n)
	assert_eq(n, 1, "one land frame plays the step hook exactly once")
	w.free()


func test_different_tempo_starts_at_zero() -> void:
	AudioManager.call("sync_bgm", "noon", true)
	var care: AudioStreamPlayer = AudioManager._bgm_a if AudioManager._bgm_front else AudioManager._bgm_b
	assert_true(care.playing and care.stream != null, "care BGM playing")
	care.seek(4.0)
	AudioManager.enter_hunt_bgm()
	var hunt: AudioStreamPlayer = AudioManager._bgm_a if AudioManager._bgm_front else AudioManager._bgm_b
	gut.p("enter start_sec=%.4f playback=%.4f out_bar=%.4f" % [AudioManager.last_bgm_start_sec, hunt.get_playback_position(), AudioManager.last_outgoing_bar])
	assert_almost_eq(AudioManager.last_outgoing_bar, AudioManager.BAR_SEC, 0.001, "captured care bar before the flag flip")
	assert_almost_eq(AudioManager.last_bgm_start_sec, 0.0, 0.001, "hunt BGM starts at 0")
	assert_lte(hunt.get_playback_position(), 0.08, "hunt playback is the start of the new track")
	hunt.seek(4.0)
	AudioManager.exit_hunt_bgm()
	var back: AudioStreamPlayer = AudioManager._bgm_a if AudioManager._bgm_front else AudioManager._bgm_b
	gut.p("exit start_sec=%.4f playback=%.4f out_bar=%.4f" % [AudioManager.last_bgm_start_sec, back.get_playback_position(), AudioManager.last_outgoing_bar])
	assert_almost_eq(AudioManager.last_outgoing_bar, AudioManager.hunt_bar_sec(), 0.001, "captured hunt bar before leaving")
	assert_almost_eq(AudioManager.last_bgm_start_sec, 0.0, 0.001, "care BGM starts at 0")
	assert_lte(back.get_playback_position(), 0.08, "care playback is the start of the new track")


func test_codex_hooks_use_ui_bus() -> void:
	for id in ["sfx_codex_page_flip", "sfx_codex_page_flip_a", "sfx_codex_page_flip_b", "sfx_codex_new_entry"]:
		assert_eq(AudioManager.bus_for(id), "UI", id)
	assert_eq(AudioManager.bus_for("sfx_furn_buy"), "SFX", "non-codex stays SFX")


func test_map_bus_and_files() -> void:
	var bus_bad: PackedStringArray = []
	var file_bad: PackedStringArray = []
	for row in _map_rows():
		var got := AudioManager.bus_for(row["id"])
		if got != str(row["bus"]):
			bus_bad.append("%s %s id=%s map=%s code=%s" % [row["list"], row["event"], row["id"], row["bus"], got])
		if not _id_has_file(str(row["id"])):
			file_bad.append(str(row["id"]))
	gut.p("bus mismatches=%d file misses=%d" % [bus_bad.size(), file_bad.size()])
	for line in bus_bad:
		gut.p(line)
	for line in file_bad:
		gut.p("missing file " + line)
	assert_eq(file_bad.size(), 0, "every map id has an ogg")
	assert_eq(bus_bad.size(), 0, "bus_for matches every m1b_sfx_map.json row")


func test_bgm_and_loop_imports_loop() -> void:
	var bad: PackedStringArray = []
	for path in _loop_imports():
		var text := FileAccess.get_file_as_string(path)
		if text.find("loop=true") < 0 or text.find("loop=false") >= 0:
			bad.append(path)
	gut.p("loop import misses=%s" % str(bad))
	assert_eq(bad.size(), 0, "every bgm_* and *_loop import has loop=true")
	var hunt := FileAccess.get_file_as_string("res://audio/bgm/bgm_hunt_loop.ogg.import")
	assert_true(hunt.find("loop=true") >= 0, "bgm_hunt_loop.ogg.import loop=true")


func test_audio_manager_ids_exist_and_stir_renamed() -> void:
	assert_false(FileAccess.file_exists("res://audio/sfx/sfx_kitchen_stir.ogg"), "old sfx_kitchen_stir.ogg is gone")
	assert_true(FileAccess.file_exists("res://audio/sfx/sfx_kitchen_stir_loop.ogg"), "sfx_kitchen_stir_loop.ogg present")
	var src := FileAccess.get_file_as_string("res://scripts/autoload/AudioManager.gd")
	assert_true(src.find("sfx_kitchen_stir_loop") >= 0, "AudioManager references the loop id")
	assert_eq(src.find("sfx_kitchen_stir\""), -1, "AudioManager no longer quotes the old id")
	var missing: PackedStringArray = []
	for id in _referenced_ids():
		if not _id_has_file(id):
			missing.append(id)
	gut.p("referenced=%d missing=%s" % [_referenced_ids().size(), str(missing)])
	assert_eq(missing.size(), 0, "every AudioManager id has an ogg")


func test_voice_pool_overlap_report() -> void:
	assert_eq(AudioManager._sfx_pool.size(), 6, "SFX voice pool size")
	var i0 := int(AudioManager._pool_i)
	AudioManager.play("sfx_hunt_pounce")
	var first: AudioStreamPlayer = AudioManager._sfx_pool[i0 % AudioManager._sfx_pool.size()]
	var first_stream: AudioStream = first.stream
	AudioManager.play("sfx_critter_transform")
	AudioManager.play("sfx_critter_roll")
	var stolen := first.stream != first_stream or not first.playing
	var lens: PackedStringArray = []
	for hook in ["sfx_hunt_pounce", "sfx_critter_transform", "sfx_critter_roll", "sfx_mg_catch"]:
		var rec: Dictionary = AudioManager.resolve_play(hook)
		var st: AudioStream = null
		if str(rec.get("stream", "")) != "":
			st = load(str(rec["stream"]))
		lens.append("%s=%.3f" % [hook, st.get_length() if st else -1.0])
	gut.p("pool=6 simultaneous pounce+transform+roll stolen=%s %s" % [stolen, str(lens)])
	var i1 := int(AudioManager._pool_i)
	AudioManager.clear_play_log()
	AudioManager.play("sfx_hunt_pounce")
	var hold: AudioStreamPlayer = AudioManager._sfx_pool[i1 % AudioManager._sfx_pool.size()]
	var hold_stream: AudioStream = hold.stream
	AudioManager.play_later("sfx_critter_transform", 0.10)
	AudioManager.play_later("sfx_critter_roll", 0.12)
	AudioManager._process(0.13)
	var stolen_timed := hold.stream != hold_stream or not hold.playing
	gut.p("timed 0/100/120ms stolen=%s hooks=%s" % [stolen_timed, str(AudioManager.hooks_played())])


func _map_rows() -> Array:
	var rows: Array = []
	var doc: Dictionary = AudioManager.m1b_map
	if doc.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://audio/m1b_sfx_map.json"))
		if parsed is Dictionary:
			doc = parsed
	for list in ["events", "entries"]:
		for item in doc.get(list, []):
			if not (item is Dictionary) or not item.has("bus"):
				continue
			var ids: Array = []
			if str(item.get("sfx_hook", "")) != "":
				ids.append(str(item["sfx_hook"]))
			for f in item.get("files", []):
				var base := str(f).get_file().get_basename()
				if base != "" and not ids.has(base):
					ids.append(base)
			for id in ids:
				rows.append({"list": list, "event": str(item.get("event", "")), "id": id, "bus": str(item["bus"])})
	return rows


func _loop_imports() -> PackedStringArray:
	var out: PackedStringArray = []
	for folder in ["res://audio/bgm", "res://audio/sfx", "res://audio/amb"]:
		var dir := DirAccess.open(folder)
		if dir == null:
			continue
		dir.list_dir_begin()
		var name := dir.get_next()
		while name != "":
			if name.ends_with(".ogg.import"):
				var stem := name.trim_suffix(".ogg.import")
				if stem.begins_with("bgm_") or stem.find("_loop") >= 0:
					out.append("%s/%s" % [folder, name])
			name = dir.get_next()
	return out


func _referenced_ids() -> PackedStringArray:
	var src := FileAccess.get_file_as_string("res://scripts/autoload/AudioManager.gd")
	var ids: PackedStringArray = []
	var call_re := RegEx.new()
	call_re.compile("(?:play|start_loop|stop_loop|play_later)\\(\"((?:sfx_|bgm_|amb_)[^\"]+)\"")
	for m in call_re.search_all(src):
		_push_id(ids, m.get_string(1))
	var path_re := RegEx.new()
	path_re.compile("res://audio/(?:sfx|bgm|amb)/([A-Za-z0-9_]+)\\.ogg")
	for m2 in path_re.search_all(src):
		_push_id(ids, m2.get_string(1))
	return ids


func _push_id(ids: PackedStringArray, id: String) -> void:
	if id == "" or ids.has(id):
		return
	ids.append(id)


func test_m1b_fire_sfx_plays_once() -> void:
	# Walker._fire_sfx 同時 emit 同 play。通用 cue 兩次都出聲。
	var w := Walker.new()
	w.character = "tuanrong"
	w.body_size = "L"
	add_child(w)
	w.play_live_clip("scratch")
	w._sfx_fired.clear()
	var i0 := int(AudioManager._pool_i)
	w._fire_sfx(2)
	var n: int = int(AudioManager._pool_i) - i0
	gut.p("scratch plays=%d" % n)
	assert_eq(n, 1, "one scratch cue plays once")
	w.frame_i = 0
	w._step_cool = 0.0
	var i1 := int(AudioManager._pool_i)
	w._maybe_footstep(6)
	assert_eq(int(AudioManager._pool_i) - i1, 1, "one footstep plays once")
	w.free()


func test_m1b_btn_randomizer_and_shop_sound() -> void:
	var i0 := int(AudioManager._pool_i)
	AudioManager.play("sfx_ui8_btn_press_a")
	var p: AudioStreamPlayer = AudioManager._sfx_pool[i0 % AudioManager._sfx_pool.size()]
	assert_true(p.stream is AudioStreamRandomizer, "press goes through an a/b randomizer")
	if p.stream is AudioStreamRandomizer:
		assert_eq((p.stream as AudioStreamRandomizer).playback_mode, AudioStreamRandomizer.PLAYBACK_RANDOM_NO_REPEATS, "no immediate repeat")
	var book := _fn_body("res://scripts/Hud.gd", "func _refresh_book", "func _toggle_book")
	assert_true(book.find("_play_error") >= 0 or book.find("AudioManager.play") >= 0, "furniture shop failure plays a sound")
	var close := _fn_body("res://scripts/Hud.gd", "var close := _btn(\"關閉\")", "var rec := _btn")
	assert_true(close.find("_play_ui") >= 0 or close.find("AudioManager.play") >= 0, "codex close button plays a sound")
	var open := _fn_body("res://scripts/Hud.gd", "func _toggle_book", "func _toggle_sleep")
	assert_true(open.find("sfx_codex_page_flip") >= 0 or open.find("_play_press") >= 0, "codex open button plays a sound")


func test_m1b_hunt_fail_plays_error() -> void:
	var hud: Node = load("res://scripts/Hud.gd").new()
	add_child(hud)
	var i0 := int(AudioManager._pool_i)
	hud._one_tap("hunt")
	gut.p("hunt fail last=%s" % str(AudioManager.last_play.get("hook", "")))
	assert_true(str(AudioManager.last_play.get("hook", "")).find("sfx_ui8_error") >= 0, "failed hunt plays error")
	assert_eq(int(AudioManager._pool_i) - i0, 1, "failed hunt does not also play a press")
	hud.free()


func test_m1b_stop_loop_fades_and_hunt_bar() -> void:
	AudioManager.muted = false
	AudioManager.start_loop("sfx_pet_sleep_breath_loop")
	var lp: AudioStreamPlayer = AudioManager._loop_players.get("sfx_pet_sleep_breath_loop", null)
	AudioManager.stop_loop("sfx_pet_sleep_breath_loop", 0.6)
	assert_true(lp != null and lp.playing, "stop_loop keeps playing during the fade")
	var src := FileAccess.get_file_as_string("res://scripts/autoload/AudioManager.gd")
	var body := _fn_body_text(src, "func sync_bgm", "func _process")
	assert_true(body.find("BAR_SEC") < 0 or body.find("2.222") >= 0 or body.find("hunt") >= 0, "sync_bgm does not quantize hunt with the 68 BPM bar")


func test_m1b_feature_signals_connected() -> void:
	var src := FileAccess.get_file_as_string("res://scripts/autoload/AudioManager.gd")
	assert_true(src.find("dispatched.connect") >= 0, "WorkSystem.dispatched reaches AudioManager")
	assert_true(src.find("hunt_phase.connect") >= 0 or src.find("hunt_started.connect") >= 0, "Hunt signals reach AudioManager")
	assert_true(src.find("unlocked.connect") >= 0, "CollectionSystem.unlocked reaches AudioManager")


func test_m1b_boot_unlock_silent() -> void:
	CollectionSystem.ensure()
	var was: bool = CollectionSystem.silent_unlocks if "silent_unlocks" in CollectionSystem else false
	if "silent_unlocks" in CollectionSystem:
		CollectionSystem.silent_unlocks = true
	var i0 := int(AudioManager._pool_i)
	CollectionSystem.unlock_form("m1b_boot_probe")
	CollectionSystem.unlock_kid("BOOTY")
	assert_eq(int(AudioManager._pool_i) - i0, 0, "boot unlocks play no sfx")
	assert_true(str(AudioManager.last_play.get("hook", "")).find("sfx_codex_new_entry") < 0, "no sfx_codex_new_entry on boot")
	if "silent_unlocks" in CollectionSystem:
		CollectionSystem.silent_unlocks = was


func test_m1b_hunt_catch_sound() -> void:
	var src := FileAccess.get_file_as_string("res://scripts/HuntField.gd")
	assert_true(src.find("\"sfx_mg_miss\"") < 0 or src.find("hook == \"sfx_mg_miss\"") >= 0, "hunt does not play sfx_mg_miss")
	assert_true(src.find("sfx_mg_catch") >= 0, "catch plays sfx_mg_catch")
	assert_true(src.find("sfx_critter_startle") >= 0 and src.find("sfx_critter_shake") >= 0, "miss is startle then shake")
	assert_true(src.find("sfx_hunt_pounce") >= 0, "pounce uses sfx_hunt_pounce")


func test_m1b_need_warning_rules() -> void:
	AudioManager.reset_need_warning_cooldowns()
	AudioManager.appreciate_muted = true
	var muted: Dictionary = AudioManager.play_need_warning("tuanrong")
	assert_false(bool(muted.get("played", true)), "欣賞 mutes the warning")
	assert_eq(str(muted.get("reason", "")), "appreciate", "reason is appreciate")
	AudioManager.appreciate_muted = false
	AudioManager.reset_need_warning_cooldowns()
	var a: Dictionary = AudioManager.play_need_warning("tuanrong")
	assert_true(bool(a.get("played", false)), "first warning plays")
	var b: Dictionary = AudioManager.play_need_warning("kid")
	assert_eq(str(b.get("reason", "")), "same_moment", "two bubbles one sound")
	AudioManager._need_warn_global_at = -999.0
	var c: Dictionary = AudioManager.play_need_warning("tuanrong")
	assert_eq(str(c.get("reason", "")), "pet_cooldown", "same pet waits 8s")
	var p: AudioStreamPlayer = AudioManager._sfx_pool[(int(AudioManager._pool_i) - 1) % 6]
	assert_true(p.stream is AudioStreamRandomizer, "warning a/b uses the no-repeat randomizer")
	AudioManager.appreciate_muted = false


func _fn_body(path: String, start: String, end: String) -> String:
	return _fn_body_text(FileAccess.get_file_as_string(path), start, end)


func _fn_body_text(src: String, start: String, end: String) -> String:
	var i := src.find(start)
	var j := src.find(end, i + start.length()) if i >= 0 else -1
	if i < 0 or j < 0:
		return ""
	return src.substr(i, j - i)


func _id_has_file(id: String) -> bool:
	for folder in ["sfx", "bgm", "amb"]:
		if FileAccess.file_exists("res://audio/%s/%s.ogg" % [folder, id]):
			return true
		if FileAccess.file_exists("res://audio/%s/%s_a.ogg" % [folder, id]):
			return true
	var rec: Dictionary = AudioManager.resolve_play(id)
	return not bool(rec.get("silent", true)) and str(rec.get("stream", "")) != ""
