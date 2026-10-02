extends RefCounted
## Geometry primitives are a composition vocabulary, never a list of furniture or station types.

static func vector(values: Array) -> Vector3:
	return Vector3(values[0], values[1], values[2])

static func material(color: String, emission: float = 0.0) -> StandardMaterial3D:
	var result := StandardMaterial3D.new()
	result.albedo_color = Color(color)
	result.roughness = 0.8
	if emission > 0.0:
		result.emission_enabled = true
		result.emission = Color(color)
		result.emission_energy_multiplier = emission
	return result

static func part(data: Dictionary) -> MeshInstance3D:
	var instance := MeshInstance3D.new()
	var dimensions := vector(data.size)
	match data.shape:
		"box":
			var box := BoxMesh.new()
			box.size = dimensions
			instance.mesh = box
		"sphere":
			var sphere := SphereMesh.new()
			sphere.radius = 0.5
			sphere.height = 1.0
			sphere.radial_segments = 16
			sphere.rings = 8
			instance.mesh = sphere
			instance.scale = dimensions
		"cylinder":
			var cylinder := CylinderMesh.new()
			cylinder.top_radius = 0.5
			cylinder.bottom_radius = 0.5
			cylinder.height = 1.0
			cylinder.radial_segments = 16
			instance.mesh = cylinder
			instance.scale = dimensions
	instance.position = vector(data.get("position", [0, 0, 0]))
	instance.rotation_degrees = vector(data.get("rotation", [0, 0, 0]))
	instance.material_override = material(data.get("color", "#8899aa"), data.get("emission", 0.0))
	return instance

static func instantiate(asset: Dictionary, object: Dictionary) -> Node3D:
	var root := Node3D.new()
	root.name = object.id
	root.position = vector(object.position)
	root.rotation_degrees.y = object.get("rotation_y", 0.0)
	root.scale = vector(object.get("scale", [1, 1, 1]))
	var visual := Node3D.new()
	visual.name = "Visual"
	visual.scale = vector(asset.get("scale", [1, 1, 1]))
	visual.rotation_degrees.y = asset.get("rotation_y", 0.0)
	root.add_child(visual)
	var scene_path: String = asset.get("scene_path", "")
	if not scene_path.is_empty() and ResourceLoader.exists(scene_path):
		var scene = load(scene_path)
		if scene is PackedScene:
			visual.add_child(scene.instantiate())
	else:
		for component in asset.get("parts", []):
			visual.add_child(part(component))
	var collision: Dictionary = asset.get("collision", {})
	if collision.get("enabled", false):
		var body := StaticBody3D.new()
		var shape := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = vector(collision.size)
		shape.shape = box
		shape.position = vector(collision.get("offset", [0, 0, 0]))
		body.add_child(shape)
		visual.add_child(body)
	return root

static func obstacle(asset: Dictionary, object: Dictionary) -> Rect2:
	if not asset.get("collision", {}).get("enabled", false):
		return Rect2()
	var footprint: Array = asset.get("footprint", [0, 0])
	var asset_scale := vector(asset.get("scale",[1,1,1]))
	var object_scale := vector(object.get("scale",[1,1,1]))
	var low := Vector2(INF,INF)
	var high := Vector2(-INF,-INF)
	for sign_v in [Vector2(-1,-1),Vector2(-1,1),Vector2(1,-1),Vector2(1,1)]:
		var corner: Vector2 = sign_v * Vector2(footprint[0],footprint[1]) * 0.5
		corner *= Vector2(asset_scale.x,asset_scale.z)
		corner = corner.rotated(-deg_to_rad(float(asset.get("rotation_y",0))))
		corner *= Vector2(object_scale.x,object_scale.z)
		corner = corner.rotated(-deg_to_rad(float(object.get("rotation_y",0))))
		low = low.min(corner)
		high = high.max(corner)
	var center := Vector2(object.position[0], object.position[2])
	return Rect2(center+low,high-low)
