# Activity events

An event is a short-lived claim about actual activity, or a clearly marked mock for testing. It only changes the character's displayed action. It does not start work, connect a call, carry audio or grant access.

The shipped engine accepts MOCK events through its public test path. **Real work and native-call adapters are unavailable.** A future adapter must authenticate its source independently of the event JSON.

## Contract

[`activity.schema.json`](../schemas/activity.schema.json) represents `work_start`, `work_renew`, `work_end`, `call_start`, `call_renew` and `call_end` as `kind` plus `operation`:

```json
{
  "schema_version": 1,
  "event_id": "mock-event-001",
  "activity_id": "mock-work-001",
  "source": "mock",
  "sequence": 1,
  "kind": "work",
  "operation": "start",
  "timestamp": 1790899200,
  "ttl_seconds": 30,
  "world_id": "cedar_atelier",
  "character_id": "moss"
}
```

The timestamp above is an illustrative Unix-seconds value. Replace it with the current time when testing; replaying this example later must be rejected as expired. TTL is measured from event time, never from delayed receipt. Leases are bounded to at most 60 seconds. Future timestamps beyond the allowed five-second skew are rejected.

V2 adds an optional `activity_tag` to `kind: "work"` events, for example `"activity_tag": "garden"`, `"activity_tag": "map"`, or another tag authored on a world station. Omitting it preserves the original `work` station routing. The tag must use a lowercase identifier and stay unchanged across renewals of the same activity. Begin a new activity identity to change it. Call leases cannot set this field and retain priority over every work activity. END may omit the tag.

The public runtime checks that a supplied tag has a station in the current world and rejects unknown tags. **MOCK selected activity** demonstrates the same custom-tag route using the world's authored activities. It remains a visual test; it neither starts actual gardening nor invokes a model or tools. **End work** ends a selected custom activity, since it uses the same bounded work lease.

`event_id` is globally unique for a submitted message. `activity_id` identifies one lease lifecycle and must not be reused after end/expiry. `sequence` increases within a source/kind stream, including new activity IDs. Persist that ordering at the real reporter if a transport later reconnects.

## Required behavior

| Case | Result |
| --- | --- |
| Duplicate event ID | No repeated effect. |
| Older/equal sequence | Rejected; it cannot replace newer state. |
| Delayed already-expired start | Rejected rather than assigned a fresh lease. |
| Renewal after end/expiry | Rejected; use a new activity ID and newer sequence. |
| END arrives before an older START | Tombstone/high-water protection prevents resurrection. |
| Missing END | Lease expires and relinquishes control. |
| Call and work are both valid | Call has visual priority. |
| Call ends while work is still valid | Work can resume for its remaining lease. |
| Work has an authored custom activity tag | Use that tag's station; call priority and all lease protections remain. |
| Renewal changes the activity tag | Rejected; use a new activity identity. |
| Unknown target or untrusted source | Rejected. |
| No valid activity | Show the labeled simulated routine. |

Activity state is temporary and separate from persistent world content. World switching clears that world's test activity display. A time-preview control only offsets simulation; mock expiry continues to use real time. Deduplication and tombstones currently last for the runtime session; reloading resets them. Timestamp-based expiry still bounds replay lifetime, but a future real adapter needs durable sequencing/deduplication and authenticated resynchronization across sessions.

The read-only `domesSnapshot.resident` object separates `current_activity` and `previous_activity` from `animation`, navigation `phase`, `target_station`, `target_object`, and `current_location`. A walking character can already have the activity tag `garden`, but its current station stays empty until actual arrival. `last_arrived_station` records history, not a claim that the character remains there. Activity start times survive lease renewal and a call interruption. The scheduled routine continues beneath overrides; resuming it uses its authored timeline. Snapshots are session observations and are not persisted or replayed as real activity. `clock: "simulation_preview"` marks a previewed routine timestamp.

**Pause autonomous movement** stops the routine's navigation, while explicit manual visits and MOCK events may still move the character. It does not pause elapsed-time imagined project calculation. Save persists this owner preference; no mock activity or physical position is saved. Ending an override returns to the paused display until the preference is cleared.

## Adapter boundary

The GDScript store exposes `configure(world_id, character_id)`, `apply(event, now, trusted_source)` and `active(now)`. The `trusted_source` parameter is caller authority, not a value copied from untrusted event data. A real adapter needs an authenticated transport, allowed target mapping, clock policy, monotonic sequencing, health status and test evidence. Do not allow a browser import or `source: "real"` to establish identity.

Connection health and current activity are different. A connection may be healthy while no activity is reported. A stale lease means unknown current activity, not evidence of continuing work. Minimize payloads: IDs, bounded time and kind are enough; transcripts, call audio, prompts and work titles are unnecessary here.

## Native call visualization

The intended path is an existing native ChatGPT call, an optional verified report, then movement to a suitable station and a visual pose. The world never answers the call. No second agent, telephony service or audio integration is part of this engine.

If a real reporting route becomes available, record native answer time, receipt time, station arrival and visual pose time separately. Do not promise the latency observed in another private world. A mock phone animation demonstrates only the engine's visual response.
