extends RefCounted
## Pointer classification for the vc27 garden.
## A swipe or a long-press must not also walk the pet.
## Long-press clean-all runs only when a poop already exists.
##
## Hold time is an engineering threshold. core-loop names the gesture
## and does not give a duration. 0.45s is the value used here.
## Swipe distance is 48px on the viewport, also an engineering threshold.

const LONG_PRESS_SEC := 0.45
const SWIPE_PX := 48.0


static func action(kind: String, over_pet: bool, overview: bool, poops: int, pet_count: int) -> String:
	if kind == "swipe":
		if pet_count > 1:
			return "cycle"
		return "ignore"
	if kind == "long":
		if over_pet:
			return "follow"
		if poops > 0:
			return "clean_all"
		return "ignore"
	if kind == "tap":
		if over_pet:
			return "follow"
		if not overview:
			return "overview"
		return "walk"
	return "ignore"
