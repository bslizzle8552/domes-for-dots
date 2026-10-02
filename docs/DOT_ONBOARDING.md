# Owner and Dot onboarding

The owner sets the boundaries; the Dot should make meaningful creative choices. Begin with a short exchange and a small build, not a survey asking the owner to design every object.

Copy [CREATE_MY_WORLD.md](../prompts/CREATE_MY_WORLD.md) directly to the Dot. When building on your Dot's virtual machine, use its installed Godot and Blender and check versions/templates. For a hosted or already-served prebuilt world, the owner's computer only needs a browser. A Dot can work with a build agent when its tools cannot edit or execute the project. Capability reports should distinguish confirmed, unavailable and untested tools.

## Decision ownership

| Section | Meaning | How it changes |
| --- | --- | --- |
| OWNER LOCKED / `owner_locked` | Must-haves, dislikes, privacy constraints and decisions the owner reserves. | Only an explicit owner amendment can change a lock. Preserve the previous value and reason in history. |
| DOT CHOICE / `dot_choice` | Creative choices delegated to the Dot: setting, layout, hobbies, appearance, color or other choices within the locks. | The Dot may evolve these within the agreed scope, recording meaningful changes. |
| SHARED DECISION / `shared_decision` | Choices that require collaboration, or proposals whose scope is not yet settled. | Record their status; an unresolved proposal is not permission. |

Missing preferences are not a reason to ask about every detail. Ask at most three focused questions when answers materially affect the first build. Otherwise choose a reversible starting point and mark assumptions. Do not infer permissions to spend, publish, connect accounts or create recurring tasks from a visual preference. Existing explicit authorization remains valid; do not ask for it again.

## Structured brief

Save a JSON brief under `godot/content/briefs/` and reference it with the world's `brief_path`. It has its own schema and is authored content, separate from the runtime save. A minimal shape is:

```json
{
  "schema_version": 1,
  "world_id": "my_world",
  "dot_name": "Your Dot",
  "concept": "A place the Dot chose within the owner's boundaries",
  "owner_locked": {
    "privacy": "Local preview first; no personal conversations in content",
    "avoid": ["Owner-specified dislikes"],
    "reserved_decisions": ["Owner-specified decisions"]
  },
  "dot_choice": {
    "setting": "Dot chooses",
    "hobby": "Dot chooses",
    "appearance": "Dot chooses if delegated"
  },
  "shared_decision": {
    "initial_scope": "One small navigable home and one finite project",
    "unresolved": []
  },
  "capabilities": {
    "godot": "untested",
    "web_export": "untested",
    "blender": "optional; untested",
    "real_activity": "unavailable"
  },
  "initial_scope": ["One home", "One character", "One simulated project"],
  "expansion_history": []
}
```

Use the actual brief schema for accepted value shapes. Replace examples with the owner's statements and the Dot's concrete choices. Capability entries should include tool/version/test evidence when available, not just enthusiasm for a tool.

## First build

Confirm the Dot name, owner boundaries, realism/fantasy preference, appearance delegation, privacy expectations and available tools only as needed. The Dot should choose at least two meaningful elements of its home. A new setting and hobby matter more than a new paint color.

Build one small environment with reachable stations suited to that Dot, a compatible character and one finite imagined project. Rest/work/call visual tags can use any suitable prop; a conventional desk phone is not mandatory. Prove browser loading early, then movement, activity expiry and save/reload.

Deliver a usable preview, brief, changed files and a short PASS/FAIL/UNAVAILABLE/NOT TESTED record. Leave native event reporting unavailable unless a real authenticated path was tested for that owner.

## Expansion without losing the brief

Use [EXPAND_MY_WORLD.md](../prompts/EXPAND_MY_WORLD.md). Read the current brief and state before proposing changes. Keep IDs and the simulation epoch stable for compatible content-only additions. A changed routine or project meaning needs an explicit state transition; it must not silently reinterpret existing progress.

Each expansion history entry has an `id`, `description` and `owner_locked_preserved: true` in version 1. Put the date, reason, changes, any explicit lock amendment, affected identities, validation and recovery point into its description. Preservation refers to the owner's current explicit agreement; it does not prevent the owner from deliberately amending a lock. Store no transcript or secret to justify a choice. The brief survives every export and rebuild as source content.

Simulation advances an authored project. New designs, rooms and assets require actual model/tool work. No onboarding prompt creates endless background creativity or schedules recurring expansion.
