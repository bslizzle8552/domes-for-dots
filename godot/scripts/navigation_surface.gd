extends Node3D
## Planar, conservatively rasterized floor union -> Godot NavigationMesh polygons.
## Uses Godot's NavigationServer3D path queries, plus actual CharacterBody3D collisions.

var region: NavigationRegion3D
var obstacles: Array[Rect2] = []
var cells: Dictionary = {}
var cell_size := 0.5
var radius := 0.3

func build(world: Dictionary, assets: Dictionary, character_radius: float) -> void:
	cell_size = float(world.navigation.cell_size)
	radius = maxf(float(world.navigation.character_radius), character_radius)
	obstacles.clear()
	cells.clear()
	var zones: Array[Rect2] = []
	var bounds := Rect2()
	for zone in world.zones:
		var size_v := Vector2(zone.size[0], zone.size[1])
		var rect := Rect2(Vector2(zone.center[0], zone.center[2]) - size_v * 0.5, size_v)
		zones.append(rect)
		bounds = rect if zones.size() == 1 else bounds.merge(rect)
	for object in world.objects:
		var rect: Rect2 = preload("res://scripts/asset_builder.gd").obstacle(assets[object.asset_id], object)
		if rect.has_area():
			obstacles.append(rect.grow(radius + 0.04))
	var mesh := NavigationMesh.new()
	var vertices := PackedVector3Array()
	var indices: Dictionary = {}
	var polygons: Array[PackedInt32Array] = []
	for x in range(floori(bounds.position.x / cell_size), ceili(bounds.end.x / cell_size)):
		for z in range(floori(bounds.position.y / cell_size), ceili(bounds.end.y / cell_size)):
			var rect := Rect2(Vector2(x, z) * cell_size, Vector2.ONE * cell_size)
			var center := rect.get_center()
			var inside := true
			# Floor boundary erosion: each expanded corner must belong to some floor zone.
			for offset in [Vector2(-1,-1), Vector2(-1,1), Vector2(1,-1), Vector2(1,1)]:
				var sample: Vector2 = center + offset * (cell_size * 0.5 + radius * 0.8)
				var covered := false
				for zone in zones:
					if zone.has_point(sample):
						covered = true
						break
				if not covered:
					inside = false
					break
			if not inside:
				continue
			var blocked := false
			for obstacle in obstacles:
				if obstacle.intersects(rect):
					blocked = true
					break
			if blocked:
				continue
			cells[Vector2i(x, z)] = true
			var polygon := PackedInt32Array()
			for corner in [Vector2i(x,z), Vector2i(x,z+1), Vector2i(x+1,z+1), Vector2i(x+1,z)]:
				if not indices.has(corner):
					indices[corner] = vertices.size()
					vertices.append(Vector3(corner.x * cell_size, 0, corner.y * cell_size))
				polygon.append(indices[corner])
			polygons.append(polygon)
	mesh.vertices = vertices
	for polygon in polygons:
		mesh.add_polygon(polygon)
	region = NavigationRegion3D.new()
	region.navigation_mesh = mesh
	region.use_edge_connections = false
	add_child(region)

func path(from: Vector3, to: Vector3) -> PackedVector3Array:
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

