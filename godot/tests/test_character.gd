extends SceneTree
## Real scene audit, animated joint transforms and shared physical motor routes.
const Audit = preload("res://scripts/character_audit.gd")
const Motor = preload("res://scripts/character_motor.gd")
const Surface = preload("res://scripts/navigation_surface.gd")
const Loader = preload("res://scripts/content_loader.gd")
const Builder = preload("res://scripts/asset_builder.gd")
var passed := 0
var failed := 0


func _init() -> void:
	call_deferred("_run")


func check(condition: bool, label: String) -> void:
	if condition:
		passed += 1
	else:
		failed += 1
		push_error("FAIL: " + label)


func _run() -> void:
	var nova := Loader.read_json("res://content/characters/nova.json")
	var moss := Loader.read_json("res://content/characters/moss.json")
	var report := Audit.inspect(nova, root)
	check(report.ok and report.rig_kind == "joint_animation", "production Nova scene passes actual joint/clip audit")
	check(report.mesh_count >= 15 and report.animation_players[0].clips.size() == 6, "original articulated geometry and six authored clips are loaded")
	check(report.skeletons.is_empty(), "joint rig does not pretend to be skinned or retargeted")
	check(report.semantic_actions.rest.clip == "recharge" and report.semantic_actions.sit.resolved == "idle", "rest is implemented and seating is explicitly idle fallback")
	check(Audit.inspect(moss, root).ok, "original procedural resident remains compatible")
	var bad := nova.duplicate(true)
	bad.rig.animation_player_path = "AbsentPlayer"
	check(not Audit.inspect(bad, root).ok, "audit rejects an absent declared AnimationPlayer")
	bad = nova.duplicate(true)
	bad.rig.skeleton_path = "Torso"
	check(not Audit.inspect(bad, root).ok, "audit rejects a non-skeleton declared as Skeleton3D")
	bad = nova.duplicate(true)
	bad.animations.work = "absent_clip"
	bad.fallbacks.work = "interact"
	var missing_clip := Audit.inspect(bad, root)
	check(not missing_clip.ok and missing_clip.semantic_actions.work.resolved == "interact", "audit fails an absent declared clip even when runtime has a valid fallback")
	bad = nova.duplicate(true)
	bad.fallbacks.cycle_a = "cycle_b"
	bad.fallbacks.cycle_b = "cycle_a"
	check(not Audit.inspect(bad, root).ok, "audit rejects cyclic fallback declarations")
	var motor = Motor.new()
	root.add_child(motor)
	motor.configure(nova)
	check(motor.action == "idle" and motor.animation_player.current_animation == "standby", "same motor starts the production robot idle clip")
	var head: Node3D = motor.visual.get_node("Torso/Head")
	var left: Node3D = motor.visual.get_node("Torso/LeftArm")
	var right: Node3D = motor.visual.get_node("Torso/RightArm")
	motor.animation_player.advance(0.75)
	check(head.rotation.y > 0.03, "idle actually turns the head")
	motor.set_action("walk")
	motor.animation_player.advance(0.2)
	check(motor.visual.get_node("LeftLeg").rotation.x > 0.2 and motor.visual.get_node("RightLeg").rotation.x < -0.2, "walk actually articulates opposing legs")
	check(left.rotation.x < -0.3 and right.rotation.x > 0.3, "walk swings opposing arms")
	motor.set_action("interact")
	motor.animation_player.advance(0.4)
	check(right.rotation.x > 1.0 and left.rotation.x < 0.4, "interaction is an asymmetric forward reach")
	motor.set_action("work")
	motor.animation_player.advance(0.2)
	check(left.rotation.x > 1.4 and right.rotation.x < 1.3, "work alternates both arms instead of reusing interaction")
	motor.set_action("rest")
	motor.animation_player.advance(1.0)
	check(head.rotation.x > 0.3 and left.rotation.z < -0.4 and right.rotation.z > 0.4, "rest visibly folds the arms and lowers the head")
	motor.set_action("phone")
	motor.animation_player.advance(0.2)
	check(right.rotation.z < -2.7 and absf(left.rotation.z) < 0.001, "phone raises one empty hand and resets the other arm")
	motor.set_action("sit")
	motor.animation_player.advance(0.0)
	check(motor.action == "idle" and right.rotation.is_zero_approx(), "unsupported seated pose returns to standing idle without residual phone pose")
	for semantic in ["idle", "walk", "interact", "work", "rest", "phone"]:
		motor.set_action(semantic)
		var clip: Animation = motor.animation_player.get_animation(motor.animation_player.current_animation)
		var grounded := true
		for sample in range(17):
			motor.animation_player.seek(float(sample)*clip.length/16.0, true)
			if _minimum_mesh_y(motor.visual) < -0.01:
				grounded = false
		check(grounded, "pose mesh remains above the floor throughout clip: " + semantic)
	motor.queue_free()
	await process_frame
	await _test_world_motion(nova)
	print("CHARACTER TESTS: %d passed, %d failed" % [passed,failed])
	quit(0 if failed == 0 else 1)


func _minimum_mesh_y(visual: Node3D) -> float:
	var low := INF
	for mesh_node in visual.find_children("*", "MeshInstance3D", true, false):
		var bounds: AABB = mesh_node.get_aabb()
		for corner in range(8):
			var point: Vector3 = bounds.position + bounds.size*Vector3(corner&1,(corner>>1)&1,(corner>>2)&1)
			low = minf(low, (mesh_node.global_transform*point).y)
	return low


func _test_world_motion(definition: Dictionary) -> void:
	var bundle := Loader.bundle("res://content/worlds/tidal_observatory.json")
	var environment := Node3D.new()
	root.add_child(environment)
	for object in bundle.world.objects:
		environment.add_child(Builder.instantiate(bundle.assets[object.asset_id], object))
	var surface = Surface.new()
	environment.add_child(surface)
	surface.build(bundle.world,bundle.assets,definition.collision.radius)
	var motor = Motor.new()
	environment.add_child(motor)
	motor.configure(definition)
	motor.global_position = Builder.vector(bundle.world.spawn)
	var deadline := Time.get_ticks_msec()+5000
	while Time.get_ticks_msec() < deadline and surface.path(motor.global_position, motor.global_position).is_empty():
		await physics_frame
	check(not surface.path(motor.global_position,motor.global_position).is_empty(), "production navigation is synchronized for character acceptance")
	var arrivals: Array[String] = []
	motor.arrived.connect(func(id: String): arrivals.append(id))
	for station in bundle.world.stations:
		arrivals.clear()
		var accepted: bool = motor.go_to(station, surface)
		check(accepted, "shared motor accepts production station: " + station.id)
		if not accepted:
			continue
		for frame in range(2000):
			await physics_frame
			if not motor.moving:
				break
		check(arrivals.has(station.id) and motor.global_position.distance_to(Builder.vector(station.interaction)) < 0.6, "articulated body physically arrives: " + station.id)
		check(motor.animation_player.current_animation == definition.animations.get(motor.action, ""), "arrival plays the resolved production clip: " + station.id)
	environment.queue_free()
	await process_frame
