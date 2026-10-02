# Development and release tools

These Python tools run locally and do not install Godot, publish a repository,
deploy a site, create accounts, or grant access. Use Python 3.12 and install
`requirements-dev.txt` in a development environment.

| Tool | Purpose |
| --- | --- |
| `validate_content.py` | Strict schema, reference, character and planar navigation checks. |
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
always requires both Godot core and runtime test suites to have passed.

Source and Web ZIP files have stable file timestamps and are CRC-verified after
creation. `SHA256SUMS` identifies the resulting bytes; build/release manifests
record version and verification evidence without local absolute paths. A secret
scanner catches recognizable patterns, not every possible credential format;
review unfamiliar content and assets before release.
