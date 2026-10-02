# Development and release tools

These are contributor/cloud-operator tools, never owner setup instructions.
Use Python 3.12 and `requirements-dev.txt` in that environment. Most validation
tools are local; `setup_cloud_godot.py` explicitly prepares an ephemeral Linux
worker, `character_request.dispatch` submits authenticated cloud work, and
`publish_pages.py` explicitly publishes a verified public synthetic proof.

| Tool | Purpose |
| --- | --- |
| `character_factory.py` | Generic package orchestration, registered producer dispatch and isolated test-template installation. |
| `character_contract.py`, `character_package.py` | Shared schema/digest helpers and generic bounded envelope/identity/file/asset checks, then mandatory backend validation. |
| `character_backends.py` | Explicit trusted-code producer registry; unknown labels fail closed. |
| `procedural_character.py`, `factory_glb.py` | Strict current robot specification/rig/clip/engine acceptance and unchanged geometry/animation emitter. |
| `character_request.py` | Bounded reference/spec transport and authenticated operator workflow dispatch. |
| `cloud_worker.py` | Recorded production/import/motion-validation/Web-export stages. |
| `setup_cloud_godot.py` | Linux CI-only pinned engine/template bootstrap with upstream hash verification. |
| `publish_pages.py` | First public demo publication from an exact succeeded-job file inventory; never overwrites an existing proof branch or different Pages source. |
| `factory_browser_acceptance.cjs` | Real navigation, changing bone poses, imported clips and reload behavior in local or hosted Web export. |
| `validate_content.py` | Strict schema, reference, character and planar navigation checks. |
| `world_author.py create/prepare/plan/apply/recover` | Validate complete Dot-authored proposals, enforce existing locks/policy, detect stale bases and retain recoverable originals. See [World authoring](../docs/WORLD_AUTHORING.md). |
| `build.py --godot PATH` | Verify Godot 4.5.1, validate content, run Python and actual Godot tests, and export Web into `dist/web`. |
| `serve.py --port 8060` | Serve a built Web preview on loopback; see its `--help`. |
| `check_release.py` | Scan Git-tracked source for obvious credentials, private home-directory paths and accidental build/cache/state files. |
| `check_release.py --include-untracked` | Include nonignored pre-staging candidates in that scan. |
| `package_release.py` | Package clean tracked source and its matching verified Web build under `dist/release`. |

`build.py` accepts `GODOT_BIN`, a local `.tools` installation, or a Godot executable
on PATH when `--godot` is omitted. Matching Web export templates must already be
installed. All commands fail on nonzero exit status, and Godot steps also fail on
`ERROR:` or `SCRIPT ERROR:` even when the engine exits with status zero. Test
scripts must print their success summaries. Logs stay under ignored `artifacts/`.
A failed staged build preserves the previous `dist/web` output.

For normal release preparation, run the build, inspect its browser preview, run
the hygiene scanner, commit reviewed source, and run `package_release.py`.
Packaging verifies every exported file and compares the runtime source hashes
with the tested build; documentation-only changes do not require another export.
The source archive contains only Git-tracked files. No cache, toolchain, ignored
local state or Git metadata is added. Staged changes count as dirty until committed.
Building the extracted source archive does not require Git; the build records
`source_commit: "source-archive"` and unknown (`null`) dirty status. Final release
packaging still requires a Git checkout with reviewed tracked files.

`--allow-dirty` permits an explicitly labeled candidate package. It does not add
untracked source or bypass hygiene, hash or test checks. The build's
`--allow-missing-runtime-test` supports early development only; final packaging
always requires Godot core, runtime and character test suites plus the loaded-scene character audit to have passed.

Source and Web ZIP files have stable file timestamps and are CRC-verified after
creation. `SHA256SUMS` identifies the resulting bytes; build/release manifests
record version and verification evidence without local absolute paths. A secret
scanner catches recognizable patterns, not every possible credential format;
review unfamiliar content and assets before release.
