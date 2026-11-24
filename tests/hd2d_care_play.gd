extends SceneTree
## Real Main feed / pat / clean. The coat is the only visible body.
## Software GL is not a Mobile recording.

var _fails := 0
var _main: Node
var _ran := false


func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("care user_dir=", udir)
	if udir.find("vc27_root_adapter") < 0 and udir.find("room1_review_") < 0:
		if OS.get_environment("CARE_REQUIRE_ISOLATED") == "1" and udir.find("vc27_care_") < 0:
			print("FAIL user dir is not isolated")
			quit(2)
			return
	_main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(_main)
	process_frame.connect(_on_frame)


func _on_frame() -> void:
	if _ran:
		return
	var main := _main
	var pet: Node = main.get("pet")
	if pet == null:
		return
	_ran = true
	process_frame.disconnect(_on_frame)
	_ok(pet != null, "pet exists")
	var host: Node = main.get_node_or_null("Hd2dPresentation")
	_ok(host != null and bool(host.get("active")), "presentation is the normal pet")
	var coat: Sprite3D = pet.get_node_or_null("Hd2dCoat")
	_ok(coat != null and coat.visible, "coat is visible")
	_ok(pet.sprite == null or not pet.sprite.visible, "walker sprite is hidden")
	var visible_sprites := 0
	for child in pet.get_children():
		if child is Sprite3D and (child as Sprite3D).visible:
			visible_sprites += 1
			if str(child.name).begins_with("Face_"):
				_ok(false, "face sprite is a second body")
	_ok(visible_sprites == 1, "one visible sprite body")
	var blob: Node3D = pet.get_node_or_null("BlobShadow")
	_ok(blob != null and is_equal_approx(blob.position.y, 0.25), "shadow sits at the coat foot offset")
	var sim: Node = root.get_node("Sim")
	var needs: Dictionary = sim.get("state").get("needs", {})
	needs["hunger"] = 40.0
	sim.get("state")["needs"] = needs
	var before := float(needs["hunger"])
	var fed: Dictionary = main.call("hand_feed", pet, "meal")
	_ok(bool(fed.get("ok", false)), "feed accepted")
	var brain: Node = pet.get_node_or_null("PetBrain")
	_ok(brain != null, "brain exists")
	brain.call("_tick_tap", null, null)
	_ok(str(host.call("care_id")) == "eat", "feed plays eat on the coat")
	var after := float(sim.get("state").get("needs", {}).get("hunger", 0))
	_ok(is_equal_approx(after - before, float(sim.get("FEED_MEAL"))), "one feed changes hunger once")
	host.set_process(false)
	host.call("_process", 0.0)
	var eat_tex: Texture2D = coat.texture
	main.call("hand_feed", pet, "meal")
	brain.call("_tick_tap", null, null)
	host.call("_process", 0.0)
	_ok(str(host.call("care_id")) == "eat" and coat.texture == eat_tex, "eat is not restarted by a second feed")
	var mood_before := float(sim.get("state").get("needs", {}).get("mood", 0))
	main.call("hand_pat", pet)
	brain.call("_tick_tap", null, null)
	_ok(str(host.call("care_id")) == "eat", "pat does not replace eat")
	var mood_after := float(sim.get("state").get("needs", {}).get("mood", 0))
	_ok(mood_after >= mood_before, "pat still applies once in Sim")
	host.call("_process", 0.13)
	_ok(str(host.call("care_id")) == "eat", "frame 2 of eat is still eat")
	pet.global_position += Vector3(0, 0, -6)
	host.call("_process", 0.05)
	_ok(str(host.call("care_id")) == "eat", "walking during eat does not cancel the pose")
	host.get("clip").set("facing", "back")
	host.call("_process", 0.5)
	_ok(str(host.call("care_id")) == "", "eat completes without chaining happy")
	var resumed := str(coat.texture.resource_path) if coat.texture else ""
	_ok(host.get("clip").facing == "back", "walk facing is back after eat")
	_ok(resumed.find("back") >= 0, "back walk frame returns instead of eat")
	_ok(bool(host.call("play_care", "emo_happy")), "happy is an explicit clip")
	host.call("_process", 0.0)
	_ok(str(host.call("care_id")) == "emo_happy", "happy started")
	host.call("_process", 2.0)
	_ok(str(host.call("care_id")) == "", "happy repeat 4 returns to idle or walk")
	_ok(bool(host.call("play_care", "nuzzle")), "nuzzle starts")
	host.call("_process", 0.2)
	_ok(bool(host.call("play_care", "nuzzle")), "repeat nuzzle restarts")
	_ok(is_equal_approx(float(host.get("_care_elapsed")), 0.0), "restarted nuzzle is at the first frame")
	_ok(bool(host.call("play_care", "emo_surprised")), "surprised replaces interruptible nuzzle")
	var surprised := str(host.call("care_id"))
	_ok(not bool(host.call("play_care", "nuzzle")), "nuzzle does not cut off surprised")
	_ok(str(host.call("care_id")) == surprised, "surprised stays")
	host.call("cancel_care")
	_ok(str(host.call("care_id")) == "", "cancel returns the body to walk or idle")
	host.get("clip").set("facing", "back")
	host.call("_process", 0.0)
	var back_tex: Texture2D = coat.texture
	_ok(bool(host.call("play_care", "eat")), "eat while the body faces back")
	host.call("_process", 0.0)
	_ok(coat.flip_h == false, "care frames stay unflipped")
	_ok(coat.texture != back_tex, "care does not paste the front face onto the back frame")
	host.call("_process", 0.6)
	_ok(str(host.call("care_id")) == "" and coat.texture == back_tex, "after eat the same back frame returns")
	var poops := int(sim.get("state").get("poops", 0))
	_ok(bool(sim.call("clean_one")), "clean removes one poop")
	_ok(int(sim.get("state").get("poops", 0)) == poops - 1, "clean applies once")
	_ok(str(host.call("care_id")) == "", "clean does not start a care pose")
	_ok(int(sim.get("state").get("version", -1)) == 1, "save version stays 1")
	print("PASS hd2d_care_play" if _fails == 0 else "FAIL hd2d_care_play")
	quit(0 if _fails == 0 else 1)


func _ok(cond: bool, label: String) -> void:
	if cond:
		print("PASS ", label)
	else:
		_fails += 1
		print("FAIL ", label)
