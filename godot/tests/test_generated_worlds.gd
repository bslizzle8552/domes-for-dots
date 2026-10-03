extends SceneTree
## Run against an isolated compiled world's staged project, never source catalog edits.
const MainScene = preload("res://scenes/main.tscn")
const States = preload("res://scripts/core/state_store.gd")
const Builder = preload("res://scripts/asset_builder.gd")
var main: Node3D
var passed := 0
var failed := 0
var samples := 0
var prop_samples := 0
var report: Array = []

func _init() -> void:
	call_deferred("run")

func check(condition: bool, label: String) -> void:
	if condition:
		passed += 1
	else:
		failed += 1
		push_error("FAIL: " + label)

func run() -> void:
	main = MainScene.instantiate()
	main.test_mode = true
	main.store = States.new("user://world-creator-test-"+str(Time.get_ticks_usec()),"world-creator-test")
	root.add_child(main)
	var deadline := Time.get_ticks_msec()+6000
	while Time.get_ticks_msec() < deadline:
		await physics_frame
		if main.ready_world:
			break
	check(main.ready_world,"compiled runtime loads")
	if not main.ready_world:
		finish()
		return
	for entry in main.catalog:
		if main.world.id != entry.id:
			check(await main.load_world(entry.id),"compiled world loads "+entry.id)
		var beginning := Time.get_ticks_msec()
		var pairs := 0
		var reachable := true
		for origin in main.world.stations:
			for destination in main.world.stations:
				pairs += 1
				if main.surface.path(Builder.vector(origin.interaction),Builder.vector(destination.approach)).is_empty():
					reachable = false
		check(reachable,"all station pairs reachable "+entry.id)
		for station in main.world.stations:
			check(main.motor.go_to(station,main.surface),"accepts station "+entry.id+"/"+station.id)
			var supported := true
			var clear_head := true
			var clear_props := true
			for frame in range(3600):
				await physics_frame
				await process_frame
				samples += 1
				var support: float = main.surface.support_height(main.motor.position)
				if is_inf(support) or absf(main.motor.position.y-support) > 0.16:
					supported = false
				if main.motor.is_on_ceiling():
					clear_head = false
				if not clear_of_props():
					clear_props = false
				if not main.motor.moving:
					break
			check(not main.motor.moving and main.motor.position.distance_to(Builder.vector(station.interaction)) < 0.6,"physical arrival "+entry.id+"/"+station.id)
			check(supported and clear_head,"continuous floor and head clearance "+entry.id+"/"+station.id)
			check(clear_props,"no physical prop penetration "+entry.id+"/"+station.id)
			check(main.motor.action == main.motor._resolve_action(station.animation) or main.motor.action == main.motor._resolve_action(station.fallback_animation),"supported semantic action "+entry.id+"/"+station.id)
		report.append({"world_id":entry.id,"station_pairs":pairs,"station_count":main.world.stations.size(),"navigation_build_msec":main.surface.build_msec,"acceptance_msec":Time.get_ticks_msec()-beginning})
	finish()

func finish() -> void:
	print("GENERATED_WORLD_EVIDENCE ",JSON.stringify({"worlds":report,"passed":passed,"failed":failed,"physical_samples":samples,"prop_samples":prop_samples}))
	print("GENERATED WORLD TESTS: ",passed," passed, ",failed," failed; ",samples," physical samples")
	quit(0 if failed == 0 else 1)

func clear_of_props() -> bool:
	var position: Vector3 = main.motor.global_position
	var body_radius := float(main.motor.definition.collision.radius)
	var body_height := float(main.motor.definition.collision.height)
	for object_node in main.object_nodes.values():
		for shape_node in object_node.find_children("*","CollisionShape3D",true,false):
			if not shape_node.shape is BoxShape3D:
				continue
			prop_samples += 1
			var center: Vector3 = shape_node.global_position
			var basis: Basis = shape_node.global_basis
			var size: Vector3 = shape_node.shape.size
			var half_y := size.y*basis.y.length()*0.5
			if center.y-half_y >= position.y+body_height or center.y+half_y <= position.y+0.01:
				continue
			var relative := position-center
			var dx := maxf(0.0,absf(relative.dot(basis.x.normalized()))-size.x*basis.x.length()*0.5)
			var dz := maxf(0.0,absf(relative.dot(basis.z.normalized()))-size.z*basis.z.length()*0.5)
			if Vector2(dx,dz).length() < body_radius-0.015:
				return false
	return true
