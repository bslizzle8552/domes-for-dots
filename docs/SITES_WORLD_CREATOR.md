# Private Site World Creator adapter

This is an operator experiment for one synthetic world per owner-private ChatGPT Site. The existing Godot browser runtime remains the renderer and simulator. Sites dispatch supplies private access, D1 stores durable state, and content-addressed static JSON supplies approved primitive geometry. The owner visits a link and installs nothing. A general conversation-to-provisioned-world service is not deployed.

## Build and publish

1. Use the [cloud operator pipeline](OPERATOR_WORLD_CREATOR.md) to compile Character/World packages and export the shared runtime. Obtain a successful worker receipt and verify its exported file hashes.
2. Copy `cloud/world_site` into a fresh operator checkout, outside the source checkout's tracked files. Install its pinned lockfile with the Sites plugin's portable setup helper. Register a **new owner-private Site** and bind D1 as `DB` in `.openai/hosting.json`. Never reuse an unrelated resident's Site.
3. Produce owner-policy-checked revision snapshots using `tools/world_revision_acceptance.py` for the synthetic proof or `tools/world_revisions.py` for a reviewed supported change.
4. Run `python tools/world_site_prepare.py --site SITE_CHECKOUT --web REVIEWED_EXPORT --revision BASE_SNAPSHOT --revision NEXT_SNAPSHOT --world-id lumen_observatory`. Supply the same immutable prefix when extending a registry. All schemas, relationships, owner locks, path boundaries, migration declarations and source hashes must validate before output. Rebinding or omitting an existing registered revision is rejected.
5. Generate D1 migrations for deliberate schema changes. Use the Sites plugin's source workflow, build, package and private deployment tools. The source checkout, source commit, version and deployed URL are distinct from the GitHub feature branch. Never put credentials in source, browser data, shell arguments or receipts. Windows plugin packaging requires Git Bash on PATH and `TAR_OPTIONS=--force-local` for drive-letter archive paths.
6. Run the real-browser/API harness `tools/world_site_acceptance.cjs`, setting `DOMES_SITE_URL`, `DOMES_SITE_OUTPUT` and `PLAYWRIGHT_MODULE`. For explicitly available scoped service access, `DOMES_SITE_READ_STDIN=1` reads a credential through hidden terminal input. Normal owner login is a separate acceptance target.

The reusable scaffold intentionally has no registered project ID, runtime binaries, world registry, credentials or saved state. Its bundled framework carries its original licenses. The completed synthetic deployment and exact observations are recorded in the [completion report](../AUTONOMOUS_WORLD_CREATOR_COMPLETION_2026-10-02.md).

## Runtime data lane

The operator validates a complete World bundle, registers its SHA-256 and publishes the JSON at `/world-data/<sha256>.json`. The bridge fetches only same-origin registered paths, verifies their hash and 2 MiB bound, then supplies the bundle before Godot loads. Runtime checks allow bounded primitive recipes, unchanged bundled character/routine identities and known behavior labels. The same PCK can render changed objects, stations, supported floor levels and straight ramps. Characters, models, scripts, shaders or new behavior implementations require the code/build lane; arbitrary runtime PCK/GLB installation is not implemented.

The approximately 38 MB uncompressed engine is packaged as a 9.24 MB gzip static asset. The loader checks gzip magic because a host may transparently decompress it. No external asset origin, private original art or remote executable world content is used. Static assets were exercised; R2 remains untested. Static publication still creates a Site version even when the engine pack is unchanged.

## Durable state and revisions

D1's `domes_world` row separates `state_revision` from `structure_revision` and a monotonically increasing `activation_serial`. Save updates compare the expected state and active structure; only one concurrent writer succeeds. Acknowledgment must arrive before Godot displays a successful save. If the owner changes a preference while a save is pending, the newer preference is retained and submitted against the acknowledged revision. Server errors/conflicts are visible and never relabeled as success.

Compatible structure updates retain the epoch, character/routine/project identities and preferences; transient navigation is reconstructed from a supported spawn on reload. Activation compares both structure revision and activation serial. The serial prevents an old request becoming valid again after rollback returns to an earlier structure number. Rollback points to the previously active registered bundle and leaves unrelated state alone. The server accepts a small explicit operation set, bounded JSON, same-origin browser mutations and registered revision targets.

Client preflight download/hash failures leave the active pointer unchanged. Once a valid candidate is activated, a later Godot scene-initialization failure requires the visible recovery action; there is no automatic two-phase scene-health transaction. D1 outage prevents successful save acknowledgment and does not erase the existing row. A deployment missing its active registered revision fails explicitly. Public/multi-tenant authorization, conflict merging, general state migrations and a job service are outside this adapter.

## What the acceptance means

The harness verifies anonymous gating, D1 initialization, concurrent-write rejection, epoch protection, real Godot loaded geometry/clips, in-flight preferences, fresh isolated-browser restoration, multilevel station arrival, structural activation/new-station use, stale candidates, rollback and unchanged PCK bytes. With service access, Chromium's worklet requests bypass page routing, so the harness fetches the two reviewed same-origin audio-worklet modules with authentication and executes identical bytes through Blob URLs. This is a disclosed headless test transport, not owner sign-in UI or audio-feature acceptance. Credentials are confined to the selected origin and hidden input; no browser profile or authentication headers are recorded.

An optional read-only `read_world_state` WebMCP registration is feature-detected. Its absence does not affect the world. Native ChatGPT calls, actual work events, general model-driven autonomous changes and unsupported browser WebMCP are not implied. All resident routines remain **SIMULATED**, and explicit test events remain **MOCK**.
