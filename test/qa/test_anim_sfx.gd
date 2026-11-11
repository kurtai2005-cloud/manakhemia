extends GutTest
## 草稿。未接入遊程，唔好喺 project.godot 登記。
## 契約係本檔 _play。遊程播放器好之後，測試改呼叫佢哋嘅函式，預期表唔好改。
## 依據 art/anim-timing @ 330d3a57，toleranceFrames=1。
## 聲線：sfx_pet_<動作>_<角色>_a/b。未有角色檔就用團絨檔，再加體型 pitch。

const TOLERANCE_FRAMES := 1
const ACTORS := ["tuanrong", "kid", "visitor"]
const PITCH := {"S": 1.12, "M": 1.0, "L": 0.88}
## 有聲線。噴嚏係命名例子；呵欠、開心係 timing 入面已接嘅聲線。
const VOICED := ["sneeze", "yawn", "happy"]


class Cue:
	var play: bool
	var stream: String
	var pitch: float
	var actor: String
	var fallback: bool


func test_voice_follows_the_actor() -> void:
	var files := PackedStringArray([
		"sfx_pet_sneeze_tuanrong_a",
		"sfx_pet_sneeze_kid_a",
		"sfx_pet_sneeze_visitor_a",
		"sfx_pet_yawn_kid_a",
		"sfx_pet_happy_visitor_a",
	])
	for actor in ACTORS:
		var cue := _play("sneeze", actor, "M", "a", "sfx_pet_sneeze_a", files)
		assert_true(cue.play, actor)
		assert_eq(cue.stream, "sfx_pet_sneeze_%s_a" % actor, actor)
		assert_false(cue.fallback, actor)
	var kid := _play("yawn", "kid", "M", "a", "sfx_pet_yawn", files)
	assert_eq(kid.stream, "sfx_pet_yawn_kid_a")
	var visitor := _play("happy", "visitor", "M", "a", "sfx_pet_happy", files)
	assert_eq(visitor.stream, "sfx_pet_happy_visitor_a")
	assert_ne(kid.stream, visitor.stream)


func test_pitch_follows_size() -> void:
	var files := PackedStringArray(["sfx_pet_scratch_a"])
	assert_almost_eq(_play("scratch", "kid", "S", "a", "sfx_pet_scratch_a", files).pitch, 1.12, 0.0001)
	assert_almost_eq(_play("scratch", "tuanrong", "M", "a", "sfx_pet_scratch_a", files).pitch, 1.0, 0.0001)
	assert_almost_eq(_play("scratch", "visitor", "L", "a", "sfx_pet_scratch_a", files).pitch, 0.88, 0.0001)
	# 有自己把聲都跟體型，唔好因為檔名已經分角色就用 1.0。
	var voice := PackedStringArray(["sfx_pet_sneeze_kid_a", "sfx_pet_sneeze_kid_b"])
	assert_almost_eq(_play("sneeze", "kid", "S", "a", "sfx_pet_sneeze_a", voice).pitch, 1.12, 0.0001)
	assert_almost_eq(_play("sneeze", "kid", "L", "b", "sfx_pet_sneeze_b", voice).pitch, 0.88, 0.0001)


func test_sneeze_and_voiced_actions_fall_back_to_tuanrong_plus_pitch() -> void:
	var only_tuanrong := PackedStringArray([
		"sfx_pet_sneeze_a",
		"sfx_pet_sneeze_b",
		"sfx_pet_yawn",
		"sfx_pet_happy",
	])
	for actor in ["kid", "visitor"]:
		for size in ["S", "M", "L"]:
			var sneeze := _play("sneeze", actor, size, "a", "sfx_pet_sneeze_a", only_tuanrong)
			assert_eq(sneeze.stream, "sfx_pet_sneeze_a", actor + size)
			assert_true(sneeze.fallback, actor)
			assert_almost_eq(sneeze.pitch, float(PITCH[size]), 0.0001)
			var other := _play("sneeze", actor, size, "b", "sfx_pet_sneeze_b", only_tuanrong)
			assert_eq(other.stream, "sfx_pet_sneeze_b")
	# 團絨自己用現有檔，唔當借用別人。
	var self_cue := _play("sneeze", "tuanrong", "M", "a", "sfx_pet_sneeze_a", only_tuanrong)
	assert_eq(self_cue.stream, "sfx_pet_sneeze_a")
	assert_false(self_cue.fallback)
	assert_eq(_play("yawn", "kid", "S", "a", "sfx_pet_yawn", only_tuanrong).stream, "sfx_pet_yawn")
	assert_eq(_play("happy", "visitor", "L", "a", "sfx_pet_happy", only_tuanrong).stream, "sfx_pet_happy")
	assert_almost_eq(_play("yawn", "kid", "S", "a", "sfx_pet_yawn", only_tuanrong).pitch, 1.12, 0.0001)
	# 有帶角色名嘅團絨檔，先用佢，唔好跳去舊名。
	var named := PackedStringArray(["sfx_pet_sneeze_tuanrong_a", "sfx_pet_sneeze_a"])
	assert_eq(_play("sneeze", "kid", "M", "a", "sfx_pet_sneeze_a", named).stream, "sfx_pet_sneeze_tuanrong_a")


func test_action_and_sound_stay_within_one_frame() -> void:
	# pounce，fps 8，6 幀。land 喺 frame 4、t_ms 500。每幀 125 ms。
	var pounce: Array = [125, 125, 125, 125, 125, 125]
	assert_true(_within(500, 4, pounce))
	assert_true(_within(625, 4, pounce))
	assert_false(_within(750, 4, pounce))
	# idle_lazy yawn：frame 3、t_ms 600。fps 5，每幀 200 ms。聲峰對準 600，播放可以早 600 ms preroll。
	var lazy: Array = [200, 200, 200, 200, 200, 200]
	assert_true(_within(600, 3, lazy))
	assert_eq(_accent_ms(0, 600), 600)
	assert_true(_within(_accent_ms(0, 600), 3, lazy))
	assert_false(_within(_accent_ms(0, 200), 3, lazy))


func test_null_hook_stays_silent() -> void:
	# idle_lively hop_peak，timing 寫 sfx_hook=null。
	var files := PackedStringArray(["sfx_pet_step_hop_a", "sfx_pet_happy"])
	var cue := _play("hop_peak", "tuanrong", "M", "a", null, files)
	assert_false(cue.play)
	assert_eq(cue.stream, "")
	# 行路步而家都係 null。有步進檔都唔好播。
	var step := _play("footstep", "kid", "S", "a", null, PackedStringArray(["sfx_pet_step_walk_a"]))
	assert_false(step.play)
	assert_eq(step.stream, "")


func _within(play_ms: int, frame_index: int, frame_ms: Array) -> bool:
	return absi(_frame_at(play_ms, frame_ms) - frame_index) <= TOLERANCE_FRAMES


func _accent_ms(play_start_ms: int, preroll_ms: int) -> int:
	return play_start_ms + preroll_ms


func _frame_at(t_ms: int, frame_ms: Array) -> int:
	var acc := 0
	for i in frame_ms.size():
		var dur: int = int(frame_ms[i])
		if t_ms < acc + dur:
			return i
		acc += dur
	if t_ms == acc and frame_ms.size() > 0:
		return frame_ms.size()
	return frame_ms.size()


func _play(action: String, actor: String, size: String, variant: String, hook, files: PackedStringArray) -> Cue:
	var cue := Cue.new()
	cue.pitch = float(PITCH[size])
	cue.actor = actor
	if hook == null:
		cue.play = false
		cue.stream = ""
		cue.fallback = false
		return cue
	cue.play = true
	if action in VOICED:
		var specific := "sfx_pet_%s_%s_%s" % [action, actor, variant]
		if files.has(specific):
			cue.stream = specific
			cue.fallback = false
			return cue
		var named := "sfx_pet_%s_tuanrong_%s" % [action, variant]
		if files.has(named):
			cue.stream = named
			cue.fallback = actor != "tuanrong"
			return cue
		var legacy_ab := "sfx_pet_%s_%s" % [action, variant]
		if files.has(legacy_ab):
			cue.stream = legacy_ab
			cue.fallback = actor != "tuanrong"
			return cue
		cue.stream = "sfx_pet_%s" % action
		cue.fallback = actor != "tuanrong"
		return cue
	cue.stream = str(hook)
	cue.fallback = false
	return cue
