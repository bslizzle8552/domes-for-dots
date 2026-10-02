extends Node3D
## Replace this entire scene via character.scene_path. Engine only speaks semantic actions.
const Builder = preload("res://scripts/asset_builder.gd")
var action := "idle"
var phase := 0.0
var torso: Node3D
var left_hand: Node3D
var right_hand: Node3D
var halo: MeshInstance3D
var color := "#eab775"
var accent := "#fff2bf"

func configure(definition: Dictionary) -> void:
	color = definition.get("appearance", {}).get("color", color)
	accent = definition.get("appearance", {}).get("accent", accent)

func _ready() -> void:
	torso = Node3D.new()
	add_child(torso)
	torso.add_child(Builder.part({"shape":"sphere", "size":[0.55,0.64,0.5], "position":[0,0.67,0], "color":color}))
	torso.add_child(Builder.part({"shape":"sphere", "size":[0.43,0.42,0.42], "position":[0,1.12,-0.02], "color":accent}))
	for x in [-0.095,0.095]:
		torso.add_child(Builder.part({"shape":"sphere", "size":[0.065,0.07,0.035], "position":[x,1.14,-0.218], "color":"#172c35"}))
	for x in [-0.16,0.16]:
		torso.add_child(Builder.part({"shape":"box", "size":[0.19,0.16,0.3], "position":[x,0.11,-0.045], "color":color}))
	left_hand = Builder.part({"shape":"sphere", "size":[0.16,0.23,0.16], "position":[-0.36,0.7,0], "color":accent})
	right_hand = Builder.part({"shape":"sphere", "size":[0.16,0.23,0.16], "position":[0.36,0.7,0], "color":accent})
	torso.add_child(left_hand)
	torso.add_child(right_hand)
	halo = Builder.part({"shape":"cylinder", "size":[0.68,0.015,0.68], "position":[0,0.025,0], "color":accent, "emission":0.2})
	add_child(halo)

func set_action(value: String) -> void:
	action = value

func _process(delta: float) -> void:
	phase += delta
	if not is_instance_valid(torso):
		return
	torso.position.y = sin(phase * (9.0 if action == "walk" else 2.0)) * (0.045 if action == "walk" else 0.018)
	left_hand.position = Vector3(-0.36,0.7,0)
	right_hand.position = Vector3(0.36,0.7,0)
	if action == "phone":
		right_hand.position = Vector3(0.25,1.1,-0.12)
	elif action == "walk":
		left_hand.position.z = sin(phase*9)*0.15
		right_hand.position.z = -sin(phase*9)*0.15
	elif action != "idle" and action != "sit":
		left_hand.position = Vector3(-0.22,0.81+sin(phase*5)*0.04,-0.32)
		right_hand.position = Vector3(0.22,0.81-sin(phase*5)*0.04,-0.32)
	# 'sit' intentionally falls back to grounded idle unless a compatible rig is supplied.

