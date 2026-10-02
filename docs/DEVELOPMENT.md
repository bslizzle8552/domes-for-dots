# Development and cloud worker setup

This checkout is V2 / 0.2.0. Download the verified source and Web ZIPs from the [v0.2.0 release](https://github.com/bslizzle8552/domes-for-dots/releases/tag/v0.2.0). See [V2 build record](V2_BUILD.md) for current acceptance and [World authoring](WORLD_AUTHORING.md) for executable creation and expansion.

This guide is DEVELOPMENT ONLY / CLOUD BACKEND. These tools belong on a contributor machine or authorized operator's worker. Normal owners can visit the verified hosted proof through [Getting started](GETTING_STARTED.md); general conversation-to-private-world creation is a target capability, not a deployed self-service route. Owners never need to execute these instructions. A Dot having code tools does not establish that it has a particular virtual machine or installed software; inspect the actual execution environment.

## Requirements

- **Godot 4.5.1 Standard**, the GDScript build. The release build uses `4.5.1.stable.official.f62fdbde1`. Install the matching 4.5.1 export templates for Web builds.
- A desktop browser supporting WebAssembly and WebGL 2 for Web preview.
- Python 3.11+ for the local server, content validation and build tools. Install development requirements for the validator/tests.

Blender is optional for authoring and is not needed to run the original primitive examples. An AI service and a Dot account are not runtime requirements either. Source archives do not bundle the Godot editor; use the pinned installation in the build environment.

Download the editor and templates from the [Godot 4.5.1 archive](https://godotengine.org/download/archive/4.5.1-stable/). In the editor, use **Editor → Manage Export Templates** and install the matching `.tpz`. If you already use another Godot version, keep this project's pinned editor separate until you have tested an upgrade.

## Run in Godot

1. Clone or extract this repository.
2. Import `godot/project.godot` into Godot 4.5.1.
3. Wait for the initial import, then press **F5**.
4. Switch between Cedar Atelier, Tidal Observatory and Lantern Archive. Visit several stations and wait for the character to arrive.
5. Try a MOCK work event followed by MOCK call. When the call ends or expires, any still-valid work can resume. Otherwise the simulated routine resumes.

**Preview +30 min** changes only the displayed simulation time; **Live time** clears the offset. It does not extend activity TTLs or save the preview offset as real elapsed time. A manual **Visit** remains selected until **Resume routine**, while MOCK activity can temporarily take priority.

**Show station markers** changes the current local preference; press **Save** to persist it. There is no in-app layout editor. **Export state** writes the runtime JSON; **World pack** writes authored JSON for the world, character, routine, resolved asset definitions and brief. It does not bundle referenced scene/model/texture binaries and is not accepted by an in-app importer. A complete editable backup is the source project plus runtime state. Browser exports download files; native exports write under Godot's `user://` directory and display the resolved location.

## Command line setup

Examples below run from the repository root in PowerShell. Replace the editor path with your installation; use the console executable on Windows for visible diagnostics.

```powershell
$env:GODOT_BIN = 'C:\path\to\Godot_v4.5.1-stable_win64_console.exe'
& $env:GODOT_BIN --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
& $env:GODOT_BIN --editor --path godot
```

On macOS/Linux, set `GODOT_BIN` to the executable and use `.venv/bin/python` in place of `.venv\Scripts\python.exe`. These platforms need their own runtime/browser acceptance; the release's recorded verification is in [BUILD_STATUS.md](../BUILD_STATUS.md).

## Validate and test

```powershell
.\.venv\Scripts\python.exe tools\validate_content.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
& $env:GODOT_BIN --headless --path godot --script res://tests/test_core.gd
& $env:GODOT_BIN --headless --fixed-fps 60 --path godot --script res://tests/test_runtime.gd
& $env:GODOT_BIN --headless --fixed-fps 60 --path godot --script res://tests/test_character.gd
& $env:GODOT_BIN --headless --path godot --script res://tools/audit_characters.gd
```

The validator checks JSON schemas and content relationships. Core tests exercise deterministic state/event behavior. Runtime tests load the real engine and its examples; `--fixed-fps 60` removes wall-clock pacing while retaining real physics callbacks. Browser rendering, visual poses and user interaction also need an actual preview; passing JSON validation alone does not prove them.

## Build and serve Web

```powershell
.\.venv\Scripts\python.exe tools\build.py --godot $env:GODOT_BIN
.\.venv\Scripts\python.exe tools\serve.py --port 8060
```

Open [http://127.0.0.1:8060](http://127.0.0.1:8060). The export is `dist/web/index.html`; keep all generated siblings together. Stop the server with **Ctrl+C**. Do not open the Godot export through `file://`. See [Web export](WEB_EXPORT.md) for hosting and diagnosis.

## State and recovery

World JSON is authored source. Save creates runtime state separately: world/character/routine identity, routine epoch, project IDs, preferences and a revision. Project progress is derived from elapsed time. Export state before clearing browser storage or changing deployments.

If the runtime reports a conflict, preserve your export and reload the current state before saving again. Native state lives under Godot's `user://state/<world-id>.json`, with a `.bak` copy; browser keys use `domes-for-dots.v1:<world-id>` and the `.bak` suffix. A valid backup can recover a missing/corrupt primary with a visible warning. Keep both copies when investigating an error.

A killed native writer can leave a `.json.lock` directory. If `writer_busy_or_stale_lock` persists, close all viewers before removing that world's empty lock directory. Do not remove a lock while a writer might still be active. A browser save does not synchronize to another browser, origin or machine. See [World format](WORLD_FORMAT.md#runtime-state-and-upgrades) and [Core notes](CORE_NOTES.md) for the adapter limits.

## Make it yours

Paste the [create-world prompt](../prompts/CREATE_MY_WORLD.md) to your Dot, or give the resulting brief to a build agent. Use one example as a schema reference, give your new world a new ID and register it in `godot/content/catalog.json`. Check every station and re-export. The prompt does not require copying either example's theme, furniture or personality.
