extends Node3D
## Layered floor rasterization with explicit, bidirectional physical ramp links.
const Builder = preload("res://scripts/asset_builder.gd")
var region: NavigationRegion3D
var obstacles: Array[Rect2] = []
var cells: Dictionary = {}
var cell_size := 0.5
var radius := 0.3
var transitions: Array = []
var zones: Array = []
var build_msec := 0

static func transition_errors(world: Dictionary, assets: Dictionary, character: Dictionary) -> Array[String]:
	var errors: Array[String] = []
	var body_radius := maxf(maxf(float(character.collision.radius), float(character.navigation.radius)),float(world.navigation.character_radius))
	var body_height := float(character.collision.height)
	var levels: Dictionary = {}
	for level in world.get("levels", []):
		levels[level.id] = float(level.elevation)
	for transition in world.get("transitions", []):
		var label := "Transition " + str(transition.get("id", "unknown")) + ": "
		if transition.get("kind", "") != "straight_ramp":
			errors.append(label+"unsupported transition family")
			continue
		var entry := Builder.vector(transition.entry)
		var exit := Builder.vector(transition.exit)
		var horizontal := Vector3(exit.x-entry.x, 0, exit.z-entry.z)
		var run := horizontal.length()
		if run < 0.1 or (absf(horizontal.x) > 0.001 and absf(horizontal.z) > 0.001):
			errors.append(label+"requires a nonzero cardinal straight run")
			continue
		if not levels.has(transition.source_level) or not levels.has(transition.destination_level):
			errors.append(label+"source and destination levels must exist")
			continue
		if absf(entry.y-levels[transition.source_level]) > 0.001 or absf(exit.y-levels[transition.destination_level]) > 0.001:
			errors.append(label+"anchors disagree with declared level elevations")
		if absf(run-float(transition.run)) > 0.001 or absf(absf(exit.y-entry.y)-float(transition.rise)) > 0.001:
			errors.append(label+"rise/run disagree with anchors")
		if absf(exit.y-entry.y)/run > 0.45:
			errors.append(label+"slope exceeds supported 0.45 rise/run")
		if float(transition.width) < 2.0*body_radius+0.5:
			errors.append(label+"width cannot clear character radius and safety margin")
		if float(transition.headroom) < body_height+0.2:
			errors.append(label+"headroom cannot clear character height and safety margin")
		if transition.get("interruption", "") != "hold_supported" or not transition.get("bidirectional", true):
			errors.append(label+"requires supported pause and bidirectional traversal")
		var inset := maxf(1.0, body_radius+float(world.navigation.cell_size))
		var landings := [entry-horizontal.normalized()*inset, exit+horizontal.normalized()*inset]
		if transition.get("safe_fallbacks", []).size() != 2:
			errors.append(label+"requires two explicit safe landing fallbacks")
			continue
		landings = [Builder.vector(transition.safe_fallbacks[0]),Builder.vector(transition.safe_fallbacks[1])]
		for landing_index in range(2):
			var landing: Vector3 = landings[landing_index]
			var endpoint := entry if landing_index == 0 else exit
			var away := -horizontal.normalized() if landing_index == 0 else horizontal.normalized()
			var projected: float = (landing-endpoint).dot(away)
			if projected < inset-0.001 or (landing-endpoint-away*projected).length() > 0.001:
				errors.append(label+"safe fallback must continue ramp centerline into its level landing")
			var supported := false
			for zone in world.zones:
				if absf(float(zone.center[1])-landing.y) < 0.001 and absf(landing.x-float(zone.center[0]))+body_radius < float(zone.size[0])/2.0 and absf(landing.z-float(zone.center[2]))+body_radius < float(zone.size[1])/2.0:
					supported = true
			if not supported:
				errors.append(label+"landing lacks complete body-envelope support")
		# Sample the entire swept body envelope, including both landing approaches.
		var start: Vector3 = landings[0]
		var finish: Vector3 = landings[1]
		var count := ceili(start.distance_to(finish)/0.1)
		for index in range(count+1):
			var point := start.lerp(finish, float(index)/count)
			var fraction := clampf(Vector3(point.x-entry.x,0,point.z-entry.z).dot(horizontal)/horizontal.length_squared(),0,1)
			point.y = lerpf(entry.y,exit.y,fraction)
			for zone in world.zones:
				var slab_bottom := float(zone.center[1])-0.26
				if slab_bottom > point.y+0.1 and slab_bottom < point.y+body_height+0.2 and absf(point.x-float(zone.center[0])) < float(zone.size[0])/2.0+body_radius and absf(point.z-float(zone.center[2])) < float(zone.size[1])/2.0+body_radius:
					errors.append(label+"overhead support slab obstructs body clearance")
					return errors
			for object in world.objects:
				var asset: Dictionary = assets[object.asset_id]
				var footprint := Builder.obstacle(asset, object)
				if not footprint.has_area() or not footprint.grow(body_radius+0.1).has_point(Vector2(point.x,point.z)):
					continue
				var scale_y := float(asset.get("scale",[1,1,1])[1])*float(object.get("scale",[1,1,1])[1])
				var half_height := float(asset.collision.size[1])*scale_y*0.5
				var center_y := float(object.position[1])+float(asset.collision.get("offset",[0,0,0])[1])*scale_y
				if center_y+half_height > point.y+0.03 and center_y-half_height < point.y+body_height+0.2:
					errors.append(label+"object "+str(object.id)+" blocks ramp or landing clearance")
					return errors
	return errors

func build(world: Dictionary, assets: Dictionary, character_radius: float) -> void:
	var started := Time.get_ticks_msec()
	cell_size = float(world.navigation.cell_size)
	radius = maxf(float(world.navigation.character_radius), character_radius)
	transitions = world.get("transitions", [])
	zones = world.zones
	obstacles.clear()
	cells.clear()
	var layers: Dictionary = {}
	for zone in zones:
		var elevation := float(zone.center[1])
		if not layers.has(elevation):
			layers[elevation] = []
		var size_v := Vector2(zone.size[0], zone.size[1])
		layers[elevation].append(Rect2(Vector2(zone.center[0], zone.center[2]) - size_v * 0.5, size_v))
	var mesh := NavigationMesh.new()
	var vertices := PackedVector3Array()
	var indices: Dictionary = {}
	var polygons: Array[PackedInt32Array] = []
	for elevation in layers:
		var floor_zones: Array = layers[elevation]
		var bounds: Rect2 = floor_zones[0]
		for floor_zone in floor_zones:
			bounds = bounds.merge(floor_zone)
		var layer_obstacles: Array[Rect2] = []
		for object in world.objects:
			var asset: Dictionary = assets[object.asset_id]
			var rect: Rect2 = Builder.obstacle(asset, object)
			var object_y := float(object.position[1])
			var height := float(asset.get("collision", {}).get("size", [0,0,0])[1]) * float(asset.get("scale", [1,1,1])[1]) * float(object.get("scale", [1,1,1])[1])
			if rect.has_area() and object_y <= float(elevation) + 0.1 and object_y + height > float(elevation):
				layer_obstacles.append(rect.grow(radius + 0.04))
				obstacles.append(rect.grow(radius + 0.04))
		for x in range(floori(bounds.position.x / cell_size), ceili(bounds.end.x / cell_size)):
			for z in range(floori(bounds.position.y / cell_size), ceili(bounds.end.y / cell_size)):
				var rect := Rect2(Vector2(x, z) * cell_size, Vector2.ONE * cell_size)
				var inside := true
				for offset in [Vector2(-1,-1), Vector2(-1,1), Vector2(1,-1), Vector2(1,1)]:
					var sample: Vector2 = rect.get_center() + offset * (cell_size * 0.5 + radius * 0.8)
					var covered := false
					for floor_zone in floor_zones:
						if floor_zone.has_point(sample):
							covered = true
							break
					if not covered:
						inside = false
						break
				if not inside:
					continue
				var blocked := false
				for obstacle in layer_obstacles:
					if obstacle.intersects(rect):
						blocked = true
						break
				if blocked:
					continue
				cells[Vector3(x, elevation, z)] = true
				var polygon := PackedInt32Array()
				for corner in [Vector2i(x,z), Vector2i(x,z+1), Vector2i(x+1,z+1), Vector2i(x+1,z)]:
					var key := Vector3(corner.x, elevation, corner.y)
					if not indices.has(key):
						indices[key] = vertices.size()
						vertices.append(Vector3(corner.x * cell_size, elevation, corner.y * cell_size))
					polygon.append(indices[key])
				polygons.append(polygon)
	mesh.vertices = vertices
	for polygon in polygons:
		mesh.add_polygon(polygon)
	region = NavigationRegion3D.new()
	region.navigation_mesh = mesh
	region.use_edge_connections = false
	add_child(region)
	for transition in transitions:
		var anchors := landing_anchors(transition)
		var link := NavigationLink3D.new()
		link.name = "Transition_" + str(transition.id)
		link.start_position = anchors[0]
		link.end_position = anchors[1]
		link.bidirectional = transition.get("bidirectional", true)
		add_child(link)
	build_msec = Time.get_ticks_msec() - started

func landing_anchors(transition: Dictionary) -> Array[Vector3]:
	if transition.get("safe_fallbacks", []).size() == 2:
		return [Builder.vector(transition.safe_fallbacks[0]),Builder.vector(transition.safe_fallbacks[1])]
	var entry := Builder.vector(transition.entry)
	var exit := Builder.vector(transition.exit)
	var direction := Vector3(exit.x-entry.x, 0, exit.z-entry.z).normalized()
	var inset := maxf(1.0, radius + cell_size)
	return [entry-direction*inset, exit+direction*inset]

func transition_at(point: Vector3) -> Dictionary:
	for transition in transitions:
		var entry := Builder.vector(transition.entry)
		var exit := Builder.vector(transition.exit)
		var horizontal := Vector3(exit.x-entry.x, 0, exit.z-entry.z)
		var fraction := Vector3(point.x-entry.x, 0, point.z-entry.z).dot(horizontal) / horizontal.length_squared()
		if fraction < 0.0 or fraction > 1.0:
			continue
		var center := entry.lerp(exit, fraction)
		if Vector2(point.x-center.x, point.z-center.z).length() <= float(transition.width)/2.0 and absf(point.y-center.y) < 0.4:
			return transition
	return {}

func support_height(point: Vector3) -> float:
	var transition := transition_at(point)
	if not transition.is_empty():
		var entry := Builder.vector(transition.entry)
		var exit := Builder.vector(transition.exit)
		var horizontal := Vector3(exit.x-entry.x, 0, exit.z-entry.z)
		var fraction := Vector3(point.x-entry.x, 0, point.z-entry.z).dot(horizontal) / horizontal.length_squared()
		return lerpf(entry.y, exit.y, fraction)
	var closest := INF
	var result := INF
	for zone in zones:
		if absf(point.x-float(zone.center[0])) <= float(zone.size[0])/2.0 and absf(point.z-float(zone.center[2])) <= float(zone.size[1])/2.0:
			var height := float(zone.center[1])
			if absf(height-point.y) < closest:
				closest = absf(height-point.y)
				result = height
	return result

func safe_fallback(point: Vector3) -> Vector3:
	# Landings are eroded into the supporting floors, never a bare ramp edge.
	var best := Vector3.ZERO
	var distance := INF
	for transition in transitions:
		for landing in landing_anchors(transition):
			if point.distance_to(landing) < distance:
				distance = point.distance_to(landing)
				best = landing
	return best

func _floor_path(from: Vector3, to: Vector3) -> PackedVector3Array:
	var map := get_world_3d().navigation_map
	if not is_instance_valid(region) or NavigationServer3D.map_get_iteration_id(map) == 0:
		return PackedVector3Array()
	var closest := NavigationServer3D.map_get_closest_point(map, to)
	if closest.distance_to(to) > cell_size * 1.05:
		return PackedVector3Array()
	var result := NavigationServer3D.map_get_path(map, from, closest, true)
	if result.is_empty() or result[-1].distance_to(closest) > 0.15:
		return PackedVector3Array()
	return result

func path(from: Vector3, to: Vector3) -> PackedVector3Array:
	var active := transition_at(from)
	if active.is_empty():
		return _floor_path(from, to)
	# Finish along the supported ramp before taking any redirected floor route.
	var best := PackedVector3Array()
	var best_length := INF
	for anchor in landing_anchors(active):
		var continuation := _floor_path(anchor, to)
		if continuation.is_empty():
			continue
		var route := PackedVector3Array([from, anchor])
		route.append_array(continuation)
		var length := 0.0
		for index in range(1, route.size()):
			length += route[index-1].distance_to(route[index])
		if length < best_length:
			best = route
			best_length = length
	return best
