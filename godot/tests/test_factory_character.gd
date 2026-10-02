extends SceneTree
## Isolated generated-package acceptance. Called only after a factory install.
## -- --character res://content/characters/aster.json
const Audit = preload("res://scripts/character_audit.gd")
const Motor = preload("res://scripts/character_motor.gd")
var passed := 0
var failed := 0


func check(condition: bool, label: String) -> void:
	if condition:
		passed += 1
	else:
		failed += 1
		printerr("FAIL: " + label)


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 2 or args[0] != "--character":
		printerr("Usage: -- --character res://content/characters/generated.json")
		quit(2)
		return
	var definition: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[1]))
	var audit := Audit.inspect(definition, root)
	check(audit.ok, "actual imported character audit")
	var motor = Motor.new()
	root.add_child(motor)
	motor.configure(definition)
	var player: AnimationPlayer = motor.animation_player
	var skeleton: Skeleton3D = motor.visual.get_node_or_null(definition.rig.skeleton_path)
	check(is_instance_valid(skeleton) and skeleton.get_bone_count() == 18, "imported 18-bone skeleton")
	check(is_instance_valid(player), "imported animation player")
	if not is_instance_valid(player) or not is_instance_valid(skeleton):
		quit(1)
		return
	for semantic in definition.animations:
		motor.set_action(semantic)
		var clip: Animation = player.get_animation(definition.animations[semantic])
		check(clip.loop_mode == Animation.LOOP_LINEAR, semantic + " loops after glTF import")
		player.seek(0, true)
		var initial := []
		for index in range(skeleton.get_bone_count()):
			initial.append(skeleton.get_bone_pose_rotation(index))
		player.seek(0.375, true)
		var changed := false
		for index in range(skeleton.get_bone_count()):
			changed = changed or not initial[index].is_equal_approx(skeleton.get_bone_pose_rotation(index))
		check(changed, semantic + " changes real skeleton joint transforms")
		check(motor.position.is_equal_approx(Vector3.ZERO), semantic + " leaves motor translation in engine control")
		var hips := skeleton.get_bone_pose_position(skeleton.find_bone("Hips"))
		check(absf(hips.x) < 0.0001 and absf(hips.z) < 0.0001, semantic + " has no horizontal root motion")
	# Every authored clip must reset the standing body after a seated/phone clip.
	motor.set_action("idle")
	player.seek(0.5, true)
	var idle_arm := skeleton.get_bone_pose_rotation(skeleton.find_bone("RightUpperArm"))
	var idle_hips := skeleton.get_bone_pose_position(skeleton.find_bone("Hips"))
	for prior in ["phone", "sit", "sleep", "garden"]:
		motor.set_action(prior)
		player.seek(0.5, true)
		motor.set_action("idle")
		player.seek(0.5, true)
		check(skeleton.get_bone_pose_rotation(skeleton.find_bone("RightUpperArm")).is_equal_approx(idle_arm), prior + " resets arm on idle transition")
		check(skeleton.get_bone_pose_position(skeleton.find_bone("Hips")).is_equal_approx(idle_hips), prior + " resets hips on idle transition")
	motor.queue_free()
	await process_frame
	print("FACTORY CHARACTER TESTS: %d passed, %d failed" % [passed, failed])
	quit(0 if failed == 0 else 1)
