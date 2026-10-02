extends SceneTree
## Uses the production scene, NavigationServer3D map, CharacterBody3D and collisions.
## --fixed-fps 60 makes deterministic physics ticks run without wall-clock pacing.

const MainScene: PackedScene = preload("res://scenes/main.tscn")
const States = preload("res://scripts/core/state_store.gd")
const Motor = preload("res://scripts/character_motor.gd")
const Builder = preload("res://scripts/asset_builder.gd")

var _main: Node3D
var _passed: int = 0
var _failed: int = 0
var _arrivals: Array[String] = []
var _unreachable: Array[String] = []
var _state_root: String
var _physical_checks: int = 0


func _init() -> void:
	call_deferred("_run")


func _check(condition: bool, label: String) -> void:
	if condition:
		_passed += 1
	else:
		_failed += 1
		push_error("FAIL: " + label)


func _run() -> void:
	_state_root = "user://runtime-test-" + str(Time.get_ticks_usec())
	_main = MainScene.instantiate()
	_main.store = States.new(_state_root, "runtime-test-" + str(Time.get_ticks_usec()))
	_main.test_mode = true
	root.add_child(_main)
	var ready_deadline: int = Time.get_ticks_msec() + 6000
	while Time.get_ticks_msec() < ready_deadline:
		await physics_frame
		if _main.ready_world:
			break
	_check(_main.ready_world, "production main scene reaches ready state")
	if not _main.ready_world:
		_finish()
		return
	_check(_main.catalog.size() >= 2, "catalog exposes at least two independent world definitions")
	for entry in _main.catalog:
		if _main.world.id != entry.id:
			var loaded: bool = await _main.load_world(entry.id)
			_check(loaded and _main.ready_world, "world loads through shared production runtime: " + entry.id)
		await _test_world()
	await _test_replacement()
	_finish()


func _test_world() -> void:
	var world_id: String = _main.world.id
	var nav_map: RID = _main.surface.get_world_3d().navigation_map
	_check(NavigationServer3D.map_get_iteration_id(nav_map) > 0, "Godot navigation map synchronized: " + world_id)
	_check(_main.motor is CharacterBody3D, "production resident owns physical character body: " + world_id)
	_check(_main.state.revision >= 1 and _main.state.world_id == world_id, "runtime initializes isolated revisioned state: " + world_id)
	var stations: Array = _main.world.stations
	var connected: bool = true
	var missing: Array[String] = []
	for origin in stations:
		for destination in stations:
			var approach_path: PackedVector3Array = _main.surface.path(Builder.vector(origin.interaction), Builder.vector(destination.approach))
			var interaction_path: PackedVector3Array = _main.surface.path(Builder.vector(destination.approach), Builder.vector(destination.interaction))
			if approach_path.is_empty() or interaction_path.is_empty():
				connected = false
				missing.append(str(origin.id) + " -> " + str(destination.id))
	_check(connected, "all station pairs reachable through Godot navigation: " + world_id + " " + ", ".join(missing))
	_connect_motor()
	for station in stations:
		await _visit(station, world_id)
	# Return to the first station so the final leg also uses a previously visited anchor.
	if stations.size() > 1:
		await _visit(stations[0], world_id + " return")
	var impossible: Dictionary = {"id": "unreachable-fixture", "approach": [10000, 0, 10000], "interaction": [10001, 0, 10000], "animation": "interact", "fallback_animation": "idle"}
	var position_before: Vector3 = _main.motor.global_position
	var accepted: bool = _main.motor.go_to(impossible, _main.surface)
	await physics_frame
	_check(not accepted and _unreachable.has("unreachable-fixture"), "unreachable destination signals failure: " + world_id)
	_check(not _main.motor.moving and _main.motor.action == "idle" and _main.motor.global_position.distance_to(position_before) < 0.001, "unreachable destination leaves resident safely idle: " + world_id)
	_check(_main.snapshot().connections == {"work": "unavailable", "native_call": "unavailable"}, "runtime does not claim real integration: " + world_id)
	print("RUNTIME_WORLD_TESTED ", world_id, " station_pairs=", stations.size() * stations.size(), " stations_walked=", stations.size() + 1)


func _connect_motor() -> void:
	_arrivals.clear()
	_unreachable.clear()
	_main.motor.arrived.connect(func(id: String): _arrivals.append(id))
	_main.motor.unreachable.connect(func(id: String): _unreachable.append(id))


func _visit(station: Dictionary, context: String) -> void:
	_arrivals.clear()
	_unreachable.clear()
	var accepted: bool = _main.motor.go_to(station, _main.surface)
	_check(accepted, "production go_to accepts " + context + "/" + str(station.id))
	if not accepted:
		return
	var clear: bool = true
	var violation: String = ""
	for frame in range(2400):
		await physics_frame
		# process_frame follows the physics update; sample the resulting body position.
		await process_frame
		var obstacle: String = _intersecting_obstacle()
		if not obstacle.is_empty():
			clear = false
			violation = obstacle
		if not _main.motor.moving:
			break
	_check(not _main.motor.moving and _arrivals.has(station.id) and _unreachable.is_empty(), "physical movement arrives without stall: " + context + "/" + str(station.id))
	var distance: float = _main.motor.global_position.distance_to(Builder.vector(station.interaction))
	_check(distance <= 0.6, "arrived position within 0.6 m anchor: " + context + "/" + str(station.id) + " distance=" + str(distance))
	_check(clear, "resident never penetrates expanded physical prop: " + context + "/" + str(station.id) + " " + violation)
	_check(is_zero_approx(_main.motor.global_position.y), "planar resident remains on floor: " + context + "/" + str(station.id))


func _intersecting_obstacle() -> String:
	var position: Vector3 = _main.motor.global_position
	var radius: float = _main.motor.definition.collision.radius
	var height: float = _main.motor.definition.collision.height
	for object_id in _main.object_nodes:
		var object_node: Node3D = _main.object_nodes[object_id]
		for shape_node in object_node.find_children("*", "CollisionShape3D", true, false):
			if not shape_node.shape is BoxShape3D:
				continue
			_physical_checks += 1
			var center: Vector3 = shape_node.global_position
			var basis: Basis = shape_node.global_basis
			var size: Vector3 = shape_node.shape.size
			var half_y: float = size.y * basis.y.length() * 0.5
			if center.y - half_y >= height or center.y + half_y <= 0.0:
				continue
			var relative: Vector3 = position - center
			var dx: float = maxf(0.0, absf(relative.dot(basis.x.normalized())) - size.x * basis.x.length() * 0.5)
			var dz: float = maxf(0.0, absf(relative.dot(basis.z.normalized())) - size.z * basis.z.length() * 0.5)
			if Vector2(dx, dz).length() < radius - 0.015:
				return str(object_id)
	return ""


func _test_replacement() -> void:
	var definition: Dictionary = _main.character.duplicate(true)
	definition["id"] = "replacement-fixture"
	definition["scene_path"] = "res://tests/fixtures/replacement.tscn"
	definition["forward_axis"] = "+X"
	definition["scale"] = [0.9, 1.1, 0.9]
	definition["rig"]["animation_player_path"] = "ClipPlayer"
	definition["animations"] = {"idle": "stand", "walk": "stride", "interact": "gesture"}
	definition["fallbacks"]["phone"] = "interact"
	var position: Vector3 = _main.motor.global_position
	_main.motor.queue_free()
	await process_frame
	var replacement = Motor.new()
	_main.content_root.add_child(replacement)
	replacement.configure(definition)
	replacement.global_position = position
	_main.motor = replacement
	_connect_motor()
	_check(replacement.visual.name == "ReplacementFixture" and replacement.visual.has_node("DistinctBoxVisual"), "replacement scene loads without engine edits")
	_check(replacement.visual.scale.is_equal_approx(Vector3(0.9, 1.1, 0.9)) and is_equal_approx(replacement.visual.rotation.y, PI / 2.0), "replacement scale and forward axis honored")
	_check(is_instance_valid(replacement.animation_player), "replacement resolves declared AnimationPlayer")
	_check(replacement.action == "idle" and replacement.animation_player.current_animation == "stand", "replacement initializes its idle clip immediately")
	replacement.set_action("phone")
	_check(replacement.action == "interact" and replacement.animation_player.current_animation == "gesture", "unsupported phone semantic uses declared interaction fallback clip")
	replacement.animation_player.advance(0.25)
	_check(replacement.visual.get_node("DistinctBoxVisual").rotation.y > 0.05, "replacement animation clip actually transforms visual geometry")
	definition["animations"]["missing_clip_semantic"] = "clip-does-not-exist"
	definition["fallbacks"]["missing_clip_semantic"] = "interact"
	replacement.set_action("missing_clip_semantic")
	_check(replacement.action == "interact", "declared absent clip follows semantic fallback")
	definition["fallbacks"]["cycle_a"] = "cycle_b"
	definition["fallbacks"]["cycle_b"] = "cycle_a"
	replacement.set_action("cycle_a", "idle")
	_check(replacement.action == "idle", "cyclic fallback safely resolves station fallback")
	var target: Dictionary = _main.world.stations[-1].duplicate(true)
	target["animation"] = "unsupported-custom-pose"
	target["fallback_animation"] = "idle"
	await _visit(target, "replacement-character")
	_check(replacement.action == "idle" and replacement.animation_player.current_animation == "stand", "arrival honors the station fallback animation")
	replacement.set_action("walk")
	_check(replacement.animation_player.current_animation == "stride", "replacement walk semantic resolves custom clip name")
	_check(_physical_checks > 100, "movement checked against actual physical collider transforms across frames")


func _finish() -> void:
	var world_ids: Array[String] = []
	if is_instance_valid(_main):
		for entry in _main.catalog:
			world_ids.append(entry.id)
		_main.queue_free()
	for world_id in world_ids:
		for suffix in [".json", ".json.bak", ".json.tmp", ".json.bak.tmp"]:
			var path: String = _state_root.path_join(world_id + suffix)
			if FileAccess.file_exists(path):
				DirAccess.remove_absolute(path)
	DirAccess.remove_absolute(_state_root)
	print("RUNTIME TESTS: %d passed, %d failed; %d physical obstacle samples" % [_passed, _failed, _physical_checks])
	quit(0 if _failed == 0 else 1)
