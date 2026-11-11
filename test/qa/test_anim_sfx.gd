extends GutTest
## 草稿。未接入遊程，唔好寫入 project.godot。
## 契約係本檔 _cue。遊程播放器好之後，測試改呼叫佢哋嘅函式。
## art/anim-timing-fix1 @ f6d60b5e 的 42 個 event，
## 配聲跟 audio/pet-plan-a @ 07762d21 的 anim_sfx_map.json。
## toleranceFrames=1。遊音新檔能量峰 ≤27 ms。

const TOLERANCE_FRAMES := 1
const PITCH := {"S": 1.12, "M": 1.0, "L": 0.88}
const YAWN_PREROLL_MS := 600
## clip|event|frame|t_ms|fps|hook|preroll。hook 空＝無聲。
const ROWS := [
	"part_grass|grass_rustle|2|250|8|sfx_pet_grass_rustle_a|0",
	"pounce|jump|2|250|8|sfx_pet_jump_a|0",
	"pounce|land|4|500|8|sfx_pet_step_hop_a|0",
	"carry_fruit|footstep|0|0|10|sfx_pet_step_walk_a|0",
	"carry_fruit|footstep|3|300|10|sfx_pet_step_walk_a|0",
	"cheer|jump|1|100|10|sfx_pet_jump_a|0",
	"cheer|cheer_peak|2|200|10|sfx_pet_happy|0",
	"cheer|land|4|400|10|sfx_pet_step_hop_a|0",
	"dewlet_scared|startle|0|0|6|sfx_critter_startle_a|0",
	"dewlet_tofruit|shake|0|0|8|sfx_critter_shake_a|0",
	"dewlet_tofruit|transform|3|375|8|sfx_critter_transform_a|0",
	"dewlet_tofruit|roll|4|500|8|sfx_critter_roll_a|0",
	"loambun_scared|startle|0|0|6|sfx_critter_startle_a|0",
	"loambun_tofruit|shake|0|0|8|sfx_critter_shake_a|0",
	"loambun_tofruit|transform|3|375|8|sfx_critter_transform_a|0",
	"loambun_tofruit|roll|4|500|8|sfx_critter_roll_a|0",
	"mossback_scared|startle|0|0|6|sfx_critter_startle_a|0",
	"mossback_tofruit|shake|0|0|8|sfx_critter_shake_a|0",
	"mossback_tofruit|transform|3|375|8|sfx_critter_transform_a|0",
	"mossback_tofruit|roll|4|500|8|sfx_critter_roll_a|0",
	"seedfluff_scared|startle|0|0|6|sfx_critter_startle_a|0",
	"seedfluff_tofruit|shake|0|0|8|sfx_critter_shake_a|0",
	"seedfluff_tofruit|transform|3|375|8|sfx_critter_transform_a|0",
	"seedfluff_tofruit|roll|4|500|8|sfx_critter_roll_a|0",
	"mail_post|footstep|0|0|8|sfx_pet_step_walk_a|0",
	"mail_post|letter_drop|4|500|8|sfx_pet_letter_drop_a|0",
	"mail_post|clap|5|625|8|sfx_pet_clap_a|0",
	"idle_lively|hop_peak|2|250|8||0",
	"idle_lively|land|4|500|8|sfx_pet_step_hop_a|0",
	"idle_diligent|pickup|2|250|8|sfx_pet_pickup_a|0",
	"idle_diligent|place|5|625|8|sfx_pet_place_a|0",
	"idle_lazy|yawn|3|600|5|sfx_pet_yawn|600",
	"idle_clingy|reach|2|250|8|sfx_pet_reach_a|0",
	"scratch_head|scratch|2|250|8|sfx_pet_scratch_a|0",
	"stretch|stretch|2|250|8|sfx_pet_stretch_a|0",
	"proud_hips|hands_hips|2|250|8|sfx_pet_proud_a|0",
	"point_frame|point|3|375|8|sfx_pet_point_a|0",
	"snail_postman_snail_deliver|offer|3|375|8|sfx_visitor_offer_letter|0",
	"mushroom_granny_granny_seed|nod|2|250|8|sfx_visitor_nod_a|0",
	"mushroom_granny_granny_seed|offer|3|375|8|sfx_visitor_offer_seed|0",
	"firefly_vendor_vendor_show|rattle|2|250|8|sfx_visitor_rattle_a|0",
	"firefly_vendor_vendor_show|rattle|4|500|8|sfx_visitor_rattle_a|0",
]
## 循環 clip 唔好每圈都響。數值係 clip 長度 ms。
const LOOP_MS := {
	"idle_diligent": 750,
	"idle_clingy": 750,
	"idle_lazy": 1200,
	"snail_postman_snail_deliver": 750,
	"mushroom_granny_granny_seed": 750,
	"firefly_vendor_vendor_show": 750,
}


func test_forty_two_events_forty_one_files_and_hop_peak_silent() -> void:
	assert_eq(ROWS.size(), 42)
	var voiced := 0
	var saw_hop := false
	for row in ROWS:
		var cue := _cue(row, "tuanrong", "M", true, 0, -1)
		var p: PackedStringArray = row.split("|")
		if p[1] == "hop_peak" and int(p[3]) == 250:
			saw_hop = true
			assert_eq(p[0], "idle_lively")
			assert_false(cue.play)
			assert_eq(cue.stream, "")
		else:
			assert_true(cue.play, row)
			assert_false(cue.stream.is_empty(), row)
			voiced += 1
	assert_true(saw_hop)
	assert_eq(voiced, 41)


func test_yawn_starts_at_t_minus_600() -> void:
	var row := _row("idle_lazy", "yawn")
	var cue := _cue(row, "tuanrong", "M", true, 0, -1)
	assert_eq(cue.stream, "sfx_pet_yawn")
	assert_eq(cue.play_ms, 600 - YAWN_PREROLL_MS)
	assert_eq(cue.play_ms, 0)
	# 能量峰約 603 ms，對住事件 600。差 3 ms，細過一幀（fps 5 → 200 ms）。
	assert_true(_within_frames(603, 600, 5))


func test_pitch_follows_size() -> void:
	var row := _row("cheer", "cheer_peak")
	assert_almost_eq(_cue(row, "kid", "S", true, 0, -1).pitch, 1.12, 0.0001)
	assert_almost_eq(_cue(row, "tuanrong", "M", true, 0, -1).pitch, 1.0, 0.0001)
	assert_almost_eq(_cue(row, "visitor", "L", true, 0, -1).pitch, 0.88, 0.0001)


func test_startle_only_when_entering() -> void:
	for clip in ["dewlet_scared", "loambun_scared", "mossback_scared", "seedfluff_scared"]:
		var row := _row(clip, "startle")
		var enter := _cue(row, "critter", "S", true, 0, -1)
		assert_true(enter.play, clip)
		assert_eq(enter.stream, "sfx_critter_startle_a")
		var looped := _cue(row, "critter", "S", false, 667, 0)
		assert_false(looped.play, clip)
		assert_eq(looped.stream, "")


func test_loop_sfx_not_every_cycle() -> void:
	var cases := [
		["idle_diligent", "pickup", 750],
		["idle_clingy", "reach", 750],
		["snail_postman_snail_deliver", "offer", 750],
		["mushroom_granny_granny_seed", "nod", 750],
		["firefly_vendor_vendor_show", "rattle", 750],
		["idle_lazy", "yawn", 1200],
	]
	for c in cases:
		var row := _row(c[0], c[1])
		var first := _cue(row, "tuanrong", "M", true, 0, -1)
		assert_true(first.play, c[0])
		var again := _cue(row, "tuanrong", "M", false, int(c[2]) - 1, 0)
		assert_false(again.play, c[0])
		var later := _cue(row, "tuanrong", "M", false, int(c[2]), 0)
		assert_true(later.play, c[0])


func test_accent_stays_inside_one_frame() -> void:
	# 新檔實測最慢 sfx_visitor_offer_letter 能量峰 27 ms。訪客 fps 8，一幀 125 ms。
	assert_true(_within_frames(375 + 27, 375, 8))
	# 現有 happy 峰 63 ms。cheer fps 10，一幀 100 ms，仍喺 1 幀內。
	assert_true(_within_frames(200 + 63, 200, 10))
	# 超過一幀就失敗。
	assert_false(_within_frames(200 + 100, 200, 10))


func _row(clip: String, event: String) -> String:
	for row in ROWS:
		var p: PackedStringArray = row.split("|")
		if p[0] == clip and p[1] == event:
			return row
	push_error("missing " + clip + " " + event)
	return ""


func _within_frames(heard_ms: int, event_ms: int, fps: int) -> bool:
	var frame_ms := int(round(1000.0 / float(fps)))
	return absi(heard_ms - event_ms) <= frame_ms * TOLERANCE_FRAMES


func _cue(row: String, _actor: String, size: String, entering: bool, now_ms: int, last_play_ms: int) -> Cue:
	var p: PackedStringArray = row.split("|")
	var clip := p[0]
	var event := p[1]
	var hook := p[5]
	var preroll := int(p[6])
	var out := Cue.new()
	out.pitch = float(PITCH[size])
	if hook.is_empty():
		out.play = false
		out.stream = ""
		return out
	if event == "startle" and not entering:
		out.play = false
		out.stream = ""
		return out
	if clip in LOOP_MS and last_play_ms >= 0:
		if now_ms - last_play_ms < int(LOOP_MS[clip]):
			out.play = false
			out.stream = ""
			return out
	out.play = true
	out.stream = hook
	out.play_ms = int(p[3]) - preroll
	return out


class Cue:
	var play: bool
	var stream: String
	var pitch: float
	var play_ms: int
