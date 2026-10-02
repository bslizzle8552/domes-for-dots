extends CharacterBody3D
signal arrived(station_id: String)
signal unreachable(station_id: String)

var definition: Dictionary
var visual: Node3D
var path_points := PackedVector3Array()
var target_station: Dictionary = {}
var animation_player: AnimationPlayer
var visual_skeleton: Skeleton3D
var action := ""
var moving := false
var speed := 2.4
var stalled := 0.0
var previous_position := Vector3.ZERO
var facing_offset := 0.0
var layered := false
var navigation_surface: Node3D
var recovery_count := 0

func configure(data: Dictionary) -> void:
	definition = data
	speed = data.navigation.speed
	var capsule := CapsuleShape3D.new()
	capsule.radius = data.collision.radius
	capsule.height = data.collision.height
	var collision := CollisionShape3D.new()
	collision.shape = capsule
	collision.position.y = capsule.height * 0.5
	add_child(collision)
	var resource = load(data.scene_path)
	if resource is PackedScene:
		visual = resource.instantiate()
	else:
		visual = preload("res://scenes/characters/placeholder.tscn").instantiate()
	if visual.has_method("configure"):
		visual.configure(data)
	visual.scale = preload("res://scripts/asset_builder.gd").vector(data.scale)
	var offsets := {"-Z":0.0,"+Z":180.0,"+X":90.0,"-X":-90.0}
	facing_offset = deg_to_rad(offsets.get(data.forward_axis, 0.0))
	visual.rotation.y = facing_offset
	add_child(visual)
	var player_path: String = data.rig.get("animation_player_path", "")
	if not player_path.is_empty():
		animation_player = visual.get_node_or_null(player_path) as AnimationPlayer
	var skeleton_path: String = data.rig.get("skeleton_path", "")
	if not skeleton_path.is_empty():
		visual_skeleton = visual.get_node_or_null(skeleton_path) as Skeleton3D
	set_action("idle")

func visual_snapshot() -> Dictionary:
	# Read-only acceptance evidence: actual running clip and bone poses, separate
	# from the requested semantic. Works with any manifest's declared rig paths.
	var result := {"scene_path":definition.get("scene_path", ""), "clip":"", "playing":false, "position_seconds":0.0, "bone_count":0, "bone_rotations":[]}
	if is_instance_valid(animation_player):
		result.clip = str(animation_player.current_animation)
		result.playing = animation_player.is_playing()
		result.position_seconds = animation_player.current_animation_position
	if is_instance_valid(visual_skeleton):
		result.bone_count = visual_skeleton.get_bone_count()
		for index in range(visual_skeleton.get_bone_count()):
			var rotation := visual_skeleton.get_bone_pose_rotation(index)
			result.bone_rotations.append([rotation.x, rotation.y, rotation.z, rotation.w])
	return result

func _resolve_action(semantic: String) -> String:
	var visited: Dictionary = {}
	var chosen := semantic
	while not chosen.is_empty() and not visited.has(chosen):
		visited[chosen] = true
		if definition.get("animations",{}).has(chosen):
			if not is_instance_valid(animation_player) or animation_player.has_animation(definition.animations[chosen]):
				return chosen
		chosen = definition.get("fallbacks",{}).get(chosen,"")
	return ""

func set_action(semantic: String, station_fallback: String = "interact") -> void:
	var chosen := _resolve_action(semantic)
	if chosen.is_empty():
		chosen = _resolve_action(station_fallback)
	if chosen.is_empty():
		chosen = "idle"
	if action == chosen and is_instance_valid(visual):
		return
	action = chosen
	if visual.has_method("set_action"):
		visual.set_action(chosen)
	if is_instance_valid(animation_player):
		var clip: String = definition.get("animations", {}).get(chosen, "")
		if animation_player.has_animation(clip):
			animation_player.play(clip)
		else:
			var fallback: String = definition.get("animations", {}).get("idle", "")
			if animation_player.has_animation(fallback):
				animation_player.play(fallback)

func go_to(station: Dictionary, surface: Node3D) -> bool:
	navigation_surface = surface
	layered = not surface.transitions.is_empty()
	floor_snap_length = 0.4
	floor_max_angle = deg_to_rad(35.0)
	floor_constant_speed = true
	target_station = station
	var approach := preload("res://scripts/asset_builder.gd").vector(station.approach)
	var interaction := preload("res://scripts/asset_builder.gd").vector(station.interaction)
	var first: PackedVector3Array = surface.path(global_position, approach)
	var second: PackedVector3Array = surface.path(approach, interaction)
	if first.is_empty() or second.is_empty():
		moving = false
		path_points.clear()
		set_action("idle")
		unreachable.emit(station.id)
		return false
	path_points = first
	path_points.append_array(second)
	stalled = 0.0
	previous_position = global_position
	moving = true
	set_action("walk")
	return true

func _physics_process(delta: float) -> void:
	if not moving:
		velocity = Vector3.ZERO
		return
	while not path_points.is_empty() and Vector2(global_position.x,global_position.z).distance_to(Vector2(path_points[0].x,path_points[0].z)) < 0.09 and (not layered or absf(global_position.y-path_points[0].y) < 0.4):
		path_points.remove_at(0)
	if path_points.is_empty():
		moving = false
		velocity = Vector3.ZERO
		rotation.y = deg_to_rad(float(target_station.get("facing",0)))
		set_action(target_station.get("animation",""),target_station.get("fallback_animation","interact"))
		arrived.emit(target_station.id)
		return
	var offset := path_points[0] - global_position
	offset.y = 0
	var direction := offset.normalized()
	rotation.y = lerp_angle(rotation.y, atan2(-direction.x,-direction.z), minf(1,delta*10))
	var vertical := velocity.y - 9.8*delta if layered else 0.0
	velocity = direction * minf(speed, offset.length() / delta)
	velocity.y = vertical
	move_and_slide()
	if not layered:
		global_position.y = path_points[0].y
	else:
		var support: float = navigation_surface.support_height(global_position)
		if not is_finite(support) or absf(global_position.y-support) > 0.4:
			global_position = navigation_surface.safe_fallback(global_position)
			velocity = Vector3.ZERO
			moving = false
			path_points.clear()
			recovery_count += 1
			set_action("idle")
			unreachable.emit(target_station.id)
			return
	if global_position.distance_to(previous_position) < 0.005:
		stalled += delta
	else:
		stalled = 0.0
	previous_position = global_position
	if stalled > 2.0:
		moving = false
		path_points.clear()
		set_action("idle")
		unreachable.emit(target_station.id)
