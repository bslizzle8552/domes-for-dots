# V2 virtual-only dependency audit

Audited 2026-10-02 against the current repository, not the historical HTML prototype. Scope: tracked documentation/prompts, Python build/authoring/release tools, Godot source/scenes/content/schemas/export configuration, tests, workflows and example authoring instructions. Ignored local `.tools`, `.venv`, caches, `artifacts` and `dist` are execution/output locations, not shipped user dependencies. License text and prior evidence receipts are preserved as records.

**Product rule:** a normal owner supplies creative input and visits a hosted URL. They do not install software, clone repositories, run commands, manipulate project files or deploy builds. Tools running on an operator machine, CI runner or cloud worker remain acceptable.

## Classification

| Category | Meaning |
| --- | --- |
| DEVELOPMENT ONLY | Contributor setup, source changes, diagnostics and local acceptance. Never an owner prerequisite. |
| CLOUD BACKEND | Generation, rigging, export, validation, deployment and recovery performed by managed infrastructure. |
| USER RUNTIME | Browser-delivered application and its honest visible capabilities/limits. No specialized install. |
| REMOVE/REPLACE | A workflow offered to ordinary owners that requires local production tools, manual files or claims unsupported hosted capability. |

## Findings and changes

| Exact path / area | Baseline dependency or assumption | Classification and disposition |
| --- | --- | --- |
| `README.md` Quick start | Download/extract Web ZIP, install/use Python server; alternatively create venv/build or open Godot. | **REMOVE/REPLACE:** replaced owner entry with hosted URL/conversation, explicit no-install rule, deployment evidence link and separate developer setup. |
| `docs/GETTING_STARTED.md` | “Getting started” led directly to Godot/templates/Python, clone/import/F5, commands, local server and manual recovery. | **REMOVE/REPLACE:** now an owner guide without setup commands. Operational material preserved in `docs/DEVELOPMENT.md`. |
| `docs/DEVELOPMENT.md`, `CONTRIBUTING.md` | Pinned editor, templates, Python environment, tests, local server and packaging. | **DEVELOPMENT ONLY / CLOUD BACKEND:** retained and explicitly separated from owner onboarding. |
| `docs/DOT_ONBOARDING.md` | Assumed Godot/Blender on a Dot VM; described writing project files and delivering changed files. | **REMOVE/REPLACE:** inspect connected services, preserve Dot/human input, backend writes files, owner receives hosted URL. Missing backend is a service blocker. |
| `prompts/CREATE_MY_WORLD.md` | Owner attaches repo, reports tools; agent assumes VM, runs CLI and returns preview. | **REMOVE/REPLACE:** no owner repo/toolchain requirement, remote work only, actual service capability tests, character self-description, hosted proof and persistence status. |
| `prompts/CREATE_CHARACTER.md` | Blender/rig adaptation and filesystem steps lacked a clear service boundary. | **REMOVE/REPLACE:** explicit remote worker, Dot interview, generator-independent package and honest reference handling. Commands remain agent/worker instructions. |
| `prompts/EXPAND_MY_WORLD.md`, `prompts/ADD_ASSET.md` | Project-file handoff, CLI operations and creative software could be read as owner work. | **REMOVE/REPLACE:** owner identifies world/describes changes; cloud worker handles files, import, validation and publication. |
| `docs/WORLD_AUTHORING.md`, `tools/world_author.py`, `examples/authoring/make_cedar_telescope.py`, `examples/authoring/lantern_archive/README.md` | Python proposals, hash-bound plans, apply/recover, writer locks and filesystem backups. | **CLOUD BACKEND / DEVELOPMENT ONLY:** preserved. Guide now labels scope. The CLI is not an authenticated multi-tenant API; isolated worker checkout and service ownership checks remain necessary. |
| `docs/CHARACTER_PIPELINE.md`, `docs/ASSET_PIPELINE.md`, `godot/tools/audit_characters.gd`, `godot/scripts/character_audit.gd` | Scene/model authoring, import, rig/clip checks and headless Godot. | **CLOUD BACKEND / DEVELOPMENT ONLY:** preserved standard visual/semantic contract; character guide now explicitly prohibits owner installs during creation as well as playback. |
| `docs/WEB_EXPORT.md`, `tools/build.py`, `godot/export_presets.cfg` | Existing Godot 4.5.1/templates; headless import/tests/export; generated Web siblings. | **CLOUD BACKEND / DEVELOPMENT ONLY:** preserved build. Hosting responsibilities now belong to operator; browser URL is the user handoff. |
| `tools/build.py::WEB_README` | Generated Web artifact told recipients to run Python locally. | **REMOVE/REPLACE:** coordinating implementation updates packaged instructions to hosted delivery and operator-only preview. Verify rebuilt `README.txt` with final build receipt. |
| `tools/serve.py` | Python HTTP server on loopback. | **DEVELOPMENT ONLY:** useful preview; explicitly not a production or owner entry path. |
| `tools/browser_acceptance.cjs` | Node, Playwright, installed Chrome, `DOMES_URL`, downloaded evidence. | **DEVELOPMENT ONLY / CLOUD BACKEND:** acceptance runner can target hosted URL; these packages are never shipped requirements. |
| `tools/check_release.py`, `tools/package_release.py`, `tools/README.md`, `requirements-dev.txt` | Git-tracked source inspection, Python dependencies, archives, hashes. | **DEVELOPMENT ONLY / CLOUD BACKEND:** keep operator release tooling. A downloadable release is an artifact, not browser deployment proof. |
| `.github/workflows/validate.yml` | Installs Python/dependencies on a GitHub-hosted runner. | **CLOUD BACKEND:** already satisfies no-owner-install boundary; baseline covered schemas/Python tests, not full engine export/deployment. New worker execution evidence belongs in final build status. |
| `godot/scripts/content_loader.gd`, `godot/content/catalog.json`, `schemas/*.schema.json` | `res://` bundled resources and world catalog. | **CLOUD BACKEND + USER RUNTIME:** valid static-package design. A user cannot upload an arbitrary character or edit a hosted world just by changing a URL; service rebuild/package installation is required. |
| `godot/scripts/main.gd` state/world export | Browser JSON download; native `user://exports` writes; no in-app importer. | **USER RUNTIME:** optional backup/export, not required to visit. **REMOVE/REPLACE for full cloud recovery:** future account restore must remove dependence on owner-managed files. |
| `godot/scripts/core/state_store.gd` | Native files under `user://state`, browser `JavaScriptBridge`/`localStorage`, synchronous methods. | **USER RUNTIME:** no installation needed, but browser-local only. **REMOVE/REPLACE for account persistence:** implement asynchronous authenticated revisioned storage; retain local fallback honestly. Static hosting alone cannot solve this. |
| `godot/scripts/core/simulation.gd`, `activity_store.gd`, `resident_state.gd` | Elapsed-time progress, transient event leases, SIMULATED/MOCK behavior. | **USER RUNTIME:** retain. No continuously running local process/model is required for elapsed-time progress. Real activity adapters remain unavailable until authenticated and tested. |
| `godot/scripts/character_motor.gd`, `placeholder_visual.gd`, `articulated_robot_visual.gd` | Runtime movement/visual generation and semantic animation. | **USER RUNTIME:** execute inside delivered Godot Web application; do not require Godot Editor or Blender installation. |
| `godot/project.godot`, `godot/scenes/**`, remaining engine scripts | Godot resource graph, render/UI/navigation. | **USER RUNTIME** when exported; **DEVELOPMENT ONLY** for editing. Preserve working engine and scene architecture. |
| `tests/*.py`, `godot/tests/**` | Python, Godot, fixture files and native temporary saves. | **DEVELOPMENT ONLY / CLOUD BACKEND:** retain isolated tests; native test success does not establish remote account/browser compatibility. |
| `docs/ARCHITECTURE.md`, `CORE_NOTES.md`, `IMPLEMENTATION_CONTRACT.md`, `WORLD_FORMAT.md`, `ACTIVITY_EVENTS.md`, `PRIVACY.md` | Internal local storage/resource assumptions and future adapter descriptions. | **DEVELOPMENT ONLY** technical descriptions plus truthful **USER RUNTIME** limits. Supplement with `CLOUD_ARCHITECTURE.md`; do not rewrite facts to pretend remote services exist. |
| `BUILD_STATUS.md`, `docs/V2_BUILD.md`, `VERIFICATION.md`, `RELEASE_PREPARATION.md`, `RELEASE_NOTES.md`, `docs/releases/v0.2.0.md`, validation receipts and examples | Prior local build/release/browser evidence, download/manual preview instructions. | **DEVELOPMENT ONLY / historical evidence:** retain dated facts; current owner instructions take precedence. Final status records new evidence separately. |
| `prototype/README.md`, `prototype/Dot_World_Starter_Kit.md`, `prototype/Dot_World_Preview.html` | Preserved owner-supplied historical HTML research and local instructions. | **DEVELOPMENT ONLY / historical research:** not a supported onboarding path or current runtime; do not mutate the historical specimen to make a product claim. |
| Ignored `.tools/`, `.venv/`, `node_modules/`, native editor caches and private execution artifacts | Tool installs, machine paths, credentials possibly managed by the environment. | **DEVELOPMENT ONLY:** excluded from source/release artifacts. Neither evidence of owner requirements nor material to publish. |

No FFmpeg, local AI model, external SDK, rigging application or additional optional plugin is required by the delivered browser runtime. Future generator dependencies remain backend concerns and need capability-specific evidence.

## Remaining product gaps

The no-install owner documentation is implemented. Full service availability is a separate acceptance requirement: successful authenticated job submission, verified hosted world, private assets when required, durable account storage, cross-device restoration and device-specific browser testing. See [cloud architecture](CLOUD_ARCHITECTURE.md) for the interfaces and [BUILD_STATUS.md](../BUILD_STATUS.md) for actual run results. A deployment containing a moving generated character is stronger evidence than a successful build, but does not by itself complete authentication or persistence.

The current audit found browser-local persistence deliberately implemented, not an accidental hidden server dependency. Preserve it until the remote adapter is real. Never rename its status to “cloud saved” merely because its page came from a cloud host.
