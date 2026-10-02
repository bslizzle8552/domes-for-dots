extends RefCounted
## Pure elapsed-time simulation. Calling evaluate never mutates content or state.


static func evaluate(routine: Dictionary, epoch: float, now: float) -> Dictionary:
	var empty: Dictionary = {"step": {}, "projects": [], "elapsed": 0.0}
	if not is_finite(epoch) or not is_finite(now):
		empty["error"] = "Simulation timestamps must be finite."
		return empty
	var elapsed: float = maxf(0.0, now - epoch)
	if not is_finite(elapsed):
		empty["error"] = "Simulation time range is too large."
		return empty
	var cycle: float = float(routine.get("cycle_seconds", 0.0))
	var steps: Array = routine.get("steps", [])
	if cycle <= 0.0 or not is_finite(cycle) or steps.is_empty():
		empty["error"] = "Routine requires a positive cycle and steps."
		return empty
	var duration_sum: float = 0.0
	var per_cycle: Dictionary = {}
	for raw_step in steps:
		if not raw_step is Dictionary:
			empty["error"] = "Routine step must be an object."
			return empty
		var duration: float = float(raw_step.get("duration_seconds", 0.0))
		if duration <= 0.0 or not is_finite(duration):
			empty["error"] = "Routine step duration must be positive and finite."
			return empty
		duration_sum += duration
		var tag: String = str(raw_step.get("activity_tag", ""))
		per_cycle[tag] = float(per_cycle.get(tag, 0.0)) + duration
	if not is_equal_approx(duration_sum, cycle):
		empty["error"] = "Routine step durations must sum to cycle_seconds."
		return empty
	var whole_cycles: float = floor(elapsed / cycle)
	var remainder: float = fposmod(elapsed, cycle)
	var accumulated: Dictionary = {}
	for tag in per_cycle:
		accumulated[tag] = whole_cycles * float(per_cycle[tag])
	var cursor: float = 0.0
	var selected: Dictionary = steps[0]
	var selected_offset: float = 0.0
	for step in steps:
		var duration: float = float(step["duration_seconds"])
		var tag: String = str(step.get("activity_tag", ""))
		accumulated[tag] = float(accumulated.get(tag, 0.0)) + clampf(remainder - cursor, 0.0, duration)
		if remainder >= cursor and remainder < cursor + duration:
			selected = step
			selected_offset = cursor
		cursor += duration
	var projects: Array = []
	for project in routine.get("projects", []):
		if not project is Dictionary:
			continue
		var required: float = float(project.get("required_seconds", 0.0))
		if required <= 0.0 or not is_finite(required):
			continue
		var progress: float = clampf(float(accumulated.get(str(project.get("activity_tag", "")), 0.0)) / required, 0.0, 1.0)
		var stages: Array = project.get("stages", [])
		var stage: String = ""
		if not stages.is_empty():
			stage = str(stages[mini(int(floor(progress * stages.size())), stages.size() - 1)])
		projects.append({"id": project.get("id", ""), "title": project.get("title", ""), "progress": progress, "stage": stage})
	var started_at: float = epoch + whole_cycles * cycle + selected_offset
	return {"step": selected.duplicate(true), "projects": projects, "elapsed": elapsed, "cycle_index": whole_cycles, "step_started_at": started_at, "step_ends_at": started_at + float(selected.duration_seconds)}
