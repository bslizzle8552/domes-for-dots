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


static func hosted_bundle(original: Dictionary) -> Dictionary:
	# Opt-in deployment adapter. The external bridge hashes the immutable bundle
	# against the operator-published registry before exposing it here. Compilation
	# and full spatial validation remain mandatory at package/deployment intake.
	# This data lane cannot introduce another character resource or executable scene.
	if not OS.has_feature("web") or original.has("error"):
		return original
	var raw: Variant = JavaScriptBridge.eval("window.domesHostedBundle ? JSON.stringify(window.domesHostedBundle) : null", true)
	if raw == null:
		return original
	if not raw is String or raw.to_utf8_buffer().size() > 2097152:
		return {"error": "Hosted bundle exceeds the supported data boundary"}
	var data: Variant = JSON.parse_string(raw)
	if not data is Dictionary or data.size() != 4:
		return {"error": "Hosted bundle must contain world, character, routine and assets"}
	for key in ["world", "character", "routine", "assets"]:
		if not data.get(key) is Dictionary:
			return {"error": "Invalid hosted bundle field: " + key}
	if data.world.get("id") != original.world.get("id"):
		return original
	if data.character != original.character:
		return {"error": "Dynamic character replacement requires a reviewed engine export"}
	if data.routine != original.routine:
		return {"error": "Dynamic routine changes require an explicit timeline migration"}
	if data.assets.size() > 128 or not data.world.get("objects") is Array or data.world.objects.size() > 256:
		return {"error": "Hosted bundle geometry exceeds supported bounds"}
	for asset in data.assets.values():
		if not asset is Dictionary or asset.get("scene_path", "") != "" or asset.has("model_path"):
			return {"error": "Hosted assets must be approved primitive recipes"}
		if not asset.get("parts") is Array or asset.parts.size() > 64:
			return {"error": "Invalid hosted primitive recipe"}
		for part in asset.parts:
			if not part is Dictionary or not part.get("shape") in ["box", "sphere", "cylinder"]:
				return {"error": "Unsupported hosted primitive"}
	for object in data.world.objects:
		if not object is Dictionary or not data.assets.has(object.get("asset_id", "")):
			return {"error": "Unresolved hosted object asset"}
	for station in data.world.get("stations", []):
		if not station is Dictionary or not station.get("behavior", "") in ["", "activity_light"]:
			return {"error": "Unsupported hosted station behavior"}
	return data
