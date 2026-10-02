extends RefCounted
## In-memory leases, not an integration. The caller must establish source authority.

const MAX_TTL_SECONDS: float = 60.0
const FUTURE_SKEW_SECONDS: float = 5.0
const EVENT_CACHE_LIMIT: int = 2048
const FIELDS: Array[String] = ["schema_version", "event_id", "activity_id", "source", "sequence", "kind", "operation", "timestamp", "ttl_seconds", "world_id", "character_id"]

var _world_id: String = ""
var _character_id: String = ""
var _leases: Dictionary = {}
var _sequences: Dictionary = {}
var _timestamps: Dictionary = {}
var _tombstones: Dictionary = {}
var _events: Dictionary = {}
var _event_order: Array[String] = []


func configure(world_id: String, character_id: String) -> void:
	_world_id = world_id
	_character_id = character_id
	_leases.clear()
	_sequences.clear()
	_timestamps.clear()
	_tombstones.clear()
	_events.clear()
	_event_order.clear()


func apply(event: Dictionary, now: float, trusted_source: String = "mock") -> Dictionary:
	if not is_finite(now) or now < 0.0:
		return _reject("invalid_clock")
	_expire(now)
	var invalid: String = _validate(event)
	if not invalid.is_empty():
		return _reject(invalid)
	if _world_id.is_empty() or _character_id.is_empty():
		return _reject("not_configured")
	if event["world_id"] != _world_id or event["character_id"] != _character_id:
		return _reject("wrong_target")
	if trusted_source.is_empty() or event["source"] != trusted_source:
		return _reject("untrusted_source")
	var event_id: String = event["event_id"]
	var fingerprint: String = JSON.stringify(event, "", true)
	if _events.has(event_id):
		if _events[event_id] != fingerprint:
			return _reject("event_id_collision")
		return {"accepted": true, "reason": "duplicate"}
	var stream: String = _stream(event)
	var activity: String = _activity(event)
	var sequence: int = int(event["sequence"])
	var timestamp: float = float(event["timestamp"])
	var operation: String = event["operation"]
	if timestamp > now + FUTURE_SKEW_SECONDS:
		return _reject("future_timestamp")
	if sequence <= int(_sequences.get(stream, -1)):
		return _reject("stale_sequence")
	if timestamp < float(_timestamps.get(stream, -1.0)):
		return _reject("stale_timestamp")
	if operation != "end" and _tombstones.has(activity):
		return _reject("activity_ended")
	var expires_at: float = timestamp + float(event["ttl_seconds"])
	if operation != "end" and expires_at <= now:
		return _reject("expired_event")
	if operation == "renew":
		if not _leases.has(stream) or _activity(_leases[stream]) != activity:
			return _reject("no_live_activity")
	if operation == "start" and _leases.has(stream):
		if _activity(_leases[stream]) == activity:
			return _reject("already_started")
		_tombstones[_activity(_leases[stream])] = true
	_sequences[stream] = sequence
	_timestamps[stream] = timestamp
	if operation == "end":
		_tombstones[activity] = true
		if _leases.has(stream) and _activity(_leases[stream]) == activity:
			_leases.erase(stream)
	else:
		var lease: Dictionary = event.duplicate(true)
		lease["expires_at"] = expires_at
		_leases[stream] = lease
	_events[event_id] = fingerprint
	_event_order.append(event_id)
	if _event_order.size() > EVENT_CACHE_LIMIT:
		_events.erase(_event_order.pop_front())
	return {"accepted": true, "reason": "applied"}


func active(now: float) -> Dictionary:
	if not is_finite(now):
		return {}
	_expire(now)
	var result: Dictionary = {}
	for lease in _leases.values():
		if result.is_empty() or _higher_priority(lease, result):
			result = lease
	return result.duplicate(true)


func _higher_priority(candidate: Dictionary, current: Dictionary) -> bool:
	if candidate["kind"] != current["kind"]:
		return candidate["kind"] == "call"
	if candidate["timestamp"] != current["timestamp"]:
		return candidate["timestamp"] > current["timestamp"]
	return str(candidate["event_id"]) > str(current["event_id"])


func _expire(now: float) -> void:
	for stream in _leases.keys():
		if float(_leases[stream]["expires_at"]) <= now:
			_tombstones[_activity(_leases[stream])] = true
			_leases.erase(stream)


func _stream(event: Dictionary) -> String:
	return JSON.stringify([event["source"], event["kind"]])


func _activity(event: Dictionary) -> String:
	return JSON.stringify([event["source"], event["kind"], event["activity_id"]])


func _validate(event: Dictionary) -> String:
	if event.size() != FIELDS.size():
		return "invalid_fields"
	for field in FIELDS:
		if not event.has(field):
			return "missing_field"
	if not _integer(event["schema_version"]) or int(event["schema_version"]) != 1:
		return "unsupported_schema"
	for field in ["event_id", "activity_id", "source", "world_id", "character_id"]:
		if not event[field] is String or event[field].is_empty() or event[field].length() > 128:
			return "invalid_identifier"
	if not _integer(event["sequence"]) or float(event["sequence"]) < 1.0 or float(event["sequence"]) > 9007199254740991.0:
		return "invalid_sequence"
	if not event["kind"] in ["work", "call"] or not event["operation"] in ["start", "renew", "end"]:
		return "invalid_operation"
	if not _number(event["timestamp"]) or float(event["timestamp"]) < 0.0:
		return "invalid_timestamp"
	if not _number(event["ttl_seconds"]):
		return "invalid_ttl"
	var ttl: float = float(event["ttl_seconds"])
	if ttl > MAX_TTL_SECONDS or ttl < 0.0 or (event["operation"] != "end" and ttl == 0.0):
		return "invalid_ttl"
	return ""


func _number(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value))


func _integer(value: Variant) -> bool:
	return _number(value) and float(value) == floor(float(value))


func _reject(reason: String) -> Dictionary:
	return {"accepted": false, "reason": reason}
