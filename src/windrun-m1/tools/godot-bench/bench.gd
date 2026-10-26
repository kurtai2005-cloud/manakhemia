# 同 town-lab 等價嘅 Godot 4 headless 基準：載入同一份 Tiled JSON、建 AStarGrid2D、跑同一組 500 個 LCG 隨機尋路（同 src/town.js astarBench 同種子），並計時 TileMapLayer 建立。
# 執行：godot --headless --path tools/godot-bench --script bench.gd -- <map.json>
extends SceneTree
func _init():
	var args = OS.get_cmdline_user_args()
	var path = args[0] if args.size() > 0 else "../../art/town/town_morningmoss.json"
	var t0 = Time.get_ticks_usec()
	var txt = FileAccess.get_file_as_string(path)
	var m = JSON.parse_string(txt)
	var t_load = (Time.get_ticks_usec() - t0) / 1000.0
	var w = int(m.width); var h = int(m.height)
	var coll = []
	var layers = {}
	for l in m.layers:
		if l.type == "tilelayer": layers[l.name] = l.data
	coll = layers["collision"]
	# --- A* ---
	var t1 = Time.get_ticks_usec()
	var grid = AStarGrid2D.new()
	grid.region = Rect2i(0, 0, w, h)
	grid.cell_size = Vector2(16, 16)
	grid.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	grid.default_compute_heuristic = AStarGrid2D.HEURISTIC_OCTILE
	grid.default_estimate_heuristic = AStarGrid2D.HEURISTIC_OCTILE
	grid.update()
	var free = []
	for y in range(h):
		for x in range(w):
			if coll[y * w + x] != 0: grid.set_point_solid(Vector2i(x, y), true)
			else: free.append(Vector2i(x, y))
	var t_grid = (Time.get_ticks_usec() - t1) / 1000.0
	var seed_ = 12345
	var times = []; var lens = []
	for i in range(500):
		seed_ = (seed_ * 1664525 + 1013904223) & 0xFFFFFFFF
		var a = free[int((float(seed_) / 4294967296.0) * free.size())]
		seed_ = (seed_ * 1664525 + 1013904223) & 0xFFFFFFFF
		var b = free[int((float(seed_) / 4294967296.0) * free.size())]
		var ta = Time.get_ticks_usec()
		var p = grid.get_id_path(a, b)
		var dt = (Time.get_ticks_usec() - ta) / 1000.0
		if p.size() > 0: times.append(dt); lens.append(p.size())
	times.sort()
	var sum = 0.0
	for v in times: sum += v
	var lsum = 0.0
	for v in lens: lsum += v
	# --- TileMapLayer 建立（唔渲染）---
	var t2 = Time.get_ticks_usec()
	var img = Image.new(); img.load("../../art/town/town_tiles.png")
	var tex = ImageTexture.create_from_image(img)
	var ts = TileSet.new(); ts.tile_size = Vector2i(16, 16)
	var src = TileSetAtlasSource.new(); src.texture = tex; src.texture_region_size = Vector2i(16, 16)
	for i in range(40): src.create_tile(Vector2i(i % 16, i / 16))
	ts.add_source(src, 0)
	var made = 0
	for ln in ["ground", "decor", "occlusion"]:
		var tl = TileMapLayer.new(); tl.tile_set = ts
		var d = layers[ln]
		for i in range(w * h):
			if d[i] != 0:
				var gi = int(d[i]) - 1
				tl.set_cell(Vector2i(i % w, i / w), 0, Vector2i(gi % 16, gi / 16)); made += 1
		root.add_child(tl)
	var t_tm = (Time.get_ticks_usec() - t2) / 1000.0
	print(JSON.stringify({godot = Engine.get_version_info().string, map = path, jsonLoadMs = t_load, astarGridBuildMs = t_grid, astarN = times.size(), astarAvgMs = sum / max(1, times.size()), astarP95Ms = times[int(times.size() * 0.95)], astarMaxMs = times[times.size() - 1], avgPathLen = lsum / max(1, lens.size()), tilemapBuildMs = t_tm, cellsSet = made, renderer = RenderingServer.get_current_rendering_method()}))
	quit()
