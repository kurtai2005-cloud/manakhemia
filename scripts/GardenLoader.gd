extends Node
class_name GardenLoader
## 載入 garden3d.mesh/2 JSON＋PNG，砌 ArrayMesh。UV 由 V-up 翻成 Godot。

const ROOT := "res://art/garden3d/H1/"
const OBJ_PATH := ROOT + "objects.json"
const CAM_PATH := ROOT + "camera.json"
const LIGHT_PATH := ROOT + "lights.json"

static func load_json(path: String) -> Dictionary:
	var raw := FileAccess.get_file_as_string(path)
	var p: Variant = JSON.parse_string(raw)
	return p if typeof(p) == TYPE_DICTIONARY else {}


static func hex_color(s: String, default_v: Color = Color.WHITE) -> Color:
	var t := s.strip_edges()
	if t.begins_with("#"):
		return Color.html(t)
	return default_v


static func make_tex(path: String) -> Texture2D:
	var tex: Texture2D = load(path) as Texture2D
	return tex


static func make_mat(tex: Texture2D, unlit: bool, alpha_cut: float = 0.5, emissive: Texture2D = null) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_texture = tex
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	m.texture_repeat = false
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	m.alpha_scissor_threshold = alpha_cut
	m.cull_mode = BaseMaterial3D.CULL_BACK
	m.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	if unlit:
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	else:
		m.shading_mode = BaseMaterial3D.SHADING_MODE_PER_PIXEL
		m.diffuse_mode = BaseMaterial3D.DIFFUSE_LAMBERT
	if emissive:
		m.emission_enabled = true
		m.emission_texture = emissive
		m.emission_energy_multiplier = 0.0  # 日間關；夜景再開
	return m


static func mesh_from_json(data: Dictionary, flip_v: bool = true) -> ArrayMesh:
	var pos: Array = data.get("positions", [])
	var nrm: Array = data.get("normals", [])
	var uvs: Array = data.get("uvs", [])
	var idx: Array = data.get("indices", [])
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var uv := PackedVector2Array()
	var i := 0
	while i + 2 < pos.size():
		vertices.append(Vector3(float(pos[i]), float(pos[i + 1]), float(pos[i + 2])))
		i += 3
	i = 0
	while i + 2 < nrm.size():
		normals.append(Vector3(float(nrm[i]), float(nrm[i + 1]), float(nrm[i + 2])))
		i += 3
	i = 0
	while i + 1 < uvs.size():
		var v := float(uvs[i + 1])
		if flip_v:
			v = 1.0 - v
		uv.append(Vector2(float(uvs[i]), v))
		i += 2
	var indices := PackedInt32Array()
	for n in idx:
		indices.append(int(n))
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	if normals.size() == vertices.size():
		arrays[Mesh.ARRAY_NORMAL] = normals
	if uv.size() == vertices.size():
		arrays[Mesh.ARRAY_TEX_UV] = uv
	arrays[Mesh.ARRAY_INDEX] = indices
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return am


static func ground_mesh(size: float, uv_scale: float = 1.0, flip_v: bool = false) -> ArrayMesh:
	# 平面 XZ，中心 0，邊長 size。u=(x+size/2)/size，v=(z+size/2)/size
	var h := size * 0.5
	var verts := PackedVector3Array([
		Vector3(-h, 0, -h), Vector3(h, 0, -h), Vector3(h, 0, h), Vector3(-h, 0, h)
	])
	var nrm := PackedVector3Array([Vector3.UP, Vector3.UP, Vector3.UP, Vector3.UP])
	var u0 := 0.0
	var u1 := uv_scale
	var v0 := 0.0 if not flip_v else uv_scale
	var v1 := uv_scale if not flip_v else 0.0
	# z=-h 係遠（圖頂）。v 跟圖頂＝0（唔翻）或按需要。
	var uv := PackedVector2Array([
		Vector2(u0, v0), Vector2(u1, v0), Vector2(u1, v1), Vector2(u0, v1)
	])
	var idx := PackedInt32Array([0, 2, 1, 0, 3, 2])  # 上向
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = nrm
	arrays[Mesh.ARRAY_TEX_UV] = uv
	arrays[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return am


static func backdrop_mesh(w: float, h: float) -> ArrayMesh:
	# 固定朝 +Z（鏡頭），pivot 底中 (0.5, 1.0)
	var verts := PackedVector3Array([
		Vector3(-w * 0.5, 0, 0), Vector3(w * 0.5, 0, 0),
		Vector3(w * 0.5, h, 0), Vector3(-w * 0.5, h, 0)
	])
	var nrm := PackedVector3Array([Vector3(0, 0, 1), Vector3(0, 0, 1), Vector3(0, 0, 1), Vector3(0, 0, 1)])
	var uv := PackedVector2Array([
		Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)
	])
	var idx := PackedInt32Array([0, 1, 2, 0, 2, 3])
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = nrm
	arrays[Mesh.ARRAY_TEX_UV] = uv
	arrays[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return am


## 可靠 XZ 地平面（SurfaceTool，法線向上）。uv_origin／uv_unit：u=(x-ox)/unit，v=(z-oz)/unit。
static func xz_plane(x0: float, x1: float, z0: float, z1: float, uv_origin: Vector2, uv_unit: float) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var pts := [
		Vector3(x0, 0, z0), Vector3(x1, 0, z0),
		Vector3(x1, 0, z1), Vector3(x0, 0, z1)
	]
	var uvs: Array = []
	for p in pts:
		uvs.append(Vector2((p.x - uv_origin.x) / uv_unit, (p.z - uv_origin.y) / uv_unit))
	# 由 +Y 睇 CCW：0-3-1、1-3-2
	var order := PackedInt32Array([0, 3, 1, 1, 3, 2])
	for i in order:
		st.set_normal(Vector3.UP)
		st.set_uv(uvs[i])
		st.add_vertex(pts[i])
	st.generate_normals()
	return st.commit()


static func opaque_tex_mat(tex: Texture2D, unlit: bool, repeat: bool, aniso_mip: bool = false) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_texture = tex
	m.albedo_color = Color(1, 1, 1, 1)
	# 遠景 repeat 草地：nearest + mip + 各向異性，收斂摩爾紋，近處仍偏像素風
	if aniso_mip:
		m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS_ANISOTROPIC
	else:
		m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	m.texture_repeat = repeat
	m.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED if unlit else BaseMaterial3D.SHADING_MODE_PER_PIXEL
	if not unlit:
		m.diffuse_mode = BaseMaterial3D.DIFFUSE_LAMBERT
	return m
