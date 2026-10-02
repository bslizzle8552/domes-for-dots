extends RefCounted
## Transient, inspectable activity intent. Animation and physical arrival are observations.
## Never persisted as a real activity report or used to replay a lease after reload.

var current_activity: Dictionary = {}
var previous_activity: Dictionary = {}


static func resolve(simulation: Dictionary, active: Dictionary, manual_station: String, stations: Array, paused: bool, now: float) -> Dictionary:
	var step: Dictionary = simulation.get("step", {})
	var activity := {"id": "routine:%s:%s" % [step.get("id", "idle"), simulation.get("cycle_index", 0)], "tag": str(step.get("activity_tag", "")), "label": str(step.get("label", "Resting")), "source": "simulated", "started_at": float(simulation.get("step_started_at", now)), "ends_at": float(simulation.get("step_ends_at", 0.0)), "routine_step_id": str(step.get("id", "")), "externally_triggered": false}
	var target: String = str(step.get("station_id", ""))
	if not active.is_empty():
		var tag: String = str(active.get("activity_tag", active.kind)) if active.kind == "work" else "call"
		activity = {"id": str(active.activity_id), "tag": tag, "label": tag.replace("_", " ").capitalize(), "source": "mock" if active.source == "mock" else "reported", "started_at": float(active.get("started_at", active.timestamp)), "ends_at": float(active.expires_at), "routine_step_id": "", "externally_triggered": true}
		target = ""
	elif not manual_station.is_empty():
		activity = {"id": "manual:" + manual_station, "tag": "visit", "label": "Manual visit", "source": "manual", "started_at": now, "ends_at": 0.0, "routine_step_id": "", "externally_triggered": false}
		target = manual_station
	elif paused:
		activity = {"id": "paused", "tag": "idle", "label": "Autonomous movement paused", "source": "paused", "started_at": now, "ends_at": 0.0, "routine_step_id": "", "externally_triggered": false}
		target = ""
	if target.is_empty() and activity.source != "paused":
		for station in stations:
			if activity.tag in station.activity_tags:
				target = station.id
				break
	var target_object := ""
	for station in stations:
		if station.id == target:
			target_object = station.get("object_id", "")
			if activity.source == "manual":
				activity.label = station.label
			break
	return {"activity": activity, "target_station": target, "target_object": target_object}


func observe(intent: Dictionary, observation: Dictionary) -> Dictionary:
	var next: Dictionary = intent.activity.duplicate(true)
	if next.id != current_activity.get("id", "") or next.source != current_activity.get("source", ""):
		previous_activity = current_activity.duplicate(true)
		current_activity = next
	else:
		# Manual and paused intents are sampled repeatedly; their original start remains stable.
		next.started_at = current_activity.started_at
		current_activity = next
	return {"current_activity": current_activity.duplicate(true), "previous_activity": previous_activity.duplicate(true), "target_station": intent.target_station, "target_object": intent.target_object, "phase": observation.get("phase", "idle"), "current_location": observation.get("current_location", {}).duplicate(true), "last_arrived_station": observation.get("last_arrived_station", ""), "animation": observation.get("animation", "idle"), "clock": observation.get("clock", "live")}
