# Guarded World Creator revisions

`tools/world_revisions.py` adds narrow data operations to the existing `world_author.py` plan/apply/recovery workflow. It does not recompile the whole creative brief or replace a compiler package. A validated World Package remains an immutable seed; subsequent runtime-bundle edits retain its optional SHA-256 provenance and record what changed.

The implemented local adapter is an operator tool. It supplies an exclusive filesystem writer lock and guarded recovery, **not** an authenticated service or distributed database transaction. Owner-side development software is not a product requirement: the operator/cloud worker performs this work. The separate Site adapter owns hosted activation, access control and durable state.

## API and data operations

```python
from pathlib import Path
from tools.world_revisions import prepare_revision, plan_revision, apply_revision

root = Path("artifacts/world_creator/revisions-v3/working")
request = prepare_revision(
    root, "lumen_observatory",
    [{"op": "move_object", "id": "activity_0",
      "position": [-2.0, 0, -2.2], "rotation_y": 0}],
    reason="Make room around the reading station; retain the owner's lamp.",
    request_id="reading_adjustment",
)
plan = plan_revision(root, request)  # Isolated validation; no active replacement.
receipt = apply_revision(root, request)  # Rebuilds and revalidates under the lock.
```

Coordinates above are illustrative; the compiler/validator must approve actual placement for the selected world. The module rejects nonfinite values, duplicate entity IDs, unknown operations, arbitrary request fields and executable asset scenes. It accepts:

| Operation | Required fields | Behavior |
| --- | --- | --- |
| `add_object` | `entity` | Adds a complete bounded runtime object using a referenced asset. |
| `move_object` | `id`, `position`, `rotation_y` | Moves one object and transforms its attached station approach/interaction anchors and facing by the same rigid transform. |
| `modify_object` | `id`, `changes` | Changes `asset_id` and/or `scale`; resizing also preserves station anchor relationships in object-local axes. All content/fit/navigation checks rerun. |
| `add_station` | `entity` | Adds one explicit runtime station with supported action/fallback. |
| `add_zone` | `entity` | Adds one support zone; center circulation must remain reachable and new support cannot overlap existing same-height floors. |
| `add_level` | `entity` | Adds a supported level, accompanied by valid support and connectivity in the same candidate. |
| `add_transition` | `entity` | Adds a registered runtime transition, subject to width, headroom, support and navigation validation. |
| `add_asset` | `manifest_path`, `entity` | Adds original procedural parts to an already referenced world-owned manifest. Imported binaries go through package/asset validation instead. |
| `decorate` | `environment` | Replaces the bounded environment palette/light settings. |

Operations run in supplied order. References may be resolved by later operations in the same candidate, but the complete candidate must validate. Asset manifests shared by another world remain protected by `world_author`. Existing policy limits still control tools, allowed operations, primitive/content budgets, world bounds and forbidden behaviors. Transition/level edits are explicit policy operations, rather than being classified as decoration.

New physics, executable behavior, arbitrary scripts/URLs, locomotion types, changed routine meaning, and schema migrations belong to a reviewed code/build/test lane. This adapter supplies no approval flag or permission override.

The CLI accepts a proposal with `world_id`, `operations`, `reason`, `request_id`, and optional `state_migration`/`source_package_hash`:

```powershell
.\.venv\Scripts\python.exe tools/world_revisions.py --root <composed-repo> prepare <proposal.json> --output <request.json>
.\.venv\Scripts\python.exe tools/world_revisions.py --root <composed-repo> plan <request.json>
.\.venv\Scripts\python.exe tools/world_revisions.py --root <composed-repo> apply <request.json> --output <receipt.json>
.\.venv\Scripts\python.exe tools/world_revisions.py --root <composed-repo> rollback <transaction-id>
```

Output files use the existing exclusive-create authoring rules. A repository-relative report belongs under `artifacts/` outside the reserved transaction directory. Existing reports/source cannot be overwritten through `--output`.

## Owner edits and meaningful objects

Stable IDs and narrowly derived edits preserve every unrelated field from the authoritative current base. An earlier candidate cannot replay old object positions after an owner change: its content hash becomes stale.

Protected fields live inside the existing immutable creative-brief boundary:

```json
{
  "owner_locked": {
    "entity_protection": [
      {
        "kind": "object",
        "id": "owner_lamp",
        "fields": ["*"],
        "chosen_by": "human",
        "reason": "The owner moved and pinned this reading lamp."
      }
    ]
  }
}
```

Supported kinds are `object`, `zone`, `station`, and `transition`. `fields` is `['*']` or a nonempty list of existing top-level entity fields, for example `['position']`. `chosen_by` records human, Dot, collaborative or compiler provenance; it grants no authority. Private chat transcripts are unnecessary.

A fully protected object pins its placement, dimensions and asset identity, the referenced asset document, and its associated station meaning. Its support must persist at the same elevation; harmless floor growth remains possible. An asset recolor/hidden replacement or a floor moved away from the object cannot bypass the lock by leaving the object JSON unchanged. Partial field locks preserve exactly the named fields and entity identity.

`world_revision_guards.py` is called from **every** `world_author.prepare_candidate` path, including legacy complete-document requests. A caller cannot bypass these protections by skipping the narrow adapter. Owner-lock changes require the separately reviewed owner-amendment path already described in `WORLD_AUTHORING.md`; a model-authored `approved: true` has no effect. Direct filesystem editing remains outside the tool's authority boundary.

## Candidate and revision identity

Each candidate records its exact base content SHA-256, active structure revision and revision ID, reason, narrow operations, state migration and optional source package hash. The request is strict and contains no arbitrary file replacement list.

The candidate is reconstructed from the current source at plan and apply. `world_author` then validates schema, paths, resources, policy, collision/navigation, owner locks and routine identity; it rechecks the source hash immediately before installation. A cached `status: passed` receipt never substitutes for validation. Concurrent changes produce `stale_revision`/`stale_request`; there is no silent rebase.

`world.metadata.revision_state` records:

- New structure revision and stable revision ID, plus parent revision ID.
- Source content and immutable compiler-seed package hashes.
- Reason, operation provenance and affected/protected entity IDs.
- Explicit migration and prior known-good revision/hash rollback reference.
- `compiled_seed_modified: true`, so edited output is not represented as exact compiler seed output.

The common `world.metadata.structure_revision` is updated alongside this detail. Generated seeds retain their compiler-provided starting revision; legacy unversioned worlds start at zero. Revision bookkeeping does not require extra decoration authority for an otherwise permitted move.

## Compatible state migration

Every zone/level/transition addition requires this explicit bounded migration:

```json
{
  "strategy": "preserve_existing_ids_and_routine",
  "routine_id": "the_existing_routine_id",
  "reset_transient_navigation": true
}
```

The supported operations never remove existing IDs or change routine timing/project semantics. Existing epoch, preferences and meaningful progress therefore retain their interpretation. The local tool never reads or writes native/browser/runtime save files. Its receipt declares the preservation strategy; a runtime/hosting adapter must re-resolve transient navigation when it activates the new structure. The declaration is not itself a cloud state migration or proof that an already open browser has reloaded.

Changing routine duration, required project work, persistent entity removal/remapping, or schema meaning is intentionally unsupported. Those changes need an explicit reviewed migration beyond this identity-preserving contract.

## Recovery and rollback

Activation uses the original `world_author` journal, validated candidate, exact before-tree backup, filesystem writer lock and content hashes. Errors after either swap boundary trigger guarded known-good recovery. Interrupted recovery can be retried through the existing journal.

`rollback_revision(root, transaction_id)` restores the previous content tree and asset references only if the active content still matches that transaction's candidate. It refuses to discard newer owner/Dot edits, and it rejects missing or corrupted backups. Runtime state remains separate; progress written after the structural revision survives rollback.

Local rollback reactivates the original prior structure revision/ID rather than inventing a new monotonically increasing revision. The retained transaction journal records recovery. Hosted D1 activation can instead allocate monotonic activation revisions while referencing the retained immutable structure. These are different counters and should not be conflated.

The existing bound of ten retained filesystem authoring transactions still applies. Backup archival/retention remains an operator action. This local rollback does not claim to reverse a Site deployment or database migration.

## Reproducible generated-world acceptance

```powershell
.\.venv\Scripts\python.exe tools/world_revision_acceptance.py `
  --source artifacts/world_creator/stage `
  --world-id lumen_observatory `
  --output artifacts/world_creator/revisions-v3
```

Use a fresh output directory for a rerun. The source is read-only. The runner creates a synthetic owner-moved/pinned lamp and preserves existing protected compiler objects. It writes independent composed-repository snapshots at `base`, `furniture`, `addition`, and `structural`; each includes `schemas/`, `godot/`, `snapshot.json` and the exact authoring receipt when applicable. These can be exported or registered by a separate trusted Site adapter.

The phases exercise one ordinary furniture move, a meaningful inspection object/station, and a connected deck with its own reachable inspection station and explicit migration. The runner then rejects a stale candidate, rolls back the deck while preserving subsequently increased runtime progress, injects an installation failure and verifies known-good recovery, and checks that its original source is unchanged. `revision-acceptance.json` records results and snapshot paths/hashes.

This is static content/navigation and filesystem transaction acceptance. Browser locomotion, private hosting, D1 durability and scene activation require the separate runtime/Site evidence. The synthetic lamp fixture is not represented as a real human action or a change to a private existing world.

Unit regression command:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_world_revisions.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_authoring.py -v
```

Coverage includes protected field/asset/support preservation, transformed station anchors, allowed-scope policy, unreachable/overlapping additions, schema/data boundaries, seed revision continuity, stale base both before and after validation, newer-content rollback conflicts, progress preservation, and injected activation failure recovery.
