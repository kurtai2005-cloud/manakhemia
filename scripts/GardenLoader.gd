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



static func solidify_mesh(src: ArrayMesh, thickness: float) -> ArrayMesh:
	# 把薄面擠出厚度（法線朝室內／向上，向外擠），補齊外牆同孔洞側壁，令房間係立體盒而唔係平面層。
	if src == null or thickness <= 0.001 or src.get_surface_count() < 1:
		return src
	var arr: Array = src.surface_get_arrays(0)
	if arr.is_empty() or arr[Mesh.ARRAY_VERTEX] == null or arr[Mesh.ARRAY_INDEX] == null:
		return src
	var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var uvs: PackedVector2Array = PackedVector2Array()
	if arr[Mesh.ARRAY_TEX_UV] != null:
		uvs = arr[Mesh.ARRAY_TEX_UV]
	var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
	var seen: Dictionary = {}
	var faces: Array = []
	var t := 0
	while t + 2 < idx.size():
		var i0 := int(idx[t])
		var i1 := int(idx[t + 1])
		var i2 := int(idx[t + 2])
		t += 3
		if i0 >= verts.size() or i1 >= verts.size() or i2 >= verts.size():
			continue
		var a: Vector3 = verts[i0]
		var b: Vector3 = verts[i1]
		var c: Vector3 = verts[i2]
		var n: Vector3 = (b - a).cross(c - a)
		if n.length_squared() < 0.000001:
			continue
		n = n.normalized()
		var key := _face_key(a, b, c)
		if seen.has(key):
			continue
		seen[key] = true
		faces.append({"i0": i0, "i1": i1, "i2": i2, "n": n})
	if faces.is_empty():
		return src
	var edge_use: Dictionary = {}
	var edge_info: Dictionary = {}
	for f in faces:
		_note_edge(edge_use, edge_info, verts[f["i0"]], verts[f["i1"]], f["i0"], f["i1"], f["n"])
		_note_edge(edge_use, edge_info, verts[f["i1"]], verts[f["i2"]], f["i1"], f["i2"], f["n"])
		_note_edge(edge_use, edge_info, verts[f["i2"]], verts[f["i0"]], f["i2"], f["i0"], f["n"])
	var nv := PackedVector3Array()
	var nn := PackedVector3Array()
	var nu := PackedVector2Array()
	var ni := PackedInt32Array()
	for f in faces:
		var i0: int = f["i0"]
		var i1: int = f["i1"]
		var i2: int = f["i2"]
		var n: Vector3 = f["n"]
		var out := -n * thickness
		var p0: Vector3 = verts[i0]
		var p1: Vector3 = verts[i1]
		var p2: Vector3 = verts[i2]
		var u0 := uvs[i0] if i0 < uvs.size() else Vector2.ZERO
		var u1 := uvs[i1] if i1 < uvs.size() else Vector2.ZERO
		var u2 := uvs[i2] if i2 < uvs.size() else Vector2.ZERO
		_emit_tri(nv, nn, nu, ni, p0, p1, p2, n, u0, u1, u2)
		_emit_tri(nv, nn, nu, ni, p0 + out, p2 + out, p1 + out, -n, u0, u2, u1)
	for ek in edge_use.keys():
		if int(edge_use[ek]) != 1:
			continue
		var info: Dictionary = edge_info[ek]
		var p0: Vector3 = info["p0"]
		var p1: Vector3 = info["p1"]
		var n: Vector3 = info["n"]
		var out := -n * thickness
		var i0: int = info["i0"]
		var i1: int = info["i1"]
		var u0 := uvs[i0] if i0 < uvs.size() else Vector2.ZERO
		var u1 := uvs[i1] if i1 < uvs.size() else Vector2.ZERO
		var side_n: Vector3 = (p1 - p0).cross(out)
		if side_n.length_squared() < 0.000001:
			continue
		side_n = side_n.normalized()
		_emit_tri(nv, nn, nu, ni, p0, p1, p1 + out, side_n, u0, u1, u1)
		_emit_tri(nv, nn, nu, ni, p0, p1 + out, p0 + out, side_n, u0, u1, u0)
	var out_arr: Array = []
	out_arr.resize(Mesh.ARRAY_MAX)
	out_arr[Mesh.ARRAY_VERTEX] = nv
	out_arr[Mesh.ARRAY_NORMAL] = nn
	out_arr[Mesh.ARRAY_TEX_UV] = nu
	out_arr[Mesh.ARRAY_INDEX] = ni
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, out_arr)
	return am


static func _face_key(a: Vector3, b: Vector3, c: Vector3) -> String:
	var pts: Array = [a, b, c]
	pts.sort_custom(func(p: Vector3, q: Vector3) -> bool:
		if p.x != q.x:
			return p.x < q.x
		if p.y != q.y:
			return p.y < q.y
		return p.z < q.z
	)
	return "%s|%s|%s" % [_vec_key(pts[0]), _vec_key(pts[1]), _vec_key(pts[2])]


static func _vec_key(v: Vector3) -> String:
	return "%d,%d,%d" % [int(round(v.x * 100.0)), int(round(v.y * 100.0)), int(round(v.z * 100.0))]


static func _edge_key(a: Vector3, b: Vector3) -> String:
	var ka := _vec_key(a)
	var kb := _vec_key(b)
	if ka < kb:
		return ka + ">" + kb
	return kb + ">" + ka


static func _note_edge(use_c: Dictionary, info: Dictionary, a: Vector3, b: Vector3, ia: int, ib: int, n: Vector3) -> void:
	var k := _edge_key(a, b)
	use_c[k] = int(use_c.get(k, 0)) + 1
	if not info.has(k):
		info[k] = {"p0": a, "p1": b, "i0": ia, "i1": ib, "n": n}


static func _emit_tri(nv: PackedVector3Array, nn: PackedVector3Array, nu: PackedVector2Array, ni: PackedInt32Array, a: Vector3, b: Vector3, c: Vector3, n: Vector3, ua: Vector2, ub: Vector2, uc: Vector2) -> void:
	var base := nv.size()
	nv.append(a)
	nv.append(b)
	nv.append(c)
	nn.append(n)
	nn.append(n)
	nn.append(n)
	nu.append(ua)
	nu.append(ub)
	nu.append(uc)
	ni.append(base)
	ni.append(base + 1)
	ni.append(base + 2)
