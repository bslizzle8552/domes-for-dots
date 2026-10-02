# Dot-led authoring and recoverable expansion

**CLOUD BACKEND / DEVELOPMENT ONLY.** The commands and filesystem operations in this guide run inside an authorized operator's worker or contributor environment. These are executable source-authoring tools, not a deployed general self-service or autonomous world-creation service. Target owner flow: express preferences in ChatGPT and open a hosted URL, with no Python, manual JSON, repository clone or Godot installation. See the [owner guide](GETTING_STARTED.md) and [cloud architecture](CLOUD_ARCHITECTURE.md). Autonomous World Creator is the next major project; auth/storage is deferred until the complete world unit is defined.

V2 adds an executable path from a Dot's complete authored proposal to validated source content. The existing Godot world, character, asset, routine and brief formats remain the source of truth. There is no fixed menu of world templates and no model inference inside the authoring tool.

The owner supplies context and boundaries. The Dot interprets them, chooses a concept, records its choices in the brief, authors the required documents and assets, and prepares a concrete change request. The tool validates a candidate and records its effect before changing the working project. A build and real preview then establish whether the proposed home works visually.

## Artifacts and commands

Use the development Python environment with `requirements-dev.txt` installed. Commands run from the repository root. `--root PATH` may precede the command to target a separate checkout; this is useful for experiments.

| Artifact | Meaning |
| --- | --- |
| Proposal | Complete Dot-authored JSON documents, description and target identity. No source hash yet. |
| Change request | Proposal plus `base_content_hash`, bound to a reviewed source snapshot. |
| Plan | Derived operations, policy limits, geometry/schema checks and candidate hash. It grants no permission. |
| Transaction receipt | Applied hashes, backup location, status and rollback identity. Stored locally in ignored `artifacts/authoring/`. |
| Brief history | Durable authored explanation appended automatically on successful apply; preserved in exports. |

A proposal uses this envelope. Each `document` must contain its complete current schema-conforming content; the abbreviated `{}` below is only an envelope illustration.

```json
{
  "schema_version": 1,
  "id": "my_home_initial",
  "world_id": "my_home",
  "intent": "create",
  "description": "The Dot's chosen concept and reasons for this build.",
  "files": [
    {"path": "godot/content/worlds/my_home.json", "document": {}},
    {"path": "godot/content/briefs/my_home.json", "document": {}},
    {"path": "godot/content/routines/my_home.json", "document": {}}
  ]
}
```

Supply separate character and asset documents when needed. Existing reviewed resources may be referenced directly. New scenes/models must first be added and reviewed as ordinary project source; JSON requests cannot install scripts, copy arbitrary files, run commands or download anything. The tool updates the catalog from the supplied world's identity/title. It never edits another world's shared content through this request.

```powershell
python tools/world_author.py create artifacts/my-home.proposal.json --output artifacts/my-home.request.json
python tools/world_author.py plan artifacts/my-home.request.json --output artifacts/my-home.plan.json
python tools/world_author.py apply artifacts/my-home.request.json --output artifacts/my-home.applied.json
```

`create` prepares a request; `apply` performs the source change. `prepare` does the same snapshotting for an `intent: "expand"` proposal. Preparing a new request after source changed is a new review point: reread its diff rather than replacing the hash in an old request blindly. `plan` and `apply` both reject stale source hashes and both independently build and validate the candidate. A plan is not a substitute for validation at apply time.

Outputs inside the repository must be new files in `artifacts/`, outside the reserved `artifacts/authoring/` journal directory. Existing outputs are never overwritten. Outputs may also use a new path outside the repository. This prevents a mistyped report filename from replacing source content.

The complete [Lantern Archive pilot](../examples/authoring/lantern_archive/README.md) demonstrates full creation and subsequent expansion. A second small additive example prepares a telescope for Cedar Atelier without editing the current world:

```powershell
python examples/authoring/make_cedar_telescope.py --output artifacts/cedar-telescope.request.json
python tools/world_author.py plan artifacts/cedar-telescope.request.json
python tools/world_author.py apply artifacts/cedar-telescope.request.json
```

That addition creates a prop and reachable `observe` station. Existing routines remain unchanged; **Visit** or a MOCK custom activity can use the station. It does not create telescope optics or synthesize a new ongoing routine from a timer.

## Owner control and Dot freedom

The existing `owner_locked`, `dot_choice` and `shared_decision` sections retain their meaning. Expansion preserves the entire existing `owner_locked` dictionary exactly, including its optional `authoring_policy`. The tool also preserves existing history and appends its own entry. An `approved: true` field is rejected rather than treated as authority.

An owner can establish a structured policy when creating a world by storing a document matching [owner-policy.schema.json](../schemas/owner-policy.schema.json) at `owner_locked.authoring_policy`. Inspect the complete default with:

```powershell
python tools/world_author.py default-policy
```

| Policy | Enforcement |
| --- | --- |
| `autonomy` | `within_bounds` permits valid ordinary edits. `proposal_only` produces a reviewable plan and refuses apply. |
| `allowed_tools` | Must include `world_author` to use this tool. This does not control unrelated tools or grant them access. |
| `allowed_operations` | Checks derived additions, modifications, moves, removals, character replacement and presentation edits. Metadata cannot declare a different operation. Initial creation is checked against content budgets; operations govern later changes. |
| `destructive_actions` | Removal requires `allow` plus its corresponding allowed operation. `deny` and `require_owner_review` reject removal here. |
| Object/zone/station/asset/primitive counts | Bounds authored complexity; these are not measured frame-rate or GPU budgets. |
| `max_content_bytes` | Bounds target-world JSON documents, including its brief and referenced manifests; it excludes scene/model/texture binaries, native saves and exports. |
| `world_bounds` | Checks zone edges, spawn, station anchors and transformed declared object footprints in the X/Z plane. Meshes must have honest footprints; this does not inspect every imported vertex. |
| Forbidden tags/behaviors | Checks exact asset tags/categories and behavior identifiers. Free-form dislikes still require the Dot's interpretation and human review when ambiguous. |

Worlds without a structured policy use the printed default: ordinary reversible content edits are allowed, removals require separate review, and finite schema-scale budgets apply. Existing textual owner locks remain binding instructions even where software cannot interpret their prose. No extra chair-by-chair approval is introduced.

The tool does not authenticate an owner or prevent an agent with unrestricted filesystem access from bypassing it. For an explicit owner amendment, preserve a versioned backup, edit the brief in a separately reviewed source change, record the prior value and reason in history, validate it, and prepare subsequent requests from that new source. There is deliberately no `--owner-approved` bypass. Never infer an amendment from time passing, a JSON boolean, or an unresolved shared decision.

## Timeline compatibility

Compatible expansions preserve world ID/version, Dot name, character ID, routine ID, step order/IDs/activity tags/durations, cycle length, project order/IDs/activity tags/required seconds and all existing runtime saves. Keeping these stable retains the meaning of the saved epoch. World version is currently part of the runtime save identity, so this tool does not automatically bump it for compatible content additions.

The Dot can add/move/modify rooms, objects and stations; change decorations; supply a replacement character visual under its stable identity; and edit routine labels, animation semantics, station preferences and project presentation. Validation still checks animation contracts, relationships and reachability. A newly added station can be used manually or by a custom MOCK activity without rewriting the schedule.

Changing schedule timing, activity integration, project requirements or identity requires a deliberate new timeline. In this release, create a separate world/brief/routine identity using the revised complete documents. The new world receives a fresh save/epoch when opened; the original world's content and saves remain available. There is no general offline progress migration or automatic in-place reset. The rejection message explains this boundary. Copying the old save to a new name is not a supported migration.

## Apply, failure and recovery

Close Godot/editor builds and other content writers before apply. The authoring writer lock excludes another invocation of this tool, not an unrelated editor. A full candidate is validated first, copied onto the same filesystem, verified, and journaled. The current `godot/content` directory is renamed into the transaction's `before` backup; the candidate is then renamed into place and verified. The source hash is rechecked immediately before the swap.

This is a journaled recoverable two-rename operation, not a globally atomic filesystem transaction or power-loss guarantee. There can briefly be no `godot/content` directory between renames. No running viewer's loaded content or native/browser save is mutated. Restart/rebuild to load a successful expansion.

Ordinary failures attempt immediate guarded rollback. The receipt prints its `transaction_id`; use it to recover an interrupted operation or undo the latest compatible apply:

```powershell
python tools/world_author.py recover my_request-012345abcdef
```

Recovery verifies the backup hash and accepts only absent content, the exact applied candidate, or an already restored original. If the source contains later edits, it refuses to discard them. Recover newer transactions first, or preserve/merge those edits deliberately. An interrupted recovery is resumable when its displaced candidate and original backup verify. A killed process can leave the empty writer-lock directory; first close other authoring processes, then manually remove only `artifacts/authoring/write.lock` and rerun recovery.

Snapshots are limited to 16 MiB/4096 files, requests to 64 documents, and retained transaction directories to 10. At that limit, archive reviewed old receipts/backups elsewhere before another apply. Backups are not silently pruned. A transaction can retain both original and rolled-back candidate trees, so the maximum retained payload is approximately 320 MiB plus journals and a temporary candidate. Runtime saves and model binaries outside `godot/content` are not included in this backup: preserve the complete project separately when replacing those resources.

## Validation and launch

After apply, run `python tools/build.py`, inspect the actual world, visit changed stations, and check save/reopen on the intended platform. Candidate validation proves schema, resource references, policy, compatible identity and conservative planar reachability; it cannot prove pose quality, imported mesh cost, genuine native activity reporting or browser rendering.

The authoring tests use isolated temporary projects and exercise successful creation, compatible additions, immutable locks/history, source staleness, policy denial, shared resources, Windows case aliases, navigation failure, output-path mistakes, rollback at both swap boundaries, damaged backups, interrupted recovery and newer-edit conflicts. The [V2 build record](V2_BUILD.md) separates these checks from runtime and browser acceptance.
