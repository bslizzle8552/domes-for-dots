extends SceneTree
## Production-scene acceptance for the bounded straight-ramp transition family.
const MainScene = preload("res://scenes/main.tscn")
const Loader = preload("res://scripts/content_loader.gd")
const States = preload("res://scripts/core/state_store.gd")
var main: Node3D
var passed := 0
var failed := 0
var samples := 0
var support_failures := 0
var ceiling_failures := 0

func _init() -> void:
	call_deferred("run")

func check(condition: bool, label: String) -> void:
	if condition:
		passed += 1
	else:
		failed += 1
		push_error("FAIL: " + label)

func fixture() -> Dictionary:
	var bundle := Loader.bundle("res://content/worlds/cedar_atelier.json")
	var world: Dictionary = bundle.world
	world.id = "ramp_acceptance"
	world.zones = [{"id":"lower","center":[0,0,0],"size":[8,8],"color":"#586d77","level_id":"ground"},{"id":"upper","center":[16,3,0],"size":[8,8],"color":"#b29f80","level_id":"deck"}]
	world.levels = [{"id":"ground","elevation":0},{"id":"deck","elevation":3}]
	world.transitions = [{"id":"access_ramp","kind":"straight_ramp","source_level":"ground","destination_level":"deck","entry":[4,0,0],"exit":[12,3,0],"width":3.0,"rise":3.0,"run":8.0,"headroom":3.0,"bidirectional":true,"interruption":"hold_supported","safe_fallbacks":[[3,0,0],[13,3,0]]}]
	world.objects = []
	world.spawn = [-2,0,0]
	world.stations = [{"id":"lower","label":"Lower station","activity_tags":["work"],"approach":[-1,0,0],"interaction":[-2,0,0],"animation":"interact","fallback_animation":"idle","behavior":"","facing":90},{"id":"upper","label":"Upper station","activity_tags":["observe"],"approach":[15,3,0],"interaction":[16,3,0],"animation":"interact","fallback_animation":"idle","behavior":"","facing":-90}]
	return bundle

func sample() -> void:
	samples += 1
	var support: float = main.surface.support_height(main.motor.global_position)
	if is_inf(support) or absf(main.motor.position.y-support) > 0.16:
		support_failures += 1
		if support_failures <= 3:
			print("SUPPORT_FAILURE ", main.motor.position, " support=",support)
	if main.motor.is_on_ceiling():
		ceiling_failures += 1

func settle() -> void:
	for frame in range(2400):
		await physics_frame
		await process_frame
		sample()
		if not main.motor.moving:
			break

func run() -> void:
	main = MainScene.instantiate()
	main.store = States.new("user://ramp-test-"+str(Time.get_ticks_usec()),"ramp-test")
	main.test_mode = true
	root.add_child(main)
	for frame in range(600):
		await physics_frame
		if main.ready_world:
			break
	check(main.ready_world,"initial runtime ready")
	var bundle := fixture()
	check(await main.load_bundle(bundle),"two-level bundle loads with production geometry/navigation")
	check(main.motor.position.y == 0.0,"safe lower spawn")
	check(main.surface.get_children().filter(func(node): return node is NavigationLink3D).size() == 1,"explicit navigation link registered")
	check(main.motor.go_to(bundle.world.stations[1],main.surface),"upward route accepted")
	await settle()
	check(not main.motor.moving and main.motor.position.distance_to(Vector3(16,3,0)) < 0.2,"physical uphill traversal arrives at upper station")
	check(main.motor.go_to(bundle.world.stations[0],main.surface),"downward route accepted")
	await settle()
	check(not main.motor.moving and main.motor.position.distance_to(Vector3(-2,0,0)) < 0.2,"physical downhill traversal arrives at lower station")
	check(main.motor.go_to(bundle.world.stations[1],main.surface),"second uphill route accepted")
	for frame in range(1200):
		await physics_frame
		await process_frame
		sample()
		if main.motor.position.y > 1.2:
			break
	check(main.motor.position.y > 1.2 and main.motor.position.y < 2.5,"interrupt occurs in middle of ramp")
	main.motor.moving = false
	main.motor.path_points.clear()
	var interrupted: Vector3 = main.motor.position
	for frame in range(60):
		await physics_frame
		await process_frame
		sample()
	check(main.motor.position.distance_to(interrupted) < 0.001,"pause holds physically supported ramp position")
	check(main.motor.go_to(bundle.world.stations[0],main.surface),"mid-ramp redirect to source accepted")
	await settle()
	check(main.motor.position.distance_to(Vector3(-2,0,0)) < 0.2,"redirect returns along ramp to safe lower landing")
	main.motor.go_to(bundle.world.stations[1],main.surface)
	for frame in range(1200):
		await physics_frame
		await process_frame
		sample()
		if main.motor.position.y > 1.2:
			break
	check(main.motor.go_to(bundle.world.stations[1],main.surface),"mid-ramp redirect toward destination accepted")
	await settle()
	check(main.motor.position.distance_to(Vector3(16,3,0)) < 0.2,"redirect reaches upper landing")
	main.state.preferences["autonomy_paused"] = true
	main._save()
	var epoch: float = main.state.routine_epoch
	check(await main.load_bundle(bundle),"reload around transition loads safely")
	check(main.motor.position.distance_to(Vector3(-2,0,0)) < 0.001,"reload uses declared safe spawn rather than stale midair position")
	check(main.state.preferences.autonomy_paused and main.state.routine_epoch == epoch,"reload preserves durable preference and routine epoch")
	var rejected := bundle.duplicate(true)
	rejected.world.transitions[0].width = float(rejected.character.collision.radius)
	check(not await main.load_bundle(rejected) and "width" in main.notice,"runtime rejects incompatible transition width")
	rejected = bundle.duplicate(true)
	rejected.world.transitions[0].headroom = float(rejected.character.collision.height)-0.1
	check(not await main.load_bundle(rejected) and "headroom" in main.notice,"runtime rejects insufficient headroom")
	rejected = bundle.duplicate(true)
	rejected.world.transitions[0].kind = "teleporter"
	check(not await main.load_bundle(rejected),"runtime rejects unsupported transition family")
	rejected = bundle.duplicate(true)
	rejected.assets["obstruction"] = {"collision":{"enabled":true,"size":[1,2,1],"offset":[0,1,0]},"footprint":[1,1]}
	rejected.world.objects = [{"id":"blocked_landing","asset_id":"obstruction","position":[13,3,0]}]
	check(not await main.load_bundle(rejected) and "blocks ramp" in main.notice,"runtime rejects blocked landing before activation")
	check(main.ready_world and main.world.id == "ramp_acceptance" and main.motor.position.distance_to(Vector3(-2,0,0)) < 0.001,"failed candidate preserves known-good active world")
	check(main.motor.recovery_count == 0,"normal traversal never requires recovery teleport")
	main.motor.go_to(bundle.world.stations[1],main.surface)
	main.motor.position = Vector3(8,-4,0)
	await physics_frame
	await process_frame
	check(main.motor.recovery_count == 1 and not main.motor.moving,"lost support triggers safe recovery and reports unreachable")
	check(main.motor.position.distance_to(Vector3(3,0,0)) < 0.01,"recovery uses fully supported interior landing")
	for degrees in [90,180,270]:
		var rotated := fixture()
		rotated.world.id = "ramp_rotated_"+str(degrees)
		for zone in rotated.world.zones:
			zone.center = turn(zone.center,degrees)
		rotated.world.spawn = turn(rotated.world.spawn,degrees)
		for station in rotated.world.stations:
			station.approach = turn(station.approach,degrees)
			station.interaction = turn(station.interaction,degrees)
		for transition in rotated.world.transitions:
			transition.entry = turn(transition.entry,degrees)
			transition.exit = turn(transition.exit,degrees)
			transition.safe_fallbacks = [turn(transition.safe_fallbacks[0],degrees),turn(transition.safe_fallbacks[1],degrees)]
		check(await main.load_bundle(rotated),"rotated ramp loads "+str(degrees))
		main.motor.go_to(rotated.world.stations[1],main.surface)
		await settle()
		check(main.motor.position.distance_to(Vector3(rotated.world.stations[1].interaction[0],3,rotated.world.stations[1].interaction[2])) < 0.2,"rotated ramp climbs "+str(degrees))
		main.motor.go_to(rotated.world.stations[0],main.surface)
		await settle()
		check(main.motor.position.distance_to(Vector3(rotated.world.spawn[0],0,rotated.world.spawn[2])) < 0.2,"rotated ramp descends "+str(degrees))
	check(support_failures == 0,"all sampled traversal positions have continuous support")
	check(ceiling_failures == 0,"all sampled traversals avoid head collisions")
	check(samples > 1000,"physical acceptance samples both levels and transitions")
	print("MULTILEVEL TESTS: ",passed," passed, ",failed," failed; ",samples," support/headroom samples; support_failures=",support_failures)
	main.queue_free()
	await process_frame
	quit(0 if failed == 0 else 1)

func turn(values: Array, degrees: int) -> Array:
	var point := Vector3(values[0],values[1],values[2]).rotated(Vector3.UP,deg_to_rad(degrees))
	return [snappedf(point.x,0.001),point.y,snappedf(point.z,0.001)]
