extends Node3D
## Content-driven orchestrator. Authored structures and routine choices live in JSON.
const Loader = preload("res://scripts/content_loader.gd")
const Builder = preload("res://scripts/asset_builder.gd")
const Surface = preload("res://scripts/navigation_surface.gd")
const Motor = preload("res://scripts/character_motor.gd")
const Simulation = preload("res://scripts/core/simulation.gd")
const Activities = preload("res://scripts/core/activity_store.gd")
const StateStore = preload("res://scripts/core/state_store.gd")
const ResidentState = preload("res://scripts/core/resident_state.gd")
const WorldUI = preload("res://scripts/world_ui.gd")

var catalog: Array = []
var world: Dictionary = {}
var character: Dictionary = {}
var routine: Dictionary = {}
var assets: Dictionary = {}
var state: Dictionary = {}
var simulation: Dictionary = {}
var activities = Activities.new()
var store = StateStore.new()
var content_root: Node3D
var surface: Node3D
var motor: CharacterBody3D
var camera: Camera3D
var ui: CanvasLayer
var markers: Array[Node3D] = []
var object_nodes: Dictionary = {}
var station_by_id: Dictionary = {}
var behavior_hooks: Dictionary = {}
var behavior_cleanup: Callable
var resident_tracker = ResidentState.new()
var resident: Dictionary = {}
var arrived_station := ""
var last_arrived_station := ""
var navigation_failed := false
var force_navigation := false
var manual_station := ""
var current_station := ""
var preview_offset := 0.0
var ready_world := false
var switching := false
var show_markers := true
var save_status := ""
var notice := ""
var state_writable := true
var tick := 0.0
var displayed_source := "SIMULATED"
var mock_sequence := 0
var mock_ids: Dictionary = {}
var mock_tags: Dictionary = {}
var bridge_callback: JavaScriptObject
var test_mode := false
var last_event_result: Dictionary = {}

func _ready() -> void:
	register_behavior("activity_light", _activity_light)
	ui = WorldUI.new()
	add_child(ui)
	ui.command.connect(command)
	var index := Loader.read_json("res://content/catalog.json")
	if index.has("error"):
		ui.notice_label.text = index.error
		return
	catalog = index.get("worlds",[])
	ui.set_catalog(catalog)
	if OS.has_feature("web"):
		_setup_bridge()
	if not catalog.is_empty():
		var startup_id: String = catalog[0].id
		if OS.has_feature("web"):
			var hosted_id: Variant = JavaScriptBridge.eval("window.domesHostedBundle?.world?.id || null", true)
			if hosted_id is String:
				for entry in catalog:
					if entry.id == hosted_id:
						startup_id = hosted_id
		await load_world(startup_id)

func load_world(id: String) -> bool:
	if switching:
		return false
	var path := ""
	for entry in catalog:
		if entry.id == id:
			path = entry.path
	if path.is_empty():
		return false
	var data := Loader.bundle(path)
	data = Loader.hosted_bundle(data)
	return await load_bundle(data)

func load_bundle(data: Dictionary) -> bool:
	if switching:
		return false
	if data.has("error"):
		notice = data.error
		return false
	var transition_errors: Array[String] = Surface.transition_errors(data.world, data.assets, data.character)
	if not transition_errors.is_empty():
		notice = "; ".join(transition_errors)
		return false
	switching = true
	ready_world = false
	_clear_behavior()
	if is_instance_valid(content_root):
		content_root.queue_free()
		await get_tree().process_frame
	world = data.world
	character = data.character
	routine = data.routine
	assets = data.assets
	manual_station = ""
	current_station = ""
	arrived_station = ""
	last_arrived_station = ""
	navigation_failed = false
	force_navigation = false
	resident_tracker = ResidentState.new()
	resident = {}
	preview_offset = 0
	notice = ""
	mock_ids.clear()
	mock_tags.clear()
	activities = Activities.new()
	activities.configure(world.id,character.id)
	await _load_state()
	show_markers = state.get("preferences",{}).get("show_markers",true)
	content_root = Node3D.new()
	content_root.name = "WorldContent"
	add_child(content_root)
	_build_environment()
	object_nodes.clear()
	markers.clear()
	station_by_id.clear()
	for zone in world.zones:
		if not world.get("transitions", []).is_empty():
			content_root.add_child(Builder.support_box(Vector3(zone.size[0],0.26,zone.size[1]), Vector3(zone.center[0],float(zone.center[1])-0.13,zone.center[2]), zone.color))
		else:
			content_root.add_child(Builder.part({"shape":"box","size":[zone.size[0],0.26,zone.size[1]],"position":[zone.center[0],float(zone.center[1])-0.14,zone.center[2]],"color":zone.color}))
		content_root.add_child(Builder.part({"shape":"box","size":[zone.size[0]+0.1,0.25,zone.size[1]+0.1],"position":[zone.center[0],float(zone.center[1])-0.38,zone.center[2]],"color":"#253934"}))
	for transition in world.get("transitions", []):
		content_root.add_child(Builder.ramp(transition))
	for object in world.objects:
		var node := Builder.instantiate(assets[object.asset_id],object)
		content_root.add_child(node)
		object_nodes[object.id] = node
	for station in world.stations:
		station_by_id[station.id] = station
		var marker := Node3D.new()
		marker.position = Builder.vector(station.interaction)
		marker.visible = show_markers
		content_root.add_child(marker)
		marker.add_child(Builder.part({"shape":"cylinder","size":[0.45,0.018,0.45],"position":[0,0.014,0],"color":"#bad69e","emission":0.2}))
		var label := Label3D.new()
		label.text = station.label
		label.font_size = 26
		label.pixel_size = 0.008
		label.position = Vector3(0,0.12,0.1)
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.no_depth_test = true
		label.modulate = Color("f4f3dc")
		marker.add_child(label)
		markers.append(marker)
	surface = Surface.new()
	content_root.add_child(surface)
	surface.build(world,assets,float(character.navigation.radius))
	motor = Motor.new()
	motor.name = "Resident"
	content_root.add_child(motor)
	motor.configure(character)
	motor.position = Builder.vector(world.spawn)
	motor.arrived.connect(_on_arrived)
	motor.unreachable.connect(_on_unreachable)
	ui.set_world(world,show_markers,state.get("preferences",{}).get("autonomy_paused",false))
	# A frame count alone does not prove an asynchronous navigation build finished.
	# Wait for this region to own the spawn point before selecting a first station.
	var navigation_map: RID = surface.get_world_3d().navigation_map
	var navigation_deadline: int = Time.get_ticks_msec() + 5000
	var navigation_ready := false
	while Time.get_ticks_msec() < navigation_deadline:
		await get_tree().physics_frame
		await get_tree().process_frame
		# A fast headless startup can reach these callbacks before the server's
		# first map synchronization. Closest-point queries are invalid until then.
		if NavigationServer3D.map_get_iteration_id(navigation_map) == 0:
			continue
		var spawn_owner: RID = NavigationServer3D.map_get_closest_point_owner(navigation_map, motor.global_position)
		var spawn_point: Vector3 = NavigationServer3D.map_get_closest_point(navigation_map, motor.global_position)
		if spawn_owner == surface.region.get_rid() and spawn_point.distance_to(motor.global_position) <= float(world.navigation.cell_size) * 1.05:
			navigation_ready = true
			break
	if not navigation_ready:
		notice = "Navigation could not connect the spawn point. Check floor, obstacles, and spawn coordinates."
		ui.notice_label.text = notice
		switching = false
		return false
	ready_world = true
	switching = false
	_update_world()
	print("WORLD_READY ",world.id," stations=",station_by_id.size()," cells=",surface.cells.size())
	return true

func _build_environment() -> void:
	var env_node := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(world.environment.background)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(world.environment.ambient)
	env.ambient_light_energy = 0.35
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env_node.environment = env
	content_root.add_child(env_node)
	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-55,-35,0)
	light.light_color = Color(world.environment.light_color)
	light.light_energy = float(world.environment.light_energy) * 0.65
	light.shadow_enabled = true
	light.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
	content_root.add_child(light)
	camera = Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = world.camera.size
	camera.position = Builder.vector(world.camera.position)
	content_root.add_child(camera)
	camera.look_at(Builder.vector(world.camera.target))
	camera.h_offset = -3.2
	camera.current = true

func _load_state() -> void:
	var loaded: Dictionary = store.load_state(world.id)
	state_writable = true
	if loaded.get("ok",false) and loaded.get("found",false):
		state = loaded.state
		var expected_ids: Array = []
		for project in routine.projects:
			expected_ids.append(project.id)
		if state.routine_id != routine.id or state.project_ids != expected_ids or state.character_id != character.id or state.world_version != world.version:
			state_writable = false
			save_status = "Content/state mismatch. Original save preserved; migrate explicitly."
			state = store.initial_state(world,character,routine,Time.get_unix_time_from_system())
		else:
			save_status = ("Private Site" if store.hosted_enabled() else ("Recovered backup" if loaded.get("recovered",false) else "Local save")) + " · revision " + str(int(state.revision))
	elif loaded.get("ok",false):
		state = store.initial_state(world,character,routine,Time.get_unix_time_from_system())
		await _save()
		if save_status.begins_with("SAVE FAILED"):
			var concurrent: Dictionary = store.load_state(world.id)
			if concurrent.get("ok",false) and concurrent.get("found",false):
				state = concurrent.state
	else:
		state_writable = false
		state = store.initial_state(world,character,routine,Time.get_unix_time_from_system())
		save_status = "Save unreadable; original preserved. Temporary preview. " + str(loaded.get("error",""))

func _save() -> void:
	if not state_writable:
		notice = "Save protected. Export preview and repair/migrate stored state first."
		return
	var saving_world_id: String = world.id
	var submitted_preferences: Dictionary = state.preferences.duplicate(true)
	var result: Dictionary
	if store.hosted_enabled():
		save_status = "Saving to private Site…"
		result = await store.save_hosted_state(world.id,state,int(state.revision))
	else:
		result = store.save_state(world.id,state,int(state.revision))
	if world.id != saving_world_id:
		return
	if result.get("ok",false):
		var latest_preferences: Dictionary = state.preferences.duplicate(true)
		var changed_during_save := latest_preferences != submitted_preferences
		state = result.state
		if changed_during_save:
			state.preferences = latest_preferences
		save_status = ("Private Site" if store.hosted_enabled() else ("This browser" if OS.has_feature("web") else "This computer")) + " · saved revision " + str(int(state.revision))
		if changed_during_save:
			# Preserve edits made while the network request was pending and persist
			# them against the acknowledged revision, never an obsolete snapshot.
			await _save()
	else:
		save_status = "SAVE FAILED: " + str(result.get("error","unknown")) + ". Existing save preserved."

func _process(delta: float) -> void:
	if not ready_world:
		return
	tick += delta
	if tick >= 0.2:
		tick = 0
		_update_world()

func _update_world() -> void:
	var now := Time.get_unix_time_from_system()
	simulation = Simulation.evaluate(routine,float(state.routine_epoch),now+preview_offset)
	var active: Dictionary = activities.active(now)
	var paused: bool = state.get("preferences",{}).get("autonomy_paused",false)
	var intent: Dictionary = ResidentState.resolve(simulation,active,manual_station,world.stations,paused,now)
	var activity: Dictionary = intent.activity
	var next_station: String = intent.target_station
	displayed_source = {"simulated":"SIMULATED", "manual":"MANUAL VISIT", "paused":"AUTONOMY PAUSED"}.get(activity.source,str(activity.source).to_upper()+" "+str(activity.tag).to_upper())
	var detail: String = activity.label
	if not active.is_empty():
		detail += " · lease %ds" % ceili(float(active.expires_at)-now)
	if (next_station != current_station or force_navigation) and not test_mode:
		force_navigation = false
		_clear_behavior()
		current_station = next_station
		navigation_failed = false
		if not next_station.is_empty():
			arrived_station = ""
			motor.go_to(station_by_id[next_station],surface)
		else:
			motor.moving = false
			motor.path_points.clear()
			motor.set_action("idle")
	var phase := "traveling" if motor.moving else "engaged"
	if next_station.is_empty():
		phase = "paused" if paused and activity.source == "paused" else "unavailable"
	elif navigation_failed:
		phase = "unreachable"
	elif not motor.moving and arrived_station != next_station:
		phase = "idle"
	var zone_id := ""
	for zone in world.zones:
		if absf(motor.position.y-float(zone.center[1])) < 0.4 and absf(motor.position.x-float(zone.center[0])) <= float(zone.size[0])/2.0 and absf(motor.position.z-float(zone.center[2])) <= float(zone.size[1])/2.0:
			zone_id = zone.id
			break
	resident = resident_tracker.observe(intent,{"phase":phase,"current_location":{"zone_id":zone_id,"station_id":arrived_station if not motor.moving else "","position":[motor.position.x,motor.position.y,motor.position.z]},"last_arrived_station":last_arrived_station,"animation":motor.action,"clock":"simulation_preview" if activity.source == "simulated" and preview_offset != 0 else "live"})
	ui.activity_label.text = displayed_source
	ui.activity_label.modulate = Color("e8c28a") if displayed_source.begins_with("MOCK") else Color("c5dfa4")
	ui.detail_label.text = ("Walking · " if motor.moving else "At home · ") + detail
	if phase == "unavailable":
		ui.detail_label.text = "No station for " + str(activity.tag) + " · safely idle"
	ui.state_label.text = "Activity: %s\nPose: %s · %s" % [str(activity.tag).replace("_"," "),motor.action,phase]
	var project_lines := PackedStringArray()
	for project in simulation.get("projects",[]):
		project_lines.append("%s · %d%%\n%s" % [project.title,roundi(float(project.progress)*100),project.stage])
		for definition in routine.projects:
			if definition.id == project.id and object_nodes.has(definition.get("visual_object_id","")):
				var node: Node3D = object_nodes[definition.visual_object_id]
				node.get_node("Visual").scale.y = 0.2+0.8*float(project.progress)
	ui.project_label.text = "\n".join(project_lines)
	ui.save_label.text = save_status
	ui.notice_label.text = notice if not notice.is_empty() else ("Preview +%d min · never saved" % int(preview_offset/60) if preview_offset > 0 else "")
	if OS.has_feature("web"):
		JavaScriptBridge.eval("window.domesSnapshot = " + JSON.stringify(snapshot()) + ";",true)

func register_behavior(id: String, callback: Callable) -> void:
	behavior_hooks[id] = callback

func _on_arrived(station_id: String) -> void:
	arrived_station = station_id
	last_arrived_station = station_id
	navigation_failed = false
	_clear_behavior()
	var station: Dictionary = station_by_id.get(station_id,{})
	var behavior: String = station.get("behavior","")
	if behavior_hooks.has(behavior):
		var cleanup: Variant = behavior_hooks[behavior].call(motor,station,object_nodes.get(station.get("object_id","")))
		if cleanup is Callable:
			behavior_cleanup = cleanup

func _on_unreachable(station_id: String) -> void:
	_clear_behavior()
	arrived_station = ""
	navigation_failed = true
	notice = "Unreachable station: " + station_id + ". Resident is safely idle."

func _clear_behavior() -> void:
	if behavior_cleanup.is_valid():
		behavior_cleanup.call()
	behavior_cleanup = Callable()

func _activity_light(_resident: Node3D, station: Dictionary, object: Variant) -> Callable:
	# Visual occupancy feedback only; no collider, geometry or persistent content changes.
	if not is_instance_valid(object):
		return Callable()
	var light := OmniLight3D.new()
	light.name = "ActivityLight"
	light.position = Vector3(0,1.7,0)
	light.light_color = Color.from_string(str(station.get("metadata",{}).get("activity_light_color","#c8e7ef")),Color("#c8e7ef"))
	light.light_energy = 0.9
	light.omni_range = 3.0
	light.shadow_enabled = false
	object.add_child(light)
	return func():
		if is_instance_valid(light):
			light.queue_free()

func command(action: String, value: String = "") -> void:
	if switching or not ready_world:
		return
	match action:
		"world": load_world(value)
		"visit":
			if station_by_id.has(value):
				manual_station = value
				force_navigation = true
				notice = "Manual visit; no real activity started."
		"resume":
			manual_station = ""
			force_navigation = true
			notice = ""
		"advance": preview_offset += clampf(value.to_float(),0,31536000)
		"live": preview_offset = 0
		"save": _save()
		"markers":
			show_markers = value == "true"
			state.preferences["show_markers"] = show_markers
			for marker in markers:
				marker.visible = show_markers
		"pause_autonomy":
			state.preferences["autonomy_paused"] = value == "true"
			ui.autonomy_pause.set_pressed_no_signal(value == "true")
			manual_station = ""
			notice = "Autonomous movement paused; elapsed simulation continues." if value == "true" else "Autonomous movement resumed."
		"export_state": _export_json(world.id+".state.json",state)
		"export_world": _export_json(world.id+".world-pack.json",{"schema_version":1,"world":world,"character":character,"routine":routine,"assets":assets,"brief":Loader.read_json(world.brief_path)})
		"work_start","work_renew","work_end","call_start","call_renew","call_end": _mock(action)
		"activity_start": _mock("work_start",value)
	if ready_world:
		_update_world()

func _mock(action: String, activity_tag: String = "") -> void:
	var parts := action.split("_")
	var kind: String = parts[0]
	var operation: String = parts[1]
	var now := Time.get_unix_time_from_system()
	mock_sequence += 1
	var activity_id: String = str(mock_ids.get(kind,""))
	var tag: String = str(mock_tags.get(kind,""))
	if operation == "start":
		activity_id = "mock-%s-%s-%s" % [kind,Time.get_ticks_msec(),mock_sequence]
		tag = activity_tag
	if activity_id.is_empty():
		notice = "No MOCK " + kind + " has been started."
		return
	var event := {"schema_version":1,"event_id":"event-%s-%s" % [Time.get_ticks_msec(),mock_sequence],"activity_id":activity_id,"source":"mock","sequence":mock_sequence,"kind":kind,"operation":operation,"timestamp":now,"ttl_seconds":20 if kind == "call" else 45,"world_id":world.id,"character_id":character.id}
	if not tag.is_empty() and kind == "work":
		event["activity_tag"] = tag
	last_event_result = receive_mock(event)
	if last_event_result.accepted:
		mock_ids[kind] = activity_id
		mock_tags[kind] = tag
	notice = "MOCK " + action + " · " + str(last_event_result.get("reason",""))

func receive_mock(event: Dictionary) -> Dictionary:
	# Browser input cannot authorize a real reporter.
	if event.get("operation","") != "end" and event.has("activity_tag") and event.activity_tag is String:
		var supported := false
		for station in world.get("stations",[]):
			if event.activity_tag in station.activity_tags:
				supported = true
				break
		if not supported:
			last_event_result = {"accepted":false,"reason":"unknown_activity_tag"}
			return last_event_result
	last_event_result = activities.apply(event,Time.get_unix_time_from_system(),"mock")
	if last_event_result.accepted:
		mock_sequence = maxi(mock_sequence,int(event.sequence))
	return last_event_result

func snapshot() -> Dictionary:
	return {"ready":ready_world,"object_count":world.get("objects",[]).size(),"structure_revision":world.get("metadata",{}).get("structure_revision",0),"recovery_count":motor.recovery_count if is_instance_valid(motor) else 0,"transition_id":str(surface.transition_at(motor.position).get("id","")) if is_instance_valid(surface) and is_instance_valid(motor) else "","navigation_build_msec":surface.build_msec if is_instance_valid(surface) else 0,"support_height":surface.support_height(motor.position) if is_instance_valid(surface) and is_instance_valid(motor) else 0,"world_id":world.get("id",""),"character_id":character.get("id",""),"position":[motor.position.x,motor.position.y,motor.position.z] if is_instance_valid(motor) else [],"station":current_station,"moving":motor.moving if is_instance_valid(motor) else false,"action":motor.action if is_instance_valid(motor) else "","source":displayed_source,"resident":resident,"simulation":simulation,"epoch":state.get("routine_epoch",0),"revision":state.get("revision",0),"preview_offset":preview_offset,"save_status":save_status,"notice":notice,"show_markers":show_markers,"autonomy_paused":state.get("preferences",{}).get("autonomy_paused",false),"controls":ui.control_bounds() if is_instance_valid(ui) else {},"viewport_size":[get_viewport().get_visible_rect().size.x,get_viewport().get_visible_rect().size.y],"connections":{"work":"unavailable","native_call":"unavailable"},"event_result":last_event_result,"visual":motor.visual_snapshot() if is_instance_valid(motor) else {}}

func _setup_bridge() -> void:
	bridge_callback = JavaScriptBridge.create_callback(_web_command)
	var window := JavaScriptBridge.get_interface("window")
	window.domesNativeCommand = bridge_callback
	JavaScriptBridge.eval("window.domesCommand = (action, value='') => window.domesNativeCommand(JSON.stringify({action,value})); window.domesMockEvent = event => window.domesNativeCommand(JSON.stringify({action:'mock_event',value:event}));",true)

func _web_command(args: Array) -> void:
	if args.is_empty() or not args[0] is String or args[0].length() > 8192:
		return
	var data = JSON.parse_string(args[0])
	if not data is Dictionary:
		return
	if data.get("action","") == "mock_event" and data.get("value") is Dictionary:
		receive_mock(data.value)
	else:
		command(str(data.get("action","")),str(data.get("value","")))

func _export_json(filename: String, data: Dictionary) -> void:
	var content := JSON.stringify(data,"  ")
	if OS.has_feature("web"):
		JavaScriptBridge.download_buffer(content.to_utf8_buffer(),filename,"application/json")
	else:
		var path := "user://"+filename
		var file := FileAccess.open(path,FileAccess.WRITE)
		if file == null:
			notice = "Export failed: could not write " + path
			return
		file.store_string(content)
		file.flush()
		notice = "Exported: " + ProjectSettings.globalize_path(path)
