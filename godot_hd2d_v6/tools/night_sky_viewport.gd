extends SceneTree
## Rasterize one ground quad with vc27 sky×albedo. Exit 2 if headless has no image.


var _vp: SubViewport
var _frames := 0


func _initialize() -> void:
	var img := Image.load_from_file("/tmp/v618-assets/godot_hd2d_v6/textures/ground_composed_low.png")
	if img == null:
		push_error("night_sky_viewport: texture missing")
		quit(1)
		return
	var tex := ImageTexture.create_from_image(img)
	_vp = SubViewport.new()
	_vp.size = Vector2i(128, 128)
	_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0, 0, 0)
	env.ambient_light_energy = 0.0
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = 1.35
	var we := WorldEnvironment.new()
	we.environment = env
	_vp.add_child(we)
	var cam := Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = 2.0
	cam.current = true
	cam.position = Vector3(0, 2, 0)
	cam.look_at(Vector3.ZERO, Vector3(0, 0, -1))
	_vp.add_child(cam)
	var mi := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(2, 2)
	mi.mesh = pm
	var mat := ShaderMaterial.new()
	mat.shader = load("res://shaders/texel_lit.gdshader")
	mat.set_shader_parameter("albedo_tex", tex)
	mat.set_shader_parameter("night_toe_gain", 1.0)
	mat.set_shader_parameter("night_sky_rgb", Vector3(0.70, 0.92, 1.00))
	mi.material_override = mat
	_vp.add_child(mi)
	root.add_child(_vp)


func _process(_dt: float) -> bool:
	_frames += 1
	if _frames < 4:
		return false
	var out := _vp.get_texture().get_image()
	if out == null or out.get_width() == 0:
		push_error("night_sky_viewport: no raster image")
		quit(2)
		return true
	var acc := Vector3.ZERO
	var n := 0
	for y in range(0, out.get_height(), 2):
		for x in range(0, out.get_width(), 2):
			var c := out.get_pixel(x, y)
			acc += Vector3(c.r, c.g, c.b)
			n += 1
	acc /= float(maxi(n, 1))
	print("vc27 viewport mean=", acc, " B/G=", acc.z / maxf(acc.y, 0.001), " n=", n)
	out.save_png("/tmp/vc27_ground_viewport.png")
	quit(0 if acc.y > acc.z and acc.y > 0.02 else 3)
	return true