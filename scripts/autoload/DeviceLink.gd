extends Node
## 6b RealWorld + 6d Share6d Godot 橋。桌面冇插件就回 {ok:false, error:"desktop"}；權限唔畀照玩。

signal steps_result(rec: Dictionary)
signal location_result(rec: Dictionary)

var realworld: Object = null
var share6d: Object = null


func _ready() -> void:
	if Engine.has_singleton("RealWorld"):
		realworld = Engine.get_singleton("RealWorld")
		if realworld and realworld.has_signal("steps_result"):
			realworld.connect("steps_result", Callable(self, "_on_steps"))
		if realworld and realworld.has_signal("location_result"):
			realworld.connect("location_result", Callable(self, "_on_loc"))
	if Engine.has_singleton("Share6d"):
		share6d = Engine.get_singleton("Share6d")


func _on_steps(rec: Dictionary) -> void:
	steps_result.emit(rec)


func _on_loc(rec: Dictionary) -> void:
	location_result.emit(rec)


func _desktop(err: String = "desktop") -> Dictionary:
	return {"ok": false, "error": err}


func rw_status() -> Dictionary:
	if realworld and realworld.has_method("status"):
		return realworld.status()
	return _desktop()


func request_steps() -> String:
	if realworld and realworld.has_method("requestSteps"):
		return str(realworld.requestSteps())
	return "desktop"


func request_location() -> String:
	if realworld and realworld.has_method("requestLocation"):
		return str(realworld.requestLocation())
	return "desktop"


func steps() -> Dictionary:
	if realworld and realworld.has_method("steps"):
		return realworld.steps()
	return _desktop()


func location() -> Dictionary:
	if realworld and realworld.has_method("location"):
		return realworld.location()
	return _desktop()


func copy_text(text: String) -> Dictionary:
	if share6d and share6d.has_method("copy"):
		return share6d.copy(text)
	# 桌面：用 DisplayServer 剪貼簿（headless 可能唔支援）
	if DisplayServer.has_feature(DisplayServer.FEATURE_CLIPBOARD):
		DisplayServer.clipboard_set(text)
		return {"ok": true, "desktop": true}
	return {"ok": true, "desktop": true, "no_clipboard": true}


func paste_text() -> Dictionary:
	if share6d and share6d.has_method("paste"):
		return share6d.paste()
	var txt := ""
	if DisplayServer.has_feature(DisplayServer.FEATURE_CLIPBOARD):
		txt = DisplayServer.clipboard_get()
	return {"ok": true, "text": txt, "desktop": true}


func save_image(data_b64: String, name: String = "glimmer-6d.png") -> Dictionary:
	if share6d and share6d.has_method("saveImage"):
		return share6d.saveImage(data_b64, name)
	return _desktop()


func share_image(data_b64: String, name: String = "glimmer-6d.png", text: String = "") -> Dictionary:
	if share6d and share6d.has_method("share"):
		return share6d.share(data_b64, name, text)
	return _desktop()
