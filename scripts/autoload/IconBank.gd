extends Node
## 載入 art/m1-icons（遊美 m1-icons-hunt）。冇檔就畫一個簡單佔位圓 icon。

var _cache: Dictionary = {}


func tex(id: String) -> Texture2D:
	if id == "" or id == "null":
		return null
	if _cache.has(id):
		return _cache[id]
	var path := "res://art/m1-icons/%s.png" % id
	if ResourceLoader.exists(path) or FileAccess.file_exists(path):
		var t: Texture2D = load(path)
		_cache[id] = t
		return t
	var ph := _placeholder(id)
	_cache[id] = ph
	return ph


func _placeholder(id: String) -> Texture2D:
	var img := Image.create(48, 48, false, Image.FORMAT_RGBA8)
	var col := Color(0.95, 0.75, 0.35)
	if id.find("eat") >= 0 or id.find("hunger") >= 0:
		col = Color(0.95, 0.45, 0.25)
	elif id.find("sleep") >= 0 or id.find("energy") >= 0:
		col = Color(0.45, 0.55, 0.95)
	elif id.find("play") >= 0 or id.find("mood") >= 0:
		col = Color(0.95, 0.55, 0.75)
	elif id.find("pet") >= 0 or id.find("clean") >= 0:
		col = Color(0.55, 0.8, 0.45)
	var c := Vector2(23.5, 23.5)
	for y in range(48):
		for x in range(48):
			var d := Vector2(float(x), float(y)).distance_to(c) / 22.0
			var a := clampf(1.0 - d, 0.0, 1.0)
			a = a * a
			if a <= 0.05:
				img.set_pixel(x, y, Color(0, 0, 0, 0))
			else:
				img.set_pixel(x, y, Color(col.r, col.g, col.b, a))
	return ImageTexture.create_from_image(img)
