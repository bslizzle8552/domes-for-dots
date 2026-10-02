extends CanvasLayer
signal command(action: String, value: String)
var title_label: Label
var description_label: Label
var activity_label: Label
var detail_label: Label
var state_label: Label
var project_label: Label
var save_label: Label
var notice_label: Label
var world_picker: OptionButton
var station_picker: OptionButton
var markers: CheckBox
var autonomy_pause: CheckBox
var activity_picker: OptionButton
var catalog: Array = []
var station_ids: Array[String] = []
var activity_ids: Array[String] = []
var button_controls: Dictionary = {}

func _ready() -> void:
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	var header := _label(root,"DOMES FOR DOTS   /   0.2",17,"b8cabb")
	header.position = Vector2(30,23)
	title_label = _label(root,"",30)
	title_label.position = Vector2(30,51)
	var panel := PanelContainer.new()
	panel.position = Vector2(28,108)
	panel.size = Vector2(326,760)
	panel.anchor_bottom = 1.0
	panel.offset_bottom = -24
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.04,0.075,0.082,0.97)
	style.border_color = Color("3a514d")
	style.set_border_width_all(1)
	style.set_corner_radius_all(14)
	style.content_margin_left = 20
	style.content_margin_right = 20
	style.content_margin_top = 18
	style.content_margin_bottom = 18
	panel.add_theme_stylebox_override("panel",style)
	root.add_child(panel)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	panel.add_child(scroll)
	var column := VBoxContainer.new()
	column.custom_minimum_size.x = 274
	column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	column.add_theme_constant_override("separation",8)
	scroll.add_child(column)
	_label(column,"A PLACE OF THEIR OWN",13,"b5d0b0")
	world_picker = OptionButton.new()
	world_picker.custom_minimum_size.y = 38
	column.add_child(world_picker)
	world_picker.item_selected.connect(func(index: int): command.emit("world",catalog[index].id))
	description_label = _label(column,"",14)
	description_label.custom_minimum_size.y = 62
	description_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	column.add_child(HSeparator.new())
	activity_label = _label(column,"SIMULATED",18,"c5dfa4")
	detail_label = _label(column,"Preparing a home...",14)
	detail_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	detail_label.custom_minimum_size.y = 36
	state_label = _label(column,"",12,"a7b7b4")
	state_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	project_label = _label(column,"",14)
	project_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	project_label.custom_minimum_size.y = 64
	_label(column,"Imagined projects use elapsed time.\nNo model is working on these projects.",12,"a7b7b4")
	_row(column,[["Preview +30 min","advance","1800"],["Live time","live",""]])
	column.add_child(HSeparator.new())
	_label(column,"VISIT A STATION",12,"b5d0b0")
	station_picker = OptionButton.new()
	station_picker.custom_minimum_size.y = 34
	column.add_child(station_picker)
	_row(column,[["Visit","visit_selected",""],["Resume routine","resume",""]])
	autonomy_pause = CheckBox.new()
	autonomy_pause.text = "Pause autonomous movement"
	autonomy_pause.toggled.connect(func(value: bool): command.emit("pause_autonomy",str(value)))
	column.add_child(autonomy_pause)
	column.add_child(HSeparator.new())
	_label(column,"MOCK ACTIVITY TESTS",12,"e8c28a")
	_row(column,[["MOCK work","work_start",""],["MOCK call","call_start",""]])
	_row(column,[["End call","call_end",""],["End work","work_end",""]])
	activity_picker = OptionButton.new()
	activity_picker.custom_minimum_size.y = 30
	column.add_child(activity_picker)
	_row(column,[["MOCK selected activity","mock_selected",""]])
	_label(column,"Visuals only · call audio stays in ChatGPT",12,"a7b7b4")
	column.add_child(HSeparator.new())
	_label(column,"REAL CONNECTIONS · UNAVAILABLE",12,"b8c3cc")
	markers = CheckBox.new()
	markers.text = "Show station markers"
	markers.button_pressed = true
	markers.toggled.connect(func(value: bool): command.emit("markers",str(value)))
	column.add_child(markers)
	_row(column,[["Save","save",""],["Export state","export_state",""],["World pack","export_world",""]])
	save_label = _label(column,"Local state",12,"c5dfa4")
	save_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	notice_label = _label(column,"",12,"e8c28a")
	notice_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var footer := _label(root,"ONE ENGINE  /  OPEN CONTENT  /  YOUR DOT'S CHOICES",12,"c1cec8")
	footer.position = Vector2(392,850)

func _label(parent: Node, text: String, font_size: int, color: String = "e8ede6") -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size",font_size)
	label.modulate = Color(color)
	parent.add_child(label)
	return label

func _row(parent: Node, buttons: Array) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation",6)
	parent.add_child(row)
	for data in buttons:
		var button := Button.new()
		button.text = data[0]
		button.custom_minimum_size.y = 32
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.add_theme_font_size_override("font_size",13)
		button.pressed.connect(func():
			if data[1] == "visit_selected":
				command.emit("visit",station_ids[station_picker.selected])
			elif data[1] == "mock_selected":
				if not activity_ids.is_empty():
					command.emit("activity_start",activity_ids[activity_picker.selected])
			else:
				command.emit(data[1],data[2])
		)
		row.add_child(button)
		button_controls[data[1]] = button

func set_catalog(data: Array) -> void:
	catalog = data
	world_picker.clear()
	for world in catalog:
		world_picker.add_item(world.title)

func set_world(world: Dictionary, show_markers: bool, autonomy_paused: bool = false) -> void:
	title_label.text = world.title
	description_label.text = world.description
	for i in catalog.size():
		if catalog[i].id == world.id:
			world_picker.select(i)
	station_picker.clear()
	station_ids.clear()
	activity_picker.clear()
	activity_ids.clear()
	for station in world.stations:
		station_ids.append(station.id)
		station_picker.add_item(station.label)
		for tag in station.activity_tags:
			if not tag in activity_ids and not tag in ["call","work"]:
				activity_ids.append(tag)
				activity_picker.add_item(str(tag).replace("_"," ").capitalize())
	markers.set_pressed_no_signal(show_markers)
	autonomy_pause.set_pressed_no_signal(autonomy_paused)
	notice_label.text = ""

func control_bounds() -> Dictionary:
	var result: Dictionary = {}
	for action in button_controls:
		var button: Button = button_controls[action]
		var rectangle: Rect2 = button.get_global_rect()
		var visible: Rect2 = rectangle.intersection(get_viewport().get_visible_rect())
		var ancestor: Node = button.get_parent()
		while ancestor != null:
			if ancestor is Control and ancestor.clip_contents:
				visible = visible.intersection(ancestor.get_global_rect())
			ancestor = ancestor.get_parent()
		result[action] = {"x":rectangle.position.x,"y":rectangle.position.y,"width":rectangle.size.x,"height":rectangle.size.y,"visible":button.is_visible_in_tree() and visible.has_area(),"visible_x":visible.position.x,"visible_y":visible.position.y,"visible_width":visible.size.x,"visible_height":visible.size.y}
	return result
