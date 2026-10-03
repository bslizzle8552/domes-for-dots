# Operator World Creator

This is the reproducible synthetic proof, operated in developer/cloud infrastructure. Owners visit its hosted browser output without installing Python, Godot or other development tools. This command does not publish anything.

With the repository development dependencies and Godot 4.5.1 Standard plus matching single-threaded Web templates already available, one invocation builds all three worlds:

```sh
python tools/world_creator_worker.py --job-dir artifacts/world-creator-run-001 --godot /path/to/Godot_v4.5.1-stable
```

Each attempt requires a new job directory. Repeat with `world-creator-run-002` to create another independent candidate. The worker reads the three checked synthetic WorldIntent/CharacterSpec pairs under `examples/world_creator`, generates distinct Character and World packages, composes the shared runtime, validates content, imports and audits characters, tests character motions and world/ramp traversal, then exports Web.

Read `<job-dir>/job.json` first. Success requires explicit zero-failure engine summaries and complete Web files. The receipt records source commit and file hashes, engine identity, package hashes, per-phase durations and export hashes. Packages and logs remain beside it. The Web directory includes runtime files and licenses. Browser playback, private access, durable hosted state and publication are separate acceptance gates; the worker does not infer them from an export.

## GitHub Actions

`Cloud world creator` (`.github/workflows/world-creator.yml`) runs on relevant pushes to `codex/autonomous-world-creator`, relevant pull-request changes and manual dispatch. There is no draft-PR exclusion. The cloud job checks out the exact feature head for PR runs; the existing `Validate content and contracts` workflow also covers GitHub's PR merge checkout. Permissions are read-only and there are no deployment secrets.

The restricted push trigger provides a first run before this newly added workflow exists on `main`. GitHub documents a default-branch requirement for manual workflow availability, with API/CLI branch dispatch available after the workflow has run; do not merge merely to manufacture a first execution. See [GitHub workflow trigger documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_dispatch).

After the first run is registered, an authorized operator can request a fresh run against the feature branch:

```sh
gh workflow run world-creator.yml --ref codex/autonomous-world-creator
```

Monitor the actual run and inspect its conclusion. Download `world-creator-evidence` for packages/receipts/logs and `three-worlds-web` for the complete runtime. A canceled, queued or failed run is not a successful cloud build.

The Linux job uses Python 3.12 and the existing `setup_cloud_godot.py` bootstrap, which verifies official archive SHA-512 values and installs Godot 4.5.1 plus `web_nothreads_release.zip`/`web_nothreads_debug.zip` templates into the matching user template directory. The checked export preset is Compatibility renderer, single-threaded Web, includes JSON content and excludes tests. The worker passes an absolute export path. These match [Godot's headless export requirements](https://docs.godotengine.org/en/4.5/tutorials/editor/command_line_tutorial.html#exporting).

The six checked package manifests were independently compared with their normalized Git blob contents; every hashed payload matches, and JSON payloads use LF. This removes a Windows-CRLF/Linux-checkout hash hazard. It is not a substitute for observing the Linux workflow finish.

## Input and delivery boundary

This workflow currently accepts the three reviewed synthetic fixtures. It is not a general private-upload endpoint or a self-service world service. No model call or real Dot interview is implied by those examples.

The local operator APIs already accept schema-valid intent plus a separately validated Character Package: `world_package.build_package(...)` and `world_composer.compose(...)`. The next cloud-input step is a bounded authenticated request adapter that carries those same contracts, checks owner authority, stores private inputs outside public artifacts, and selects only trusted compiler/character producers. It should reuse these validators instead of adding arbitrary scripts, URLs or general executable uploads.

The subsequent delivery step consumes the validated Web artifact through the supported private Site adapter, checks the actual hosted bytes, exercises a fresh browser session, and validates state and revision behavior. Native hosting capability and limits must be reported from the actual experiment. Never use another Dot's private world as the test target.
