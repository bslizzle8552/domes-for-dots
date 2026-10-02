extends Node3D
## Original primitive joint rig. AnimationPlayer owns all pose transforms;
## the shared character motor alone owns locomotion and collision.
const Builder = preload("res://scripts/asset_builder.gd")

var primary := "#9bbde0"
var accent := "#d9a0da"
var joints: Dictionary = {}


func configure(definition: Dictionary) -> void:
	primary = definition.get("appearance", {}).get("color", primary)
	accent = definition.get("appearance", {}).get("accent", accent)


func _ready() -> void:
	_build_rig()
	_build_animations()


func _joint(parent: Node3D, joint_name: String, position: Vector3) -> Node3D:
	var joint := Node3D.new()
	joint.name = joint_name
	joint.position = position
	parent.add_child(joint)
	joints[joint_name] = joint
	return joint


func _part(parent: Node3D, shape: String, size: Array, position: Array, color: String, emission: float = 0.0) -> void:
	parent.add_child(Builder.part({"shape":shape, "size":size, "position":position, "color":color, "emission":emission}))


func _build_rig() -> void:
	var torso := _joint(self, "Torso", Vector3(0, 0.72, 0))
	_part(torso, "box", [0.43,0.40,0.32], [0,0,0], primary)
	_part(torso, "box", [0.20,0.15,0.018], [0,0.015,-0.17], "#193d53")
	_part(torso, "sphere", [0.07,0.07,0.025], [0,0.015,-0.187], accent, 0.6)
	var head := _joint(torso, "Head", Vector3(0,0.38,0))
	_part(head, "box", [0.49,0.28,0.35], [0,0,0], primary)
	_part(head, "box", [0.41,0.17,0.022], [0,0,-0.182], "#172c35")
	for x in [-0.105,0.105]:
		_part(head, "box", [0.065,0.065,0.025], [x,0.008,-0.199], accent, 0.55)
	_part(head, "cylinder", [0.026,0.12,0.026], [0,0.20,0], "#40546a")
	_part(head, "sphere", [0.075,0.075,0.075], [0,0.275,0], accent, 0.25)
	for side in ["Left", "Right"]:
		var sign_value := -1.0 if side == "Left" else 1.0
		var arm := _joint(torso, side + "Arm", Vector3(sign_value*0.275,0.13,0))
		_part(arm, "sphere", [0.12,0.12,0.12], [0,0,0], "#40546a")
		_part(arm, "box", [0.105,0.20,0.12], [0,-0.12,0], primary)
		_part(arm, "sphere", [0.135,0.12,0.15], [0,-0.265,0], accent)
		var leg := _joint(self, side + "Leg", Vector3(sign_value*0.125,0.43,0))
		_part(leg, "cylinder", [0.12,0.25,0.12], [0,-0.11,0], "#40546a")
		_part(leg, "box", [0.20,0.13,0.30], [0,-0.36,-0.035], primary)


func _base_pose() -> Dictionary:
	return {
		"Torso:position":Vector3(0,0.72,0), "Torso:rotation":Vector3.ZERO,
		"Torso/Head:rotation":Vector3.ZERO,
		"Torso/LeftArm:rotation":Vector3.ZERO, "Torso/RightArm:rotation":Vector3.ZERO,
		"LeftLeg:rotation":Vector3.ZERO, "RightLeg:rotation":Vector3.ZERO,
		"LeftLeg:position":Vector3(-0.125,0.43,0), "RightLeg:position":Vector3(0.125,0.43,0)
	}


func _pose(clip: String, phase: float) -> Dictionary:
	var pose := _base_pose()
	var wave := sin(phase*TAU)
	match clip:
		"standby":
			pose["Torso:position"].y += wave*0.006
			pose["Torso/Head:rotation"].y = wave*0.065
		"stride":
			pose["Torso/LeftArm:rotation"].x = -wave*0.45
			pose["Torso/RightArm:rotation"].x = wave*0.45
			pose["LeftLeg:rotation"].x = wave*0.28
			pose["RightLeg:rotation"].x = -wave*0.28
			# Lift both feet enough for the tilted toe to clear the floor.
			pose["LeftLeg:position"].y += absf(wave)*0.055
			pose["RightLeg:position"].y += absf(wave)*0.055
			pose["Torso:rotation"].z = wave*0.035
		"reach":
			pose["Torso/RightArm:rotation"] = Vector3(0.85+wave*0.25,0,-0.12)
			pose["Torso/LeftArm:rotation"] = Vector3(0.30,0,0.10)
			pose["Torso/Head:rotation"].x = 0.10
		"console":
			pose["Torso/LeftArm:rotation"] = Vector3(1.35+wave*0.16,0,0.12)
			pose["Torso/RightArm:rotation"] = Vector3(1.35-wave*0.16,0,-0.12)
			pose["Torso/Head:rotation"].x = 0.16
		"recharge":
			pose["Torso/Head:rotation"].x = 0.32+wave*0.025
			pose["Torso/LeftArm:rotation"] = Vector3(0.28,0,-0.50)
			pose["Torso/RightArm:rotation"] = Vector3(0.28,0,0.50)
			pose["Torso:position"].y -= 0.025
		"listen":
			pose["Torso/RightArm:rotation"] = Vector3(0.22,0,-2.88)
			pose["Torso/Head:rotation"] = Vector3(0,wave*0.035,-0.09)
	return pose


func _build_animations() -> void:
	var library := AnimationLibrary.new()
	var durations := {"standby":3.0,"stride":0.8,"reach":1.6,"console":0.8,"recharge":4.0,"listen":2.5}
	for clip in durations:
		var animation := Animation.new()
		animation.resource_name = clip
		animation.length = durations[clip]
		animation.loop_mode = Animation.LOOP_LINEAR
		for path in _base_pose():
			var track := animation.add_track(Animation.TYPE_VALUE)
			animation.track_set_path(track, NodePath(path))
			for sample in range(9):
				var phase := float(sample)/8.0
				animation.track_insert_key(track, phase*animation.length, _pose(clip,phase)[path])
		library.add_animation(clip, animation)
	$Motion.add_animation_library("", library)
