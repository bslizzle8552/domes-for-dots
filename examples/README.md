# Example worlds

Both homes load through the same Godot scene and scripts. Their authoritative,
editable content lives in `godot/content/`; these examples do not maintain copies.
The world selector reads `godot/content/catalog.json`.

| World | Character | Layout | Simulated life |
| --- | --- | --- | --- |
| [Cedar Atelier](../godot/content/worlds/cedar_atelier.json) | [Moss](../godot/content/characters/moss.json) | Cedar studio and connected outdoor terrace | Field journals, wooden mobile, herbs, wind chime, rest |
| [Tidal Observatory](../godot/content/worlds/tidal_observatory.json) | [Nova](../godot/content/characters/nova.json) | Central research deck, narrow bridge and observation wing | Horizon observation, tidal atlas, spectrum archive, rest |

Each world has its own [brief](../godot/content/briefs/), [routine](../godot/content/routines/)
and [asset manifest](../godot/content/assets/). No private third-party world was
used. All new primitive asset compositions are original MIT-licensed content.
The example characters are fictional placeholders, not connected assistants.

## The data-only extension

The Cedar Atelier's wind chime is intentionally a separate content extension:

1. `godot/content/assets/wind_chime.json` defines `hanging_chime` using cylinders
   and boxes, an explicit footprint and MIT provenance.
2. The world's `asset_manifest_paths` includes that manifest; object
   `terrace_chime` places it on the terrace.
3. Station `wind_chime` targets the object, adds the new activity tag `chime`, and
   provides reachable world-space approach/interaction anchors. `behavior` is
   empty, so ordinary navigation and interaction handle the station.
4. The routine's `chime_pause` step targets that activity tag. Character semantic
   `music` falls back to `interact`.

There is no station-type registration or wind-chime branch in the engine. This
demonstrates visual interaction only; no audio is generated. Custom effects need
a separately implemented, registered behavior; a manifest cannot invent code.

Run authoring checks after changing any content:

```powershell
python -m pip install -r requirements-dev.txt
python tools/validate_content.py
python -m unittest discover -s tests -v
```

Schema validation checks structure and versions. The authoring validator also
checks local resources, duplicate IDs, character clearance, animation fallback
chains, routine sums, finite project references and station reachability. It does
not load a rig, play an animation, or replace Godot/browser acceptance checks.

## Event and state fixtures

`mock_work_start.json` is a schema example. Its timestamp is fixed, so it will
normally be expired when used verbatim; replace the timestamp with the current
Unix time before a manual mock injection, or use the runtime's mock controls.
Real source trust cannot be granted by editing `source` in this fixture.

`initial_state.json` shows the separate runtime-state shape. Its fixed epoch is
for documentation and is not copied into live saves. Project progress is derived
by the runtime from the routine epoch and IDs, not stored as an incrementing
counter. Saves never rewrite the owner-locked brief.
