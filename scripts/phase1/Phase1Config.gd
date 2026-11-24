class_name Phase1Config
extends RefCounted

const PATH := "res://data/phase1_catalog.json"

static func load_doc() -> Dictionary:
	if not FileAccess.file_exists(PATH):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	if parsed is Dictionary:
		return parsed
	return {}


static func species(doc: Dictionary, sid: String) -> Dictionary:
	for item in doc.get("species", []):
		if item is Dictionary and str(item.get("id", "")) == sid:
			return item
	return {}


static func zone(doc: Dictionary, zid: String) -> Dictionary:
	for item in doc.get("zones", []):
		if item is Dictionary and str(item.get("id", "")) == zid:
			return item
	return {}


static func node(node_name: String) -> Node:
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return null
	return tree.root.get_node_or_null(node_name)


static func food(doc: Dictionary, fid: String) -> Dictionary:
	for item in doc.get("foods", []):
		if item is Dictionary and str(item.get("id", "")) == fid:
			return item
	return {}
