extends SceneTree

const Simulation = preload("res://scripts/core/simulation.gd")
const Activities = preload("res://scripts/core/activity_store.gd")
const States = preload("res://scripts/core/state_store.gd")
const Resident = preload("res://scripts/core/resident_state.gd")

var _passed: int = 0
var _failed: int = 0


func _init() -> void:
	_test_simulation()
	_test_activity()
	_test_resident()
	_test_persistence()
	print("CORE TESTS: %d passed, %d failed" % [_passed, _failed])
	quit(0 if _failed == 0 else 1)


func _check(condition: bool, label: String) -> void:
	if condition:
		_passed += 1
	else:
		_failed += 1
		push_error("FAIL: " + label)


func _routine() -> Dictionary:
	return {"id": "routine", "cycle_seconds": 100.0, "steps": [{"id": "read", "activity_tag": "reading", "duration_seconds": 40.0}, {"id": "craft", "activity_tag": "craft", "duration_seconds": 60.0}], "projects": [{"id": "book", "title": "Read a book", "activity_tag": "reading", "required_seconds": 120.0, "stages": ["Unread", "Reading", "Read"]}, {"id": "sculpture", "title": "Sculpture", "activity_tag": "craft", "required_seconds": 1000.0, "stages": ["Idea", "Shaping", "Complete"]}]}


func _test_simulation() -> void:
	var routine: Dictionary = _routine()
	var before: String = JSON.stringify(routine)
	var first: Dictionary = Simulation.evaluate(routine, 1000.0, 1040.0)
	_check(first["step"]["id"] == "craft", "exact step boundary")
	_check(first.step_started_at == 1040.0 and first.step_ends_at == 1100.0 and first.cycle_index == 0, "simulation supplies exact activity boundaries")
	_check(is_equal_approx(first["projects"][0]["progress"], 1.0 / 3.0), "partial cycle integrates only completed reading")
	_check(first["projects"][1]["progress"] == 0.0, "next step not prematurely counted")
	var complete_cycle: Dictionary = Simulation.evaluate(routine, 1000.0, 1100.0)
	_check(complete_cycle["step"]["id"] == "read", "cycle boundary wraps")
	_check(complete_cycle.step_started_at == 1100.0 and complete_cycle.cycle_index == 1, "new cycle has distinct scheduled activity start")
	var later: Dictionary = Simulation.evaluate(routine, 1000.0, 1250.0)
	_check(later["projects"][0]["progress"] == 1.0, "finite project clamps at completion")
	_check(is_equal_approx(later["projects"][1]["progress"], 0.13), "whole cycles plus remainder integrated")
	_check(later == Simulation.evaluate(routine, 1000.0, 1250.0), "multiple viewers cannot multiply progress")
	_check(JSON.stringify(routine) == before, "simulation never mutates routine")
	var distant: Dictionary = Simulation.evaluate(routine, 1000.0, 1000000001000.0)
	_check(distant["projects"][1]["progress"] == 1.0, "long absence calculated and finite")
	_check(distant["projects"][1]["stage"] == "Complete", "completed stage remains last")
	_check(Simulation.evaluate(routine, 1000.0, 999.0)["elapsed"] == 0.0, "clock before epoch does not reverse progress")
	var bad: Dictionary = routine.duplicate(true)
	bad["cycle_seconds"] = 99.0
	_check(Simulation.evaluate(bad, 1000.0, 1100.0).has("error"), "inconsistent routine rejected")
	_check(Simulation.evaluate(routine, NAN, 1000.0).has("error"), "nonfinite clock rejected")
	var oracle_agrees: bool = true
	for elapsed in [0, 1, 39, 40, 41, 99, 100, 101, 159, 160, 161, 249, 250, 299, 300, 999]:
		var read_seconds: int = 0
		var craft_seconds: int = 0
		for tick in range(elapsed):
			if tick % 100 < 40:
				read_seconds += 1
			else:
				craft_seconds += 1
		var actual: Dictionary = Simulation.evaluate(routine, 1000.0, 1000.0 + elapsed)
		oracle_agrees = oracle_agrees and is_equal_approx(actual["projects"][0]["progress"], minf(1.0, read_seconds / 120.0))
		oracle_agrees = oracle_agrees and is_equal_approx(actual["projects"][1]["progress"], minf(1.0, craft_seconds / 1000.0))
	_check(oracle_agrees, "analytical integration matches independent second-by-second oracle across 16 boundaries")


func _event(event_id: String, activity_id: String, sequence: int, kind: String, operation: String, timestamp: float, ttl: float = 30.0) -> Dictionary:
	return {"schema_version": 1, "event_id": event_id, "activity_id": activity_id, "source": "mock", "sequence": sequence, "kind": kind, "operation": operation, "timestamp": timestamp, "ttl_seconds": ttl, "world_id": "test-world", "character_id": "test-dot"}


func _test_activity() -> void:
	var store = Activities.new()
	store.configure("test-world", "test-dot")
	var work: Dictionary = _event("w1", "work-a", 1, "work", "start", 1000.0, 60.0)
	_check(store.apply(work, 1000.0)["accepted"], "mock start accepted")
	_check(store.apply(work, 1001.0)["reason"] == "duplicate", "event duplicates idempotent")
	var collision: Dictionary = work.duplicate(true)
	collision["ttl_seconds"] = 10.0
	_check(store.apply(collision, 1001.0)["reason"] == "event_id_collision", "event ID reuse with changed payload rejected")
	_check(store.apply(_event("c1", "call-a", 1, "call", "start", 1002.0), 1002.0)["accepted"], "call starts beside work")
	_check(store.active(1003.0)["kind"] == "call", "call visually preempts work")
	_check(store.apply(_event("c2", "call-a", 2, "call", "end", 1004.0, 0.0), 1004.0)["accepted"], "call end accepted")
	_check(store.active(1004.0)["kind"] == "work", "call ending resumes valid work")
	_check(not store.apply(_event("c3", "call-a", 3, "call", "start", 1005.0), 1005.0)["accepted"], "ended activity cannot resurrect with newer sequence")
	_check(store.active(1060.0).is_empty(), "missed END expires at exact deadline")
	_check(not store.apply(_event("w2", "work-a", 2, "work", "renew", 1060.0), 1060.0)["accepted"], "expired lease cannot renew")
	_check(store.apply(work, 1061.0)["reason"] == "duplicate" and store.active(1061.0).is_empty(), "duplicate does not resurrect expired activity")
	_check(not store.apply(_event("w3", "work-b", 0, "work", "start", 1061.0), 1061.0)["accepted"], "stream high-water rejects older sequence")
	_check(store.apply(_event("w4", "work-b", 5, "work", "start", 1061.0), 1061.0)["accepted"], "new sequence starts new activity")
	_check(store.apply(_event("w5", "work-b", 6, "work", "renew", 1080.0), 1080.0)["accepted"], "live renewal extends lease")
	_check(store.active(1100.0)["expires_at"] == 1110.0, "expiry based on source timestamp")
	_check(not store.apply(_event("w6", "work-c", 7, "work", "start", 1106.0), 1100.0)["accepted"], "future clock skew bounded")
	_check(not store.apply(_event("w7", "work-c", 7, "work", "start", 1050.0), 1100.0)["accepted"], "out-of-order timestamp rejected")
	_check(not store.apply(_event("w8", "work-c", 7, "work", "start", 1100.0, 61.0), 1100.0)["accepted"], "TTL bounded")
	var forged: Dictionary = _event("fake", "other", 8, "work", "start", 1100.0)
	forged["source"] = "native-chatgpt"
	_check(store.apply(forged, 1100.0)["reason"] == "untrusted_source", "public mock path cannot claim real adapter")
	forged["source"] = "mock"
	forged["world_id"] = "another-world"
	_check(store.apply(forged, 1100.0)["reason"] == "wrong_target", "wrong world rejected")
	var unknown_end: Dictionary = _event("ce", "never-started", 10, "call", "end", 1100.0, 0.0)
	_check(store.apply(unknown_end, 1100.0)["accepted"], "end before start creates tombstone")
	_check(not store.apply(_event("cs", "never-started", 11, "call", "start", 1101.0), 1101.0)["accepted"], "delayed start after end cannot resurrect")
	_check(not store.apply(_event("old", "old", 12, "call", "start", 1100.0, 10.0), 1111.0)["accepted"], "already expired delayed start rejected")
	_check(not store.apply(_event("renew", "missing", 13, "call", "renew", 1111.0), 1111.0)["accepted"], "renew without start rejected")
	store.configure("test-world", "test-dot")
	_check(store.active(1000.0).is_empty(), "reconfiguration clears session lease state")
	store.apply(_event("sa", "superseded", 1, "work", "start", 1000.0), 1000.0)
	store.apply(_event("sb", "replacement", 2, "work", "start", 1001.0), 1001.0)
	_check(store.active(1002.0)["activity_id"] == "replacement", "newer start supersedes old activity")
	_check(not store.apply(_event("sc", "superseded", 3, "work", "renew", 1002.0), 1002.0)["accepted"], "superseded activity cannot renew with newer sequence")
	store.apply(_event("sd", "unrelated", 4, "work", "end", 1003.0, 0.0), 1003.0)
	_check(store.active(1004.0)["activity_id"] == "replacement", "unrelated END does not cancel current activity")
	var malformed: Dictionary = _event("bad-schema", "new", 5, "call", "start", 1004.0)
	malformed["schema_version"] = 2
	_check(not store.apply(malformed, 1004.0)["accepted"], "unknown event schema rejected")
	malformed["schema_version"] = 1
	malformed["sequence"] = 5.5
	_check(not store.apply(malformed, 1004.0)["accepted"], "fractional event sequence rejected")
	malformed["sequence"] = 5
	malformed["timestamp"] = NAN
	_check(not store.apply(malformed, 1004.0)["accepted"], "nonfinite event timestamp rejected")
	store.configure("test-world", "test-dot")
	var custom := _event("custom", "gardening", 1, "work", "start", 1000.0)
	custom["activity_tag"] = "garden"
	_check(store.apply(custom, 1000.0).accepted and store.active(1001.0).activity_tag == "garden", "custom activity reuses bounded work lease")
	var renewal := _event("custom-renew", "gardening", 2, "work", "renew", 1005.0)
	renewal["activity_tag"] = "garden"
	_check(store.apply(renewal, 1005.0).accepted and store.active(1006.0).started_at == 1000.0, "renewal retains actual lease lifecycle start")
	renewal = _event("custom-changed", "gardening", 3, "work", "renew", 1006.0)
	renewal["activity_tag"] = "read"
	_check(store.apply(renewal, 1006.0).reason == "activity_tag_changed", "renewal cannot silently change custom activity")
	var call := _event("custom-call", "call", 1, "call", "start", 1007.0)
	call["activity_tag"] = "garden"
	_check(store.apply(call, 1007.0).reason == "invalid_activity_tag", "call semantic cannot be overridden by custom tag")
	call.erase("activity_tag")
	store.apply(call, 1007.0)
	_check(store.active(1008.0).kind == "call", "call priority remains above custom work activity")
	store.apply(_event("custom-call-end", "call", 2, "call", "end", 1009.0, 0.0), 1009.0)
	_check(store.active(1010.0).activity_tag == "garden", "custom activity resumes after call ends")
	_check(store.active(1035.0).is_empty(), "custom activity expires at renewed source deadline")
	custom = _event("bad-tag", "other", 4, "work", "start", 1040.0)
	custom["activity_tag"] = "../../bad"
	_check(store.apply(custom, 1040.0).reason == "invalid_activity_tag", "invalid custom activity identifier rejected")


func _test_resident() -> void:
	var stations := [{"id":"one","object_id":"desk_a","label":"Desk A","activity_tags":["reading"]},{"id":"two","object_id":"desk_b","label":"Desk B","activity_tags":["reading"]},{"id":"phone","object_id":"comms","label":"Comms","activity_tags":["call"]}]
	var simulation: Dictionary = Simulation.evaluate(_routine(),1000.0,1001.0)
	var intent: Dictionary = Resident.resolve(simulation,{},"",stations,false,1001.0)
	_check(intent.target_station == "one" and intent.activity.source == "simulated", "routine preserves first matching station default")
	simulation.step["station_id"] = "two"
	intent = Resident.resolve(simulation,{},"",stations,false,1001.0)
	_check(intent.target_station == "two" and intent.target_object == "desk_b", "routine explicitly selects preferred station")
	var tracker = Resident.new()
	var observed: Dictionary = tracker.observe(intent,{"phase":"traveling","current_location":{"zone_id":"room","station_id":""},"animation":"walk"})
	_check(observed.current_activity.tag == "reading" and observed.animation == "walk" and observed.current_location.station_id == "", "activity remains reading while walking toward unreadied station")
	observed = tracker.observe(intent,{"phase":"engaged","current_location":{"zone_id":"room","station_id":"two"},"animation":"interact"})
	_check(observed.phase == "engaged" and observed.previous_activity.is_empty() and observed.current_activity.started_at == 1000.0, "arrival changes phase without replacing activity identity")
	var call := {"kind":"call","source":"mock","activity_id":"call-a","timestamp":1002.0,"started_at":1002.0,"expires_at":1032.0}
	intent = Resident.resolve(simulation,call,"two",stations,true,1002.0)
	observed = tracker.observe(intent,{"phase":"traveling","animation":"walk"})
	_check(intent.target_station == "phone" and observed.previous_activity.tag == "reading" and observed.current_activity.externally_triggered, "mock call preempts routine/manual/pause and retains previous activity")
	intent = Resident.resolve(simulation,{},"two",stations,true,1003.0)
	observed = tracker.observe(intent,{"phase":"traveling"})
	_check(observed.current_activity.source == "manual" and intent.target_station == "two", "manual visit can run while autonomy is paused")
	intent = Resident.resolve(simulation,{},"two",stations,true,1005.0)
	observed = tracker.observe(intent,{"phase":"engaged"})
	_check(observed.current_activity.started_at == 1003.0, "manual start remains stable over repeated observations")
	intent = Resident.resolve(simulation,{},"",stations,true,1006.0)
	observed = tracker.observe(intent,{"phase":"paused"})
	_check(observed.current_activity.source == "paused" and observed.target_station.is_empty(), "paused autonomy has no navigation target")
	intent = Resident.resolve(simulation,{},"",stations,false,1007.0)
	observed = tracker.observe(intent,{"phase":"traveling"})
	_check(observed.current_activity.source == "simulated" and observed.previous_activity.source == "paused", "resume restores simulated routine without fabricating external activity")
	observed.current_activity["tag"] = "mutated"
	_check(tracker.current_activity.tag == "reading", "snapshot cannot mutate resident history")
	var unknown := {"kind":"work","activity_tag":"unknown","source":"mock","activity_id":"unknown","timestamp":1010.0,"expires_at":1040.0}
	intent = Resident.resolve(simulation,unknown,"",stations,false,1010.0)
	_check(intent.target_station.is_empty(), "unmapped activity does not silently display unrelated work")


func _write(path: String, contents: String) -> void:
	var file: FileAccess = FileAccess.open(path, FileAccess.WRITE)
	file.store_string(contents)
	file.close()


func _test_persistence() -> void:
	var directory: String = "user://core-test-" + str(Time.get_ticks_usec())
	var store = States.new(directory, "core-test-" + str(Time.get_ticks_usec()))
	var state: Dictionary = store.initial_state({"id": "test-world", "version": "1.0.0"}, {"id": "test-dot"}, _routine(), 1000.0)
	var absent: Dictionary = store.load_state("test-world")
	_check(absent["ok"] and not absent["found"], "missing state is explicitly absent")
	_check(store.validate_state(state, "test-world").is_empty(), "initial state is valid")
	var first: Dictionary = store.save_state("test-world", state, 0)
	_check(first["ok"] and first["state"]["revision"] == 1, "initial write establishes revision one")
	var loaded: Dictionary = store.load_state("test-world")
	_check(loaded["ok"] and loaded["state"] == first["state"], "native save loads identical state")
	_check(not store.save_state("test-world", state, 0)["ok"], "stale viewer cannot overwrite newer revision")
	state = loaded["state"]
	state["preferences"] = {"quiet": true, "nested": {"value": 4}}
	var second: Dictionary = store.save_state("test-world", state, 1)
	_check(second["ok"] and second["state"]["revision"] == 2, "valid revision increments")
	var invalid: Dictionary = second["state"].duplicate(true)
	invalid["routine_epoch"] = "yesterday"
	_check(not store.save_state("test-world", invalid, 2)["ok"], "invalid imported epoch rejected before writes")
	invalid = second["state"].duplicate(true)
	invalid["project_ids"] = ["same", "same"]
	_check(not store.save_state("test-world", invalid, 2)["ok"], "duplicate project identities rejected")
	invalid = second["state"].duplicate(true)
	invalid["preferences"] = {"invalid": INF}
	_check(not store.save_state("test-world", invalid, 2)["ok"], "nonfinite imported preference rejected")
	_check(not store.load_state("../escape")["ok"], "world ID cannot escape state directory")
	_check(store.load_state("test-world")["state"] == second["state"], "failed saves retain good state")
	for variation in [{"schema_version": 2}, {"revision": 2.5}, {"routine_epoch": -1.0}, {"world_id": "wrong-world"}, {"preferences": []}]:
		invalid = second["state"].duplicate(true)
		invalid.merge(variation, true)
		_check(not store.save_state("test-world", invalid, 2)["ok"], "strict import rejects " + str(variation.keys()[0]))
	invalid = second["state"].duplicate(true)
	invalid["unknown"] = "field"
	_check(not store.save_state("test-world", invalid, 2)["ok"], "unknown state fields rejected")
	invalid = second["state"].duplicate(true)
	invalid["preferences"] = {"oversized": "x".repeat(262145)}
	_check(not store.save_state("test-world", invalid, 2)["ok"], "oversized state rejected before writes")
	var path: String = directory.path_join("test-world.json")
	DirAccess.make_dir_absolute(path + ".tmp")
	_check(not store.save_state("test-world", second["state"], 2)["ok"], "temporary write failure reported")
	_check(store.load_state("test-world")["state"] == second["state"], "temporary write failure preserves primary")
	DirAccess.remove_absolute(path + ".tmp")
	var backup: Variant = JSON.parse_string(FileAccess.get_file_as_string(path + ".bak"))
	_check(backup["revision"] == 1, "backup retains previous good revision")
	DirAccess.make_dir_absolute(path + ".lock")
	_check(not store.save_state("test-world", second["state"], 2)["ok"], "native lock prevents concurrent writer")
	DirAccess.remove_absolute(path + ".lock")
	_write(path, "{broken")
	var recovered: Dictionary = store.load_state("test-world")
	_check(recovered["ok"] and recovered["recovered"] and recovered["state"]["revision"] == 1 and not recovered["error"].is_empty(), "corrupt primary loads backup with visible recovery warning")
	var repaired: Dictionary = store.save_state("test-world", recovered["state"], 1)
	_check(repaired["ok"] and store.load_state("test-world")["state"]["revision"] == 2, "save after recovery repairs primary")
	_write(path, "{broken")
	_write(path + ".bak", "also broken")
	_check(not store.load_state("test-world")["ok"], "two corrupt copies fail without silent reset")
	_check(not store.save_state("test-world", state, 1)["ok"], "save refuses to replace unknown corrupt state")
	for suffix in ["", ".bak", ".tmp", ".bak.tmp"]:
		if FileAccess.file_exists(path + suffix):
			DirAccess.remove_absolute(path + suffix)
	DirAccess.remove_absolute(directory)
