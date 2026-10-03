extends RefCounted
## Revisioned local adapter. Exported world content is never modified here.

const MAX_BYTES: int = 262144
const FIELDS: Array[String] = ["schema_version", "world_id", "world_version", "character_id", "routine_id", "routine_epoch", "revision", "project_ids", "preferences"]

var _root: String
var _namespace: String
signal hosted_save_completed(result: Dictionary)
var _hosted_callback: JavaScriptObject
var _hosted_pending := false


func hosted_enabled() -> bool:
	if not OS.has_feature("web"):
		return false
	# Our pinned Web export returned a numeric Variant for eval(Boolean(...));
	# comparing it to a GDScript bool failed the typed expression during acceptance.
	# String transport is the same tested boundary used for all state responses.
	var enabled: Variant = JavaScriptBridge.eval("window.domesCloudState ? 'enabled' : 'disabled'", true)
	return enabled is String and enabled == "enabled"


func save_hosted_state(world_id: String, state: Dictionary, expected_revision: int) -> Dictionary:
	# The opt-in host bridge acknowledges a real server-side compare-and-swap.
	# A queued network request must never be reported as a successful save.
	var error := validate_state(state, world_id)
	if not error.is_empty():
		return _failure(error)
	if not hosted_enabled() or _hosted_pending:
		return _failure("hosted_save_unavailable_or_busy")
	_hosted_pending = true
	_hosted_callback = JavaScriptBridge.create_callback(_hosted_result)
	var window := JavaScriptBridge.get_interface("window")
	window.domesCloudState.save(JSON.stringify(state), expected_revision, _hosted_callback)
	var result: Dictionary = await hosted_save_completed
	_hosted_pending = false
	_hosted_callback = null
	if result.get("ok", false):
		var received: Variant = result.get("state")
		if not received is Dictionary or not validate_state(received, world_id).is_empty() or int(received.revision) != expected_revision + 1:
			return _failure("invalid_hosted_save_acknowledgment")
	return result


func _hosted_result(args: Array) -> void:
	var parsed: Variant = JSON.parse_string(str(args[0])) if args.size() == 1 else null
	hosted_save_completed.emit(parsed if parsed is Dictionary else _failure("invalid_hosted_save_response"))


func _init(storage_root: String = "user://state", storage_namespace: String = "domes-for-dots.v1") -> void:
	_root = storage_root
	_namespace = storage_namespace


func initial_state(world: Dictionary, character: Dictionary, routine: Dictionary, now: float) -> Dictionary:
	var project_ids: Array = []
	for project in routine.get("projects", []):
		project_ids.append(project.get("id", ""))
	return {"schema_version": 1, "world_id": world.get("id", ""), "world_version": world.get("version", ""), "character_id": character.get("id", ""), "routine_id": routine.get("id", ""), "routine_epoch": now, "revision": 0, "project_ids": project_ids, "preferences": {}}


func load_state(world_id: String) -> Dictionary:
	if not _valid_id(world_id):
		return _failure("invalid_world_id")
	var raw: Dictionary = _read_raw(world_id)
	if not raw["ok"]:
		return raw
	return _select_state(raw, world_id)


func save_state(world_id: String, state: Dictionary, expected_revision: int) -> Dictionary:
	var validation: String = validate_state(state, world_id)
	if not validation.is_empty():
		return _failure(validation)
	if expected_revision < 0 or int(state["revision"]) != expected_revision:
		return _failure("expected_revision_does_not_match_state")
	if expected_revision >= 9007199254740990:
		return _failure("revision_limit")
	if OS.has_feature("web"):
		return _save_web(world_id, state, expected_revision)
	var mkdir_error: Error = DirAccess.make_dir_recursive_absolute(_root)
	if mkdir_error != OK:
		return _failure("cannot_create_state_directory: " + error_string(mkdir_error))
	var lock_path: String = _path(world_id) + ".lock"
	var lock_error: Error = DirAccess.make_dir_absolute(lock_path)
	if lock_error != OK:
		return _failure("writer_busy_or_stale_lock: " + error_string(lock_error))
	var result: Dictionary = _save_native_locked(world_id, state, expected_revision)
	var unlock_error: Error = DirAccess.remove_absolute(lock_path)
	if unlock_error != OK:
		result["warning"] = "Save finished, but writer lock could not be removed: " + error_string(unlock_error)
	return result


func validate_state(state: Dictionary, world_id: String) -> String:
	if not _valid_id(world_id):
		return "invalid_world_id"
	if state.size() != FIELDS.size():
		return "invalid_state_fields"
	for field in FIELDS:
		if not state.has(field):
			return "missing_state_field: " + field
	if not _integer(state["schema_version"]) or int(state["schema_version"]) != 1:
		return "unsupported_state_schema"
	for field in ["world_id", "character_id", "routine_id"]:
		if not state[field] is String or not _valid_id(state[field]):
			return "invalid_state_identifier: " + field
	if state["world_id"] != world_id:
		return "state_world_mismatch"
	if not state["world_version"] is String or state["world_version"].is_empty() or state["world_version"].length() > 128:
		return "invalid_world_version"
	if not _number(state["routine_epoch"]) or float(state["routine_epoch"]) < 0.0:
		return "invalid_routine_epoch"
	if not _integer(state["revision"]) or float(state["revision"]) < 0.0 or float(state["revision"]) > 9007199254740991.0:
		return "invalid_revision"
	if not state["project_ids"] is Array or state["project_ids"].size() > 1024:
		return "invalid_project_ids"
	var seen: Dictionary = {}
	for project_id in state["project_ids"]:
		if not project_id is String or not _valid_id(project_id) or seen.has(project_id):
			return "invalid_or_duplicate_project_id"
		seen[project_id] = true
	if not state["preferences"] is Dictionary or not _json_safe(state["preferences"], 0):
		return "invalid_preferences"
	if JSON.stringify(state, "\t", true).to_utf8_buffer().size() + 1 > MAX_BYTES:
		return "state_too_large"
	return ""


func _save_native_locked(world_id: String, state: Dictionary, expected_revision: int) -> Dictionary:
	var raw: Dictionary = _read_raw(world_id)
	if not raw["ok"]:
		return raw
	var current: Dictionary = _select_state(raw, world_id)
	if not current["ok"]:
		return current
	var current_revision: int = int(current["state"].get("revision", 0))
	if current_revision != expected_revision:
		return _failure("revision_conflict")
	var next: Dictionary = state.duplicate(true)
	next["revision"] = expected_revision + 1
	var path: String = _path(world_id)
	var payload: String = JSON.stringify(next, "\t", true) + "\n"
	var error: String = _write_verified(path + ".tmp", payload)
	if not error.is_empty():
		return _failure(error)
	# Establish a valid backup before touching primary, including on the first save.
	# After recovery, preserve the good backup instead of copying the corrupt primary.
	if not current.get("recovered", false):
		var backup_state: Dictionary = current["state"] if current["found"] else next
		error = _write_verified(path + ".bak.tmp", JSON.stringify(backup_state, "\t", true) + "\n")
		if error.is_empty():
			error = _replace(path + ".bak.tmp", path + ".bak")
		if not error.is_empty():
			return _failure(error)
	error = _replace(path + ".tmp", path)
	if not error.is_empty():
		return _failure(error + "; known-good backup retained")
	var confirmed: Dictionary = _decode(FileAccess.get_file_as_string(path), world_id)
	if not confirmed["ok"] or FileAccess.get_file_as_string(path) != payload:
		return _failure("post_write_verification_failed; known-good backup retained")
	return {"ok": true, "state": confirmed["state"], "error": "", "recovered": current.get("recovered", false)}


func _save_web(world_id: String, state: Dictionary, expected_revision: int) -> Dictionary:
	var raw: Dictionary = _read_raw(world_id)
	if not raw["ok"]:
		return raw
	var current: Dictionary = _select_state(raw, world_id)
	if not current["ok"]:
		return current
	if int(current["state"].get("revision", 0)) != expected_revision:
		return _failure("revision_conflict")
	var next: Dictionary = state.duplicate(true)
	next["revision"] = expected_revision + 1
	var backup: Dictionary = current["state"] if current["found"] else next
	var arguments: String = JSON.stringify({"key": _key(world_id), "expected_raw": raw["primary"], "next_raw": JSON.stringify(next), "backup_raw": JSON.stringify(backup)})
	# Synchronous within this browser context. localStorage is NOT cross-tab CAS.
	var script: String = """(function(a) { try {
if (localStorage.getItem(a.key) !== a.expected_raw) return JSON.stringify({ok:false,error:'revision_conflict'});
localStorage.setItem(a.key + '.bak', a.backup_raw);
localStorage.setItem(a.key, a.next_raw);
if (localStorage.getItem(a.key) !== a.next_raw) return JSON.stringify({ok:false,error:'concurrent_write_detected'});
return JSON.stringify({ok:true,error:''});
} catch(e) { return JSON.stringify({ok:false,error:'browser_storage_error: ' + String(e)}); } })(%s)""" % arguments
	var result: Dictionary = _eval_json(script)
	if not result.get("ok", false):
		return _failure(str(result.get("error", "browser_storage_unavailable")))
	return {"ok": true, "state": JSON.parse_string(JSON.stringify(next)), "error": "", "recovered": current.get("recovered", false)}


func _read_raw(world_id: String) -> Dictionary:
	if OS.has_feature("web"):
		if hosted_enabled():
			return _eval_json("window.domesCloudState.read(" + JSON.stringify(world_id) + ")")
		var script: String = """(function(k) { try { return JSON.stringify({ok:true,primary:localStorage.getItem(k),backup:localStorage.getItem(k+'.bak')}); } catch(e) { return JSON.stringify({ok:false,error:'browser_storage_error: '+String(e)}); } })(%s)""" % JSON.stringify(_key(world_id))
		return _eval_json(script)
	var result: Dictionary = {"ok": true, "primary": null, "backup": null}
	for entry in [["primary", _path(world_id)], ["backup", _path(world_id) + ".bak"]]:
		if not FileAccess.file_exists(entry[1]):
			continue
		var file: FileAccess = FileAccess.open(entry[1], FileAccess.READ)
		if file == null:
			return _failure("state_read_failed: " + error_string(FileAccess.get_open_error()))
		if file.get_length() > MAX_BYTES:
			result[entry[0]] = "__oversized_invalid_state__"
		else:
			result[entry[0]] = file.get_as_text()
		file.close()
	return result


func _select_state(raw: Dictionary, world_id: String) -> Dictionary:
	if raw.get("primary") == null and raw.get("backup") == null:
		return {"ok": true, "found": false, "state": {}, "error": "", "recovered": false}
	var primary: Dictionary = _decode(raw.get("primary"), world_id)
	if primary["ok"]:
		return {"ok": true, "found": true, "state": primary["state"], "error": "", "recovered": false}
	var backup: Dictionary = _decode(raw.get("backup"), world_id)
	if backup["ok"]:
		return {"ok": true, "found": true, "state": backup["state"], "error": "Recovered known-good backup; primary state was absent or invalid.", "recovered": true}
	return _failure("corrupt_state_and_backup: " + str(primary["error"]))


func _decode(raw: Variant, world_id: String) -> Dictionary:
	if not raw is String or raw.to_utf8_buffer().size() > MAX_BYTES:
		return _failure("missing_or_oversized_state")
	var json: JSON = JSON.new()
	if json.parse(raw) != OK or not json.data is Dictionary:
		return _failure("invalid_state_json")
	var validation: String = validate_state(json.data, world_id)
	if not validation.is_empty():
		return _failure(validation)
	return {"ok": true, "state": json.data, "error": ""}


func _write_verified(path: String, payload: String) -> String:
	if payload.to_utf8_buffer().size() > MAX_BYTES:
		return "state_too_large"
	var file: FileAccess = FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return "state_write_failed: " + error_string(FileAccess.get_open_error())
	file.store_string(payload)
	file.flush()
	var write_error: Error = file.get_error()
	file.close()
	if write_error != OK:
		return "state_write_failed: " + error_string(write_error)
	if FileAccess.get_file_as_string(path) != payload:
		return "temporary_state_verification_failed"
	return ""


func _replace(source: String, destination: String) -> String:
	if FileAccess.file_exists(destination):
		var remove_error: Error = DirAccess.remove_absolute(destination)
		if remove_error != OK:
			return "state_replace_failed: " + error_string(remove_error)
	var rename_error: Error = DirAccess.rename_absolute(source, destination)
	if rename_error != OK:
		return "state_rename_failed: " + error_string(rename_error)
	return ""


func _eval_json(script: String) -> Dictionary:
	var response: Variant = JavaScriptBridge.eval(script, true)
	if not response is String:
		return _failure("browser_storage_unavailable")
	var parsed: Variant = JSON.parse_string(response)
	if not parsed is Dictionary:
		return _failure("invalid_browser_storage_response")
	return parsed


func _path(world_id: String) -> String:
	return _root.path_join(world_id + ".json")


func _key(world_id: String) -> String:
	return _namespace + ":" + world_id


func _valid_id(value: String) -> bool:
	if value.is_empty() or value.length() > 100:
		return false
	for character in value:
		if not character in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-":
			return false
	return true


func _json_safe(value: Variant, depth: int) -> bool:
	if depth > 8:
		return false
	if value == null or value is bool or value is String:
		return true
	if value is int or value is float:
		return is_finite(float(value))
	if value is Array:
		if value.size() > 1024:
			return false
		for item in value:
			if not _json_safe(item, depth + 1):
				return false
		return true
	if value is Dictionary:
		if value.size() > 1024:
			return false
		for key in value:
			if not key is String or key.length() > 128 or not _json_safe(value[key], depth + 1):
				return false
		return true
	return false


func _number(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value))


func _integer(value: Variant) -> bool:
	return _number(value) and float(value) == floor(float(value))


func _failure(error: String) -> Dictionary:
	return {"ok": false, "found": false, "state": {}, "error": error}
