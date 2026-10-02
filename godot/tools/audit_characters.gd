extends SceneTree
## Godot --headless --path godot --script res://tools/audit_characters.gd --
##   [--character res://content/characters/nova.json] [--output absolute/report.json]
const Audit = preload("res://scripts/character_audit.gd")


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var selected := ""
	var output := ""
	var args := OS.get_cmdline_user_args()
	var index := 0
	while index < args.size():
		if args[index] not in ["--character", "--output"] or index+1 >= args.size():
			printerr("Usage: --character res://content/characters/name.json --output report.json")
			quit(2)
			return
		if args[index] == "--character":
			selected = args[index+1]
		else:
			output = args[index+1]
		index += 2
	var paths: Array[String] = []
	if not selected.is_empty():
		paths.append(selected)
	else:
		for filename in DirAccess.get_files_at("res://content/characters"):
			if filename.ends_with(".json"):
				paths.append("res://content/characters/" + filename)
	paths.sort()
	var reports: Array = []
	var ok := not paths.is_empty()
	for path in paths:
		var definition = JSON.parse_string(FileAccess.get_file_as_string(path))
		if not definition is Dictionary:
			reports.append({"ok":false,"definition_path":path,"errors":["character JSON could not be read"]})
			ok = false
			continue
		var report := Audit.inspect(definition, root)
		report["definition_path"] = path
		reports.append(report)
		ok = ok and report.ok
	var document := {"schema_version":1,"ok":ok,"characters":reports,"engine_version":Engine.get_version_info().string}
	var serialized := JSON.stringify(document, "  ") + "\n"
	if not output.is_empty():
		var file := FileAccess.open(output, FileAccess.WRITE)
		if file == null:
			printerr("Unable to write character audit output: " + str(FileAccess.get_open_error()))
			quit(2)
			return
		file.store_string(serialized)
		file.close()
	else:
		print("CHARACTER_AUDIT_JSON=" + JSON.stringify(document))
	print("CHARACTER AUDIT: %d characters, %s" % [reports.size(), "PASS" if ok else "FAIL"])
	quit(0 if ok else 1)
