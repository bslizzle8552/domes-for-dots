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
| Unknown target or untrusted source | Rejected. |
| No valid activity | Show the labeled simulated routine. |

Activity state is temporary and separate from persistent world content. World switching clears that world's test activity display. A time-preview control only offsets simulation; mock expiry continues to use real time. Deduplication and tombstones currently last for the runtime session; reloading resets them. Timestamp-based expiry still bounds replay lifetime, but a future real adapter needs durable sequencing/deduplication and authenticated resynchronization across sessions.

## Adapter boundary

The GDScript store exposes `configure(world_id, character_id)`, `apply(event, now, trusted_source)` and `active(now)`. The `trusted_source` parameter is caller authority, not a value copied from untrusted event data. A real adapter needs an authenticated transport, allowed target mapping, clock policy, monotonic sequencing, health status and test evidence. Do not allow a browser import or `source: "real"` to establish identity.

Connection health and current activity are different. A connection may be healthy while no activity is reported. A stale lease means unknown current activity, not evidence of continuing work. Minimize payloads: IDs, bounded time and kind are enough; transcripts, call audio, prompts and work titles are unnecessary here.

## Native call visualization

The intended path is an existing native ChatGPT call, an optional verified report, then movement to a suitable station and a visual pose. The world never answers the call. No second agent, telephony service or audio integration is part of this engine.

If a real reporting route becomes available, record native answer time, receipt time, station arrival and visual pose time separately. Do not promise the latency observed in another private world. A mock phone animation demonstrates only the engine's visual response.
