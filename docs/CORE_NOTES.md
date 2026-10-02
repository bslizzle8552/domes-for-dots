# Core service semantics and verification

The three services in `godot/scripts/core/` are plain GDScript `RefCounted` classes. They do not depend on scene nodes, native ChatGPT APIs, model inference, or any named example world. The runtime must validate content and retain configuration independently from runtime state.

## Simulation

`Simulation.evaluate(routine, epoch, now)` is pure. It integrates the duration of each activity tag over complete routine cycles, then integrates one partial cycle. Runtime cost depends on the routine and project count, not elapsed days. The current step changes at its exact boundary; the cycle wraps to its first step. Time before the epoch clamps to zero.

Each finite project earns the elapsed seconds matching its activity tag. Projects sharing a tag advance in parallel, by design; this is imagined progress rather than evidence of model work. `progress` is a fraction from 0 through 1, clamped permanently at completion for a fixed epoch. The stage is selected from equal progress intervals, with the last stage retained at completion. Changing project requirements or the routine changes the derived answer: migrations must be intentional.

Viewers calculate from the same persisted epoch. Repeated evaluation never writes counters, so opening additional viewers cannot multiply earned progress. The state stores project identities; content stores their finite requirements. Arbitrary elapsed time is calculated directly, without animation replay or continuous model inference. A preview must pass a temporary `now` and never save an altered epoch.

## Activity leases and source authority

`configure(world_id, character_id)` resets one session. `apply(event, now, trusted_source="mock")` requires the event's source to exactly equal a source whose authority the caller has already established. Passing a source string is not authentication. The public browser bridge must always use the default `mock`; exposing `trusted_source` to callers would defeat this boundary. No real activity adapter ships in these services.

Events have exactly the fields in `IMPLEMENTATION_CONTRACT.md`. Sequences must be positive integers, monotonically increasing separately for each source and kind. Timestamps must be finite, nonnegative, and nondecreasing in a stream. Events more than five seconds in the future are rejected. Start/renew TTLs are greater than zero and at most 60 seconds; END may use zero. Expiry is `timestamp + ttl_seconds`, rather than receive time plus TTL. Already expired starts/renewals are rejected.

Only a matching, live activity can renew. A newer start can replace a different activity in the same stream, tombstoning the replaced activity. END tombstones an activity even if its START has not arrived. Expiry also tombstones. A later higher-sequence event cannot restart an ended/expired activity identity: adapters must allocate a new activity ID. An END for another activity never cancels the current one.

Identical event IDs and payloads are accepted as duplicates without changing the lease. Reusing an event ID with a changed payload fails. The most recent 2,048 fingerprints are cached; older duplicate events still cannot bypass stream high-water checks. Tombstones and stream high-water values remain for the session. They are intentionally not pruned in a way that would allow resurrection. A future long-lived real adapter should own durable deduplication and authenticated resynchronization; page reload resets this in-memory session protection. Short timestamp-based TTLs still bound replay lifetime across reloads.

Calls have visual priority over work. Among simultaneous leases of one kind, newest timestamp wins, with event ID as a deterministic tie-break. Ending a call reveals still-valid work. No activity result asserts that a native call or actual work occurred; only the optional authenticated adapter could provide that evidence.

## State persistence

`StateStore.new(storage_root="user://state", storage_namespace="domes-for-dots.v1")` allows isolated tests and future adapter replacement. Its public interface is `initial_state`, `load_state`, and `save_state`. `validate_state(state, world_id)` returns an empty string when valid or an error code. The store checks exact versioned fields, safe identifiers, target identity, finite numbers, integer revisions, distinct project IDs, JSON-only preference values, nesting/collection limits, and a 256 KiB serialized size limit before writes. Runtime must additionally compare loaded world version, character/routine identities, and project IDs against currently selected content, since the store has no content registry.

Initial revision is zero; a successful save increments it. The caller must retain the returned state and pass its revision to the next save. A stale expected revision returns `revision_conflict`. A missing state returns `ok: true, found: false`. Corrupt state with no valid backup returns `ok: false`; it is never silently reset. If primary is missing/corrupt and backup validates, load returns `ok: true, found: true, recovered: true` and a nonempty `error` containing a human-readable recovery warning. The UI should display that warning. Saving this recovered snapshot repairs primary and retains the good backup.

Native files live at `user://state/<world-id>.json`, with `.bak` backup. Saves acquire an exclusive directory lock for that world, re-read the current revision, write and verify a temporary candidate, establish a verified backup, then replace the primary and verify the resulting bytes. A crash during replace can leave primary absent, but a validated backup remains. This uses Godot file flush and explicit recovery; it is not a claim of filesystem-level transactions or power-loss-proof durability. A stale `.json.lock` left by a killed writer fails closed with `writer_busy_or_stale_lock`. Close all viewers before removing that world's empty lock directory manually. There is no automatic stale-lock eviction that could unlock a live writer.

Browser state uses synchronous `JavaScriptBridge` calls to origin-local `localStorage`. Keys are `domes-for-dots.v1:<world-id>` and the same key plus `.bak`. Storage access/quota errors are reported. The browser path validates current state, compares the exact previously read primary bytes, writes the validated backup first, writes the candidate, then checks the candidate bytes. These operations execute synchronously in one JavaScript task in that viewer.

**Browser concurrency limit:** localStorage does not offer atomic compare-and-swap across tabs/processes. Optimistic revision checks catch ordinary stale saves, but simultaneous cross-tab writers can both pass and one may overwrite the other. Use one writing tab in v0.1; other viewers can calculate from the shared epoch without saving. No cross-tab linearizability guarantee is made. A future asynchronous Web Locks adapter or hosted authoritative transactional adapter is required for stronger multi-writer guarantees. Do not store credentials in preferences, content, or exported state.

## Verification

Run from the repository root with Godot 4.5.1:

```powershell
& '.tools/godot/Godot_v4.5.1-stable_win64_console.exe' --headless --path godot --script res://tests/test_core.gd
```

The native deterministic suite exercises cycle/step boundaries, complete cycles plus remainder, large absences, finite project completion, repeatable evaluation, non-mutating content, clock bounds, lease expiry, idempotency, payload collisions, source/target validation, sequence/timestamp ordering, delayed START after END, renewal constraints, call priority/resumption, revision conflicts, strict import validation, native writer exclusion, known-good backup recovery, and corrupt-state refusal. It uses an isolated `user://core-test-*` directory and removes its own files. Native tests do not verify browser localStorage, browser exports, real adapter authority, real calls, or physical character motion; those require separate acceptance evidence.

The separate production-runtime suite instantiates `scenes/main.tscn`, injects an isolated state directory before `_ready`, and uses actual Godot navigation queries and `CharacterBody3D.move_and_slide` physics:

```powershell
& '.tools/godot/Godot_v4.5.1-stable_win64_console.exe' --headless --fixed-fps 60 --path godot --script res://tests/test_runtime.gd
```

It checks all 49 Cedar Atelier and 36 Tidal Observatory station pairs, physically visits every station and returns to the first, samples character clearance against transformed physical box colliders throughout movement, and verifies unreachable targets leave the resident idle. It then replaces the character definition and visual scene with `tests/fixtures/replacement.tscn`, which has different geometry and named `AnimationPlayer` clips, and checks orientation, scale, actual animation transforms, fallback behavior, and navigation without an engine fork. `--fixed-fps 60` removes wall-clock pacing while retaining actual physics callbacks; it does not manually call motor physics. Runtime readiness waits for the new navigation region to own the spawn point, with a five-second wall-clock failure bound, rather than assuming a fixed count of frames completes asynchronous navigation synchronization.
