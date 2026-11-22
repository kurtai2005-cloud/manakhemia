extends Node3D
## One 64 quad for a later Mobile look. This scene does not play care and does not save.
## Opening it shows the composited idle. It does not grab a screenshot.

const FRAMES := [
	"res://frames/idle.png",
	"res://frames/eat_01.png",
	"res://frames/eat_02.png",
	"res://frames/eat_03.png",
	"res://frames/eat_04.png",
	"res://frames/emo_happy_01.png",
	"res://frames/emo_happy_02.png",
	"res://frames/emo_surprised_01.png",
	"res://frames/emo_surprised_02.png",
	"res://frames/nuzzle_01.png",
	"res://frames/nuzzle_02.png",
	"res://frames/nuzzle_03.png",
	"res://frames/nuzzle_04.png",
	"res://frames/nuzzle_05.png",
	"res://frames/nuzzle_06.png",
]


func _ready() -> void:
	var sprite := Sprite3D.new()
	sprite.name = "CareQuad"
	sprite.pixel_size = 1.0
	sprite.centered = true
	sprite.offset = Vector2(0, 2)
	sprite.position = Vector3(0, 29, 0)
	sprite.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	sprite.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
	var tex := load(FRAMES[0]) as Texture2D
	if tex == null or tex.get_width() != 64 or tex.get_height() != 64:
		push_error("care idle frame is missing or not 64x64")
		return
	sprite.texture = tex
	add_child(sprite)
	if OS.get_environment("CARE_FRAME_CHECK") == "1":
		print("care quad node_y=29 offset_y=2 pixel_size=1 frame=64 png_written=false")
		get_tree().quit(0)
