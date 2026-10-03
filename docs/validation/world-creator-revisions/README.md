# Generated-world revision evidence — 2026-10-02

[`receipt.json`](receipt.json) is the complete final local acceptance receipt, copied unchanged from `artifacts/world_creator/revisions-final/revision-acceptance.json`. SHA-256: `4bb90668733dfe8c88acbf0cd43d53c6deb6c9e956c94bbebddcd04bfb0d5934`.

**VERIFIED:** the reusable narrow-operation adapter stages and validates changes to the generated two-level **Lumen Observatory**, preserves its protected keepsake and a synthetic owner-moved/pinned lamp, rejects stale candidates, restores the previous structure without overwriting subsequently updated runtime-state sentinel data, and recovers exact known-good content after an injected installation failure. The original composed source remains unchanged.

This receipt proves local schema/content/navigation and filesystem transaction behavior. It does not claim browser locomotion, a hosted D1 transaction, real human activity, or automatic recovery from every possible Godot failure. Runtime and private Site acceptance have separate receipts.

## Source identity

The source was freshly composed after LF-stable package regeneration, using all three checked-in World/Character Package pairs. Lumen's immutable seeds are:

| Input | SHA-256 |
| --- | --- |
| `examples/world_creator/lumen_observatory.world/package.json` | `2f95f0c693ff0ef8f7fb994d8a7572fe38d0d0d52108eb38d84e44b561bfe359` |
| `examples/world_creator/lumen_observatory.character/package.json` | `55d839ad1822d712d7981337c7fc4049bf6bdc5b6c0da100715545f6bf1fcd28` |
| Fresh composed source content tree | `9b8b561208ea49ab7bd7acf29bf12f5fa0b0fc06933d9c8f69a2a2fde57df246` |

The receipt records the original absolute paths from this Windows run. Their repository-relative equivalents are below. Compiler packages remain immutable; the independent runtime snapshots explicitly record postcompile revision provenance.

## Snapshot sequence

All directories are under `artifacts/world_creator/revisions-final/`, with `schemas/`, `godot/` and `snapshot.json` ready for separate export or Site registration.

| Directory | Structure revision | Change | Content-tree SHA-256 |
| --- | --- | --- | --- |
| `base` | 1 | Generated world plus clearly labeled synthetic owner lamp fixture | `700bd9dce580f60e46863b9df96310a7cdef651781675519a4086900a5fedd8a` |
| `furniture` | 2 | Moves `activity_0` by 10 cm and preserves its station anchors | `9954aeb971b99be7187297b935d5902ba43643d65909498e44608237d933b2c2` |
| `addition` | 3 | Adds `revision_field_lamp` and reachable inspection station | `0d8dba26438f965d9f0145a22f6a0a194a83b0b99b4ab77bced76b8b23af4fe3` |
| `structural` | 4 | Adds connected observation deck, lamp and reachable inspection station with explicit state migration | `6f33d8a8e8bd530201f997fd56857480505382c959e21e16116813310f244808` |

The final `working/` tree has been rolled back to revision 3. Its independent state sentinel advanced simulated journal progress from 17 to 23 after structural activation; rollback and the later injected failure preserved that newer value. The receipt retains original transaction IDs and authoring checks. The checks run against the real content/navigation validator, not mocked success reports.

## Reproduce

These are developer/cloud-worker commands; owners do not need this toolchain. Use fresh destination names because packages and acceptance outputs reject overwrites.

```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'tools'); from pathlib import Path; from world_composer import compose_many; p=Path('examples/world_creator'); names=['ember_foundry','lumen_observatory','verdant_courtyard']; print(compose_many([(p/(n+'.world'),p/(n+'.character')) for n in names],Path('artifacts/revision-reproduction-source')))"

.\.venv\Scripts\python.exe tools/world_revision_acceptance.py `
  --source artifacts/revision-reproduction-source `
  --world-id lumen_observatory `
  --output artifacts/revision-reproduction
```

The runner independently verifies all seven acceptance checks and writes its new receipt. Transaction IDs are intentionally unique. Expansion-history dates and future source changes can alter snapshot hashes across runs; the recorded hashes identify this exact run rather than promising time-independent transaction output.

## Focused safety coverage

Final focused results on 2026-10-02:

| Suite | Result | Recorded duration |
| --- | --- | --- |
| `test_world_revisions.py` | 23 passed, no skips | 53.658 s |
| Existing `test_authoring.py` | 22 passed, no skips | 31.084 s |
| `test_world_site_prepare.py` | 16 passed, no skips | 12.939 s |

The revision tests exercise object/field locks, indirect asset/support mutation, local station anchors, blocked/overlapping/disconnected geometry, explicit migration, stale bases before and after validation, newer-content rollback conflicts, and exact known-good recovery. The existing authoring suite additionally covers shared resources, budgets, immutable owner policy/history, routine meaning, damaged backups and interrupted recovery.

The Site preparer boundary tests cover revalidation instead of trusting receipts, code-bearing assets, source/export/output links and junctions, complete preflight before output, changed source bytes after validation, owner-policy bypass attempts, immutable registered revision IDs, retained rollback history and safe prefix extension. Link detection is injected in these unit tests so Windows symlink privileges do not turn the guard tests into skipped cases; these are not claims that live filesystem junctions were created.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_world_revisions.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_authoring.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_world_site_prepare.py -v
```

See [the revision contract](../../WORLD_REVISIONS.md) for supported operations, owner protections, the identity-preserving migration, local rollback semantics and hosting boundaries.
