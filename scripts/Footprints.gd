extends RefCounted
class_name Footprints
## 世界座標 footprint 碰撞（寵物半徑外擴 pad）。

var rects: Array = []  # {x0,x1,z0,z1}
var polys: Array = []  # PackedVector2Array + pad

func load_from_objects(objects: Array) -> void:
	rects.clear()
	polys.clear()
	for o in objects:
		if typeof(o) != TYPE_DICTIONARY:
			continue
		var fp: Variant = o.get("footprint", null)
		if fp == null or typeof(fp) != TYPE_DICTIONARY:
			continue
		var pad := float(fp.get("pad", 0))
		if str(fp.get("type", "")) == "rect":
			var xr: Array = fp.get("x", [0, 0])
			var zr: Array = fp.get("z", [0, 0])
			rects.append({
				"x0": float(xr[0]) - pad, "x1": float(xr[1]) + pad,
				"z0": float(zr[0]) - pad, "z1": float(zr[1]) + pad,
			})
		elif str(fp.get("type", "")) == "poly":
			var pts: Array = fp.get("points", [])
			var pv := PackedVector2Array()
			for p in pts:
				pv.append(Vector2(float(p[0]), float(p[1])))
			polys.append({"pts": pv, "pad": pad})


func blocked(x: float, z: float, radius: float = 10.0) -> bool:
	for r in rects:
		if x + radius >= r["x0"] and x - radius <= r["x1"] and z + radius >= r["z0"] and z - radius <= r["z1"]:
			return true
	for p in polys:
		if _in_poly_padded(x, z, p["pts"], float(p["pad"]) + radius):
			return true
	return false


func _in_poly_padded(x: float, z: float, pts: PackedVector2Array, pad: float) -> bool:
	if Geometry2D.is_point_in_polygon(Vector2(x, z), pts):
		return true
	# 外擴：同邊嘅距離
	for i in range(pts.size()):
		var a: Vector2 = pts[i]
		var b: Vector2 = pts[(i + 1) % pts.size()]
		if _dist_seg(Vector2(x, z), a, b) <= pad:
			return true
	return false


func _dist_seg(p: Vector2, a: Vector2, b: Vector2) -> float:
	var ab := b - a
	var t := 0.0 if ab.length_squared() < 1e-8 else clampf((p - a).dot(ab) / ab.length_squared(), 0.0, 1.0)
	return p.distance_to(a + ab * t)


func random_free(rng: RandomNumberGenerator, radius: float = 10.0, x0 := -140.0, x1 := 140.0, z0 := -35.0, z1 := 160.0) -> Vector3:
	for _i in range(40):
		var x := rng.randf_range(x0, x1)
		var z := rng.randf_range(z0, z1)
		if not blocked(x, z, radius):
			return Vector3(x, 0, z)
	return Vector3(0, 0, 40)
