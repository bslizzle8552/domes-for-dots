extends RefCounted
## Loads trusted project scenes to inspect actual runtime resources. This is not
## a sandbox and does not establish retargeting, prop grip or visual acceptance.

static func inspect(definition: Dictionary, parent: Node) -> Dictionary:
	var report := {
		"character_id":definition.get("id",""), "scene_path":definition.get("scene_path",""),
		"ok":false, "errors":[], "warnings":[], "nodes":[], "animation_players":[],
		"skeletons":[], "semantic_actions":{}, "mesh_count":0,
		"validation_scope":"Loaded scene, declared nodes, actual clips and fallback graph. Visual/station compatibility still requires acceptance."
	}
	if not ResourceLoader.exists(report.scene_path):
		report.errors.append("scene resource does not exist")
		return report
	var resource = load(report.scene_path)
	if not resource is PackedScene:
		report.errors.append("scene resource is not a PackedScene")
		return report
	var visual = resource.instantiate()
	if not visual is Node3D:
		report.errors.append("scene root must be Node3D")
		visual.free()
		return report
	if visual.has_method("configure"):
		visual.configure(definition)
	var scale_values: Array = definition.get("scale",[1,1,1])
	visual.scale = Vector3(scale_values[0],scale_values[1],scale_values[2])
	parent.add_child(visual)
	_inventory(visual, visual, report)
	report["neutral_visual_bounds"] = _visual_bounds(visual)
	var rig: Dictionary = definition.get("rig", {})
	var player_path: String = rig.get("animation_player_path", "")
	var player: AnimationPlayer
	if not player_path.is_empty():
		player = visual.get_node_or_null(player_path) as AnimationPlayer
		if not is_instance_valid(player):
			report.errors.append("declared animation_player_path does not resolve to AnimationPlayer: " + player_path)
	var skeleton_path: String = rig.get("skeleton_path", "")
	if not skeleton_path.is_empty() and not visual.get_node_or_null(skeleton_path) is Skeleton3D:
		report.errors.append("declared skeleton_path does not resolve to Skeleton3D: " + skeleton_path)
	var procedural := PackedStringArray()
	if visual.has_method("set_action") and visual.has_method("get_supported_actions"):
		procedural = PackedStringArray(visual.get_supported_actions())
	elif visual.has_method("set_action") and not is_instance_valid(player):
		report.errors.append("procedural scene must expose get_supported_actions() for verifiable semantic support")
	var available: Dictionary = {}
	var animations: Dictionary = definition.get("animations", {})
	for semantic in animations:
		var clip: String = animations[semantic]
		if is_instance_valid(player):
			if player.has_animation(clip):
				available[semantic] = {"clip":clip,"provider":"AnimationPlayer"}
			else:
				report.errors.append("declared animation clip is absent: " + semantic + " -> " + clip)
		elif procedural.has(semantic):
			available[semantic] = {"clip":semantic,"provider":"procedural"}
		else:
			report.errors.append("declared semantic has no verified implementation: " + semantic)
	var semantics: Array = animations.keys()
	var fallbacks: Dictionary = definition.get("fallbacks", {})
	for semantic in fallbacks:
		if not semantics.has(semantic):
			semantics.append(semantic)
	for semantic in semantics:
		var resolved := resolve_action(semantic, available, fallbacks)
		report.semantic_actions[semantic] = resolved
		if not resolved.get("supported", false):
			report.errors.append("semantic cannot resolve to an implemented action: " + semantic)
	for required in ["idle", "walk", "interact"]:
		if not report.semantic_actions.get(required,{}).get("supported",false):
			report.errors.append("required semantic is unavailable: " + required)
	if report.skeletons.is_empty():
		report.warnings.append("No Skeleton3D: this scene does not demonstrate skinning or skeleton retargeting.")
	if not is_instance_valid(player):
		report.warnings.append("Procedural actions were checked against the scene's explicit capability list; no imported animation clips are present.")
	var bounds: Dictionary = report.neutral_visual_bounds
	if not bounds.is_empty() and bounds.maximum[1] > float(definition.get("collision",{}).get("height",0)) + 0.05:
		report.warnings.append("Neutral visual extends above the declared collision height; verify the intended collision envelope with actual props.")
	report["rig_kind"] = "skeleton" if not report.skeletons.is_empty() else ("joint_animation" if is_instance_valid(player) else "procedural")
	report["declared_collision"] = definition.get("collision", {})
	report["visual_scale"] = definition.get("scale", [1,1,1])
	report.ok = report.errors.is_empty()
	visual.free()
	return report


static func resolve_action(semantic: String, available: Dictionary, fallbacks: Dictionary) -> Dictionary:
	var chosen := semantic
	var visited: Array[String] = []
	while not chosen.is_empty() and not visited.has(chosen):
		visited.append(chosen)
		if available.has(chosen):
			return {"supported":true,"resolved":chosen,"clip":available[chosen].clip,"provider":available[chosen].provider,"fallback":chosen != semantic,"chain":visited}
		chosen = fallbacks.get(chosen, "")
	return {"supported":false,"resolved":"","fallback":false,"chain":visited}


static func _inventory(node: Node, visual: Node3D, report: Dictionary) -> void:
	var path := str(visual.get_path_to(node))
	report.nodes.append({"path":path,"type":node.get_class()})
	if node is MeshInstance3D:
		report.mesh_count += 1
	if node is Skeleton3D:
		var bones: Array[String] = []
		for index in range(node.get_bone_count()):
			bones.append(node.get_bone_name(index))
		report.skeletons.append({"path":path,"bones":bones})
	if node is AnimationPlayer:
		var clips: Array = []
		for clip in node.get_animation_list():
			var animation: Animation = node.get_animation(clip)
			var tracks: Array = []
			for index in range(animation.get_track_count()):
				var track_path := str(animation.track_get_path(index))
				tracks.append({"path":track_path,"keys":animation.track_get_key_count(index)})
				var root: Node = node.get_node_or_null(node.root_node)
				var track_node: NodePath = NodePath(track_path.split(":")[0])
				if root == null or (not track_node.is_empty() and root.get_node_or_null(track_node) == null):
					report.errors.append("animation track node does not resolve: " + path + "/" + clip + " -> " + track_path)
			clips.append({"name":clip,"length_seconds":animation.length,"tracks":tracks})
		report.animation_players.append({"path":path,"clips":clips})
	for child in node.get_children():
		_inventory(child, visual, report)


static func _visual_bounds(visual: Node3D) -> Dictionary:
	var low := Vector3(INF,INF,INF)
	var high := Vector3(-INF,-INF,-INF)
	var nodes: Array[Node] = visual.find_children("*","MeshInstance3D",true,false)
	if visual is MeshInstance3D:
		nodes.append(visual)
	for mesh_node in nodes:
		if mesh_node.mesh == null:
			continue
		var bounds: AABB = mesh_node.get_aabb()
		for corner in range(8):
			var point: Vector3 = bounds.position + bounds.size*Vector3(corner&1,(corner>>1)&1,(corner>>2)&1)
			# Scene is inspected at the world origin; declared visual scale applies.
			point = mesh_node.global_transform*point
			low = low.min(point)
			high = high.max(point)
	if not low.is_finite():
		return {}
	return {"minimum":[low.x,low.y,low.z],"maximum":[high.x,high.y,high.z],"size":[high.x-low.x,high.y-low.y,high.z-low.z],"scope":"Neutral mesh AABBs including declared scale; not animated or skinned envelope proof."}
