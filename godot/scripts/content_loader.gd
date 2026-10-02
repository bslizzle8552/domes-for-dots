extends RefCounted
## Only bundled, local content is loaded. Schemas and cross-reference checks run before export.

static func read_json(path: String) -> Dictionary:
	if not path.begins_with("res://content/") or ".." in path:
		return {"error": "Content path must stay under res://content/"}
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {"error": "Cannot read content: " + path}
	var parsed = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary or parsed.get("schema_version") != 1:
		return {"error": "Unsupported or invalid content: " + path}
	return parsed

static func bundle(path: String) -> Dictionary:
	var world := read_json(path)
	if world.has("error"):
		return world
	for key in ["id", "title", "character_path", "routine_path", "asset_manifest_paths", "zones", "objects", "stations", "spawn", "environment", "camera", "navigation"]:
		if not world.has(key):
			return {"error": "Missing world field: " + key}
	var character := read_json(world.character_path)
	var routine := read_json(world.routine_path)
	if character.has("error") or routine.has("error"):
		return {"error": "Character or routine could not be loaded"}
	var assets: Dictionary = {}
	for manifest_path in world.asset_manifest_paths:
		var manifest := read_json(manifest_path)
		if manifest.has("error"):
			return manifest
		for asset in manifest.get("assets", []):
			if assets.has(asset.id):
				return {"error": "Duplicate asset ID: " + asset.id}
			assets[asset.id] = asset
	for object in world.objects:
		if not assets.has(object.asset_id):
			return {"error": "Unknown asset ID: " + object.asset_id}
	return {"world": world, "character": character, "routine": routine, "assets": assets}

