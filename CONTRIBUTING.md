# Contributing

Keep the engine reusable and the activity claims honest. A new chair, room or ordinary interaction belongs in content. A new engine capability needs a small, documented contract and evidence that both example worlds still run.

## Setup and checks

Follow [Getting started](docs/GETTING_STARTED.md). Use Godot 4.5.1 Standard, matching export templates and Python 3.11 or newer for development tools. Blender is optional. Commit source content and import settings, not `.godot/`, local state, virtual environments, downloads, exports or credentials.

Run the content validator and Python tests from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe tools\validate_content.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

For runtime changes, also run the Godot checks documented in [Getting started](docs/GETTING_STARTED.md), open both worlds, visit the affected stations and test a Web export. A headless pass does not establish browser rendering or imported-rig quality. Report what ran, its result, and what remains untested.

## Change boundaries

- Keep authored content, the creative brief, runtime state and real connections separate.
- Preserve `owner_locked` decisions. Changes to a locked choice need the owner's explicit amendment, recorded in the brief history.
- Give assets stable IDs, correct footprints and attribution. A manifest must not carry credentials or arbitrary executable snippets.
- Treat scene files and behavior scripts as reviewed application code. No automatic downloads or execution from world metadata.
- Label all synthetic events MOCK and routines SIMULATED. Do not claim a tested real adapter from a button press.
- Preserve known-good saves on failure. Schema changes require a migration plan, old-state fixture and recovery behavior.
- Include only redistributable assets; record creator, source, license and modifications. Personal photos need their own rights review before publication.

## Pull requests

Explain the user-visible result, changed content/contracts, verification and material limits. Include screenshots for visual changes and a small before/after content example for schema changes. Use the supplied pull request template. Keep private world files, transcripts, native-call audio, account identifiers and tokens out of issues and logs.

The current GitHub workflow validates content and Python tests; it does not replace the native/Web acceptance recorded for a release. New behaviors, navigation modes and persistence adapters should include focused tests for failure and recovery, not only the success path.

## Release discipline

Update the changelog, release notes and build status. Verify a clean source archive, license notices, export contents, secret scan and checksums. Tag only the verified source commit. Publishing a release for someone else's world requires their authorization; preparing a local candidate does not grant new sharing permissions.
