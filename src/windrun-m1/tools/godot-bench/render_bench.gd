# Godot 4 渲染基準（軟件 GL，非真機）：同一張城鎮圖 16px TileMapLayer＋Sprite2D 道具＋CanvasModulate＋PointLight2D（光數量對應 town-lab）。
# 執行：godot --rendering-driver opengl3 --resolution 390x844 --path tools/godot-bench --script render_bench.gd -- <lights:0|1> ; 計 240 幀（熱身 30）每幀 process 時間（唔受 vsync 限制要加 --disable-vsync ）
extends SceneTree
var frames = 0; var times = []; var last = 0; var use_lights = true
func _initialize():
	var args = OS.get_cmdline_user_args(); use_lights = args.size() == 0 or args[0] != "0"
	var m = JSON.parse_string(FileAccess.get_file_as_string("../../art/town/town_morningmoss.json"))
	var w = int(m.width); var h = int(m.height); var layers = {}; var objs = {}
	for l in m.layers:
		if l.type == "tilelayer": layers[l.name] = l.data
		else: objs[l.name] = l.objects
	var img = Image.new(); img.load("../../art/town/town_tiles.png")
	var ts = TileSet.new(); ts.tile_size = Vector2i(16, 16)
	var src = TileSetAtlasSource.new(); src.texture = ImageTexture.create_from_image(img); src.texture_region_size = Vector2i(16, 16)
	for i in range(40): src.create_tile(Vector2i(i % 16, i / 16))
	ts.add_source(src, 0)
	var world = Node2D.new(); root.add_child(world)
	for ln in ["ground", "decor", "occlusion"]:
		var tl = TileMapLayer.new(); tl.tile_set = ts; tl.y_sort_enabled = false
		for i in range(w * h):
			var g = int(layers[ln][i])
			if g != 0: tl.set_cell(Vector2i(i % w, i / w), 0, Vector2i((g - 1) % 16, (g - 1) / 16))
		world.add_child(tl)
	var names = ["tree_a", "tree_b", "house_a", "house_b", "hall", "lamp", "well"]
	var ysort = Node2D.new(); ysort.y_sort_enabled = true; world.add_child(ysort)
	for o in objs["props"]:
		var im = Image.new(); im.load("../../art/town/props/" + names[int(o.gid) - 101] + ".png")
		var sp = Sprite2D.new(); sp.texture = ImageTexture.create_from_image(im); sp.centered = false; sp.position = Vector2(o.x, o.y - o.height); ysort.add_child(sp)
	if use_lights:
		var cm = CanvasModulate.new(); cm.color = Color(44/255.0, 56/255.0, 108/255.0); root.add_child(cm)
		var gt = GradientTexture2D.new(); var gr = Gradient.new(); gr.set_color(0, Color(1, 0.8, 0.5, 1)); gr.set_color(1, Color(0, 0, 0, 0)); gt.gradient = gr; gt.fill = GradientTexture2D.FILL_RADIAL; gt.fill_from = Vector2(0.5, 0.5); gt.fill_to = Vector2(1, 0.5); gt.width = 128; gt.height = 128
		for o in objs["lights"]:
			var pl = PointLight2D.new(); pl.texture = gt; pl.position = Vector2(o.x, o.y); var r = 60.0
			for p in o.properties:
				if p.name == "radius": r = float(p.value)
			pl.texture_scale = r * 2.0 / 128.0; world.add_child(pl)
	var cam = Camera2D.new(); cam.position = Vector2(20 * 16, 14 * 16); cam.zoom = Vector2(2, 2); root.add_child(cam)
	last = Time.get_ticks_usec()
func _process(_dt):
	var now = Time.get_ticks_usec(); frames += 1
	if frames > 30: times.append((now - last) / 1000.0)
	last = now
	var cam = root.get_child(root.get_child_count() - 1); cam.position.x = 20 * 16 + sin(frames * 0.05) * 40
	if frames >= 270:
		times.sort(); var s = 0.0
		for v in times: s += v
		print(JSON.stringify({godot = Engine.get_version_info().string, lights = use_lights, frames = times.size(), avgMs = s / times.size(), p95Ms = times[int(times.size() * 0.95)], maxMs = times[times.size() - 1], driver = RenderingServer.get_current_rendering_driver_name(), method = RenderingServer.get_current_rendering_method(), adapter = RenderingServer.get_video_adapter_name(), window = DisplayServer.window_get_size()}))
		quit()
	return false
